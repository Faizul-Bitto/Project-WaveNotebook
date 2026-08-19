"""
Discount calculation service.

This module implements the core discount calculation logic for the e-commerce
system. It follows the "Best Discount Wins" principle:

  - For a given product or product-group, if multiple *price-related* discount
    rules are applicable, only the one yielding the highest discount amount
    (in BDT) is applied. Discounts are **never** stacked/compounded.

  - BOGO (Buy X Get Y) rules are evaluated independently and are **not**
    part of the "Best Discount Wins" comparison. They apply on top of the
    winning price discount.

  - Free shipping is a UI-only flag (no shipping cost exists in this app).
    It is attached to the winning rule or evaluated standalone.

The service is designed to be reused across:
  - Cart GET (discount preview)
  - Order creation (apply discount)
  - Checkout / order confirmation (discount breakdown)
"""

import json
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.discount import Discount
from app.models.discount_scope import DiscountScope
from app.models.bundle_rule import BundleRule
from app.models.bundle_slab import BundleSlab
from app.models.bogo_rule import BogoRule
from app.models.discount_usage import DiscountUsage
from app.models.product import Product
from app.models.category import Category
from app.models.spend_based_rule import SpendBasedRule
from app.models.spend_based_slab import SpendBasedSlab

from app.utils.variant_generator import resolve_attrs_display

# ============================================================
# Helpers
# ============================================================


def get_bogo_bonus_quantity(
    db: Session, product_id: int, quantity: int, unit_price: float = 0.0, selected_attributes: str = None
) -> int:
    """Return the number of free units that are *accepted* (full-free or
    partial after consent) for a given quantity.

    Partial (<100%) BOGO only auto-applies its bonus once the cart quantity
    reaches `buy_quantity + get_quantity`. At exactly `buy_quantity` the
    bonus is *not* auto-added (the front-end must prompt for opt-in).

    IMPORTANT: unit_price defaults to 1.0 (not 0.0) so that the bonus is
    always detected even when called from stock-checking paths where the
    caller does not have the unit price available. The savings comparison
    is only used to pick the best BOGO rule — it does not affect whether
    bonus units are counted.
    """
    if quantity <= 0:
        return 0
    # Use a non-zero unit_price so `bonus_savings > best_savings` always
    # evaluates correctly and bonus units are counted even when the caller
    # doesn't pass a real price (e.g. stock validation in cart/order).
    bonus, _, _ = _calc_bogo_bonus(db, product_id, quantity, unit_price or 1.0, selected_attributes)
    return bonus


def is_discount_valid(discount: Discount) -> bool:
    """Return True if the discount is active and within its date window."""
    if not discount or discount.status != "active":
        return False
    now = datetime.now()
    if now < discount.start_date:
        return False
    if discount.end_date and now > discount.end_date:
        return False
    return True


def _get_active_discounts(db: Session) -> list[Discount]:
    """Fetch all discounts that are currently valid (active + within date range)."""
    now = datetime.now()
    discounts = (
        db.query(Discount)
        .filter(
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )
    return discounts


def _get_product_category(db: Session, product_id: int) -> int | None:
    """Return the category_id for a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    return product.category_id if product else None


def _get_applicable_scoped_discounts(
    db: Session, product_id: int, category_id: int
) -> list[tuple[Discount, DiscountScope]]:
    """
    Return (discount, scope) pairs for percentage / flat / free_shipping
    discounts that apply to the given product or its category.
    """
    now = datetime.now()
    results = (
        db.query(Discount, DiscountScope)
        .join(DiscountScope, Discount.id == DiscountScope.discount_id)
        .filter(
            Discount.type.in_(["percentage", "flat", "free_shipping"]),
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .filter(
            or_(
                (DiscountScope.scope_type == "product")
                & (DiscountScope.scope_id == product_id),
                (DiscountScope.scope_type == "category")
                & (DiscountScope.scope_id == category_id),
            )
        )
        .all()
    )
    return results


def _calc_scoped_discount_amount(
    discount: Discount, original_subtotal: float, quantity: int
) -> float:
    """Calculate the discount amount for a single scoped (product/category) discount."""
    if discount.value_type == "percentage":
        amount = original_subtotal * (float(discount.value) / 100.0)
        cap = float(discount.max_discount_cap) if discount.max_discount_cap is not None else None
        if cap is not None and cap > 0:
            amount = min(amount, cap)
        return amount
    elif discount.value_type == "flat":
        return float(discount.value) * quantity
    return 0.0


def _get_bundle_discount(db: Session, bundle_rule: BundleRule) -> Discount:
    """Fetch the parent Discount for a bundle rule."""
    return db.query(Discount).filter(Discount.id == bundle_rule.discount_id).first()


def _calc_quantity_bundle_amount(
    db: Session, bundle_rule: BundleRule, item_quantity: int, original_subtotal: float
) -> float:
    """Calculate discount from a quantity-based bundle for a single product line.
    Applies max_discount_cap if the parent discount has one."""
    slabs = (
        db.query(BundleSlab)
        .filter(BundleSlab.bundle_rule_id == bundle_rule.id)
        .order_by(BundleSlab.min_quantity.desc())
        .all()
    )
    discount = _get_bundle_discount(db, bundle_rule)
    for slab in slabs:
        if item_quantity >= slab.min_quantity:
            if slab.value_type == "percentage":
                amount = original_subtotal * (float(slab.value) / 100.0)
                cap = float(discount.max_discount_cap) if discount and discount.max_discount_cap is not None else None
                if cap is not None and cap > 0:
                    amount = min(amount, cap)
                return amount
            else:
                return float(slab.value) * item_quantity
    return 0.0


def _calc_bogo_bonus(
    db: Session, product_id: int, quantity: int, unit_price: float, selected_attributes: str = None
) -> tuple[int, dict | None, dict | None]:
    """
    Calculate BOGO bonus units for a single product.

    BOGO is NOT a "discount amount" subtracted from the bill. It physically
    adds free/discounted extra units to the customer's cart/order. This returns
    the number of bonus units (get_quantity per completed buy group), the
    rule info, and any *pending* (opt-in) offer so the caller can:
      - add the bonus units to the item's total quantity (affects stock & display)
      - charge only the get_discount_percent remaining price for those units
      - show a consent prompt when the customer has qualified for a PARTIAL BOGO
        but has NOT yet accepted the extra units.

    Consent / Opt-in rule:
      - If get_discount_percent == 100  → bonus is applied automatically
        (no consent needed; the item is free, no extra cost to the customer).
      - If get_discount_percent <  100  → this is a PARTIAL (opt-in) BOGO.
        * When quantity == buy_quantity, we do NOT auto-add the discounted
          extra unit. Instead we return a `pending_offer` dict so the
          front-end can prompt the customer for explicit consent
          (e.g. "Add 1 more at 50% off?").
        * When quantity >= buy_quantity + get_quantity, the discounted
          unit(s) are treated as accepted and calculated normally.

    selected_attributes matching:
      - If a BOGO rule has selected_attributes=NULL, it applies to ALL variants.
      - If a BOGO rule has selected_attributes set, it only applies to the
        matching variant.

    Returns (bonus_quantity, rule_info, pending_offer).
    """
    now = datetime.now()
    bogo_rules = (
        db.query(BogoRule)
        .join(Discount, BogoRule.discount_id == Discount.id)
        .filter(
            BogoRule.product_id == product_id,
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    best_bonus = 0
    best_info = None
    best_pending = None
    best_savings = 0.0

    for rule in bogo_rules:
        discount = db.query(Discount).filter(Discount.id == rule.discount_id).first()
        if not is_discount_valid(discount):
            continue

        # Variant-specific matching: NULL means all variants, otherwise match exactly
        if rule.selected_attributes is not None:
            if rule.selected_attributes != selected_attributes:
                continue

        pct = float(rule.get_discount_percent)
        is_full_free = pct >= 100.0

        if is_full_free:
            # For 100% free BOGO: every buy_quantity items earns get_quantity free items
            buy_groups = quantity // rule.buy_quantity
        else:
            # For partial BOGO: group is buy+get items; get items are discounted (not added)
            group_size = rule.buy_quantity + rule.get_quantity
            buy_groups = quantity // group_size

        # ---- Partial (<100%) BOGO: show pending offer if customer can still complete a group ----
        if not is_full_free and buy_groups <= 0 and quantity >= rule.buy_quantity:
            extra_units = rule.get_quantity
            unit_disc_price = unit_price * ((100.0 - pct) / 100.0)
            pending = {
                "rule_id": rule.id,
                "discount_id": rule.discount_id,
                "buy_quantity": rule.buy_quantity,
                "get_quantity": rule.get_quantity,
                "get_discount_percent": pct,
                "extra_unit_price": round(unit_disc_price, 2),
                "extra_units": extra_units,
                "extra_total": round(extra_units * unit_disc_price, 2),
                "type": "bogo",
                "pending": True,
            }
            # Only keep the most valuable pending offer
            candidate_savings = extra_units * unit_disc_price
            if best_pending is None or candidate_savings > best_savings:
                best_pending = pending
                best_savings = candidate_savings
            continue  # Don't add to bill until user consents

        if buy_groups <= 0:
            continue
        bonus = buy_groups * rule.get_quantity
        # For partial BOGO: if quantity >= buy + get, the customer has completed
        # a full group. The get items are discounted within the purchased quantity
        # (not added as extra). For 100% free, bonus items are additional.
        # quantity >= buy + get → user has added enough units; treat as accepted

        # Full 100% OR partial already accepted
        bonus_savings = bonus * unit_price * (pct / 100.0)

        if bonus_savings > best_savings:
            best_savings = bonus_savings
            best_bonus = bonus
            best_info = {
                "rule_id": rule.id,
                "discount_id": rule.discount_id,
                "discount_name": discount.name if discount else None,
                "buy_quantity": rule.buy_quantity,
                "get_quantity": rule.get_quantity,
                "get_discount_percent": pct,
                "type": "bogo",
            }

    return best_bonus, best_info, best_pending


def _check_combo_bundles(
    db: Session, cart_items: list[dict], products: dict
) -> list[dict]:
    """
    Check all applicable combo bundle rules and return a list of
    {discount, rule, bundle_rule, amount, items_covered} for each
    applicable combo.
    """
    now = datetime.now()
    bundle_rules = (
        db.query(BundleRule)
        .join(Discount, BundleRule.discount_id == Discount.id)
        .filter(
            BundleRule.bundle_type == "combo",
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    applicable_combos = []
    cart_product_ids = set(item["product_id"] for item in cart_items)

    for rule in bundle_rules:
        discount = db.query(Discount).filter(Discount.id == rule.discount_id).first()
        if not is_discount_valid(discount):
            continue

        required = []
        if rule.required_products:
            try:
                required = json.loads(rule.required_products)
            except (json.JSONDecodeError, TypeError):
                required = []

        if not required or not all(pid in cart_product_ids for pid in required):
            continue

        combo_items = [item for item in cart_items if item["product_id"] in required]
        combo_subtotal = sum(
            float(item["unit_price"]) * item["quantity"] for item in combo_items
        )

        slabs = db.query(BundleSlab).filter(BundleSlab.bundle_rule_id == rule.id).all()

        if not slabs:
            continue

        slab = slabs[0]
        if slab.value_type == "percentage":
            amount = combo_subtotal * (float(slab.value) / 100.0)
        else:
            amount = float(slab.value)

        applicable_combos.append(
            {
                "discount": discount,
                "bundle_rule": rule,
                "amount": amount,
                "items_covered": [item["product_id"] for item in combo_items],
                "subtotal_covered": combo_subtotal,
            }
        )

    return applicable_combos


def _check_quantity_bundles(
    db: Session, cart_items: list[dict], products: dict
) -> list[dict]:
    """
    Check all applicable quantity-based bundle rules for each product.
    Returns list of {discount, bundle_rule, product_id, amount, item_index}.
    """
    now = datetime.now()
    bundle_rules = (
        db.query(BundleRule)
        .join(Discount, BundleRule.discount_id == Discount.id)
        .filter(
            BundleRule.bundle_type == "quantity",
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    applicable = []
    for idx, item in enumerate(cart_items):
        product_id = item["product_id"]
        quantity = item["quantity"]
        original_subtotal = float(item["unit_price"]) * quantity

        # Get quantity bundle rules that reference this product via scope
        # Quantity bundles use discount_scopes to target a product
        scoped = (
            db.query(Discount, BundleRule)
            .join(DiscountScope, Discount.id == DiscountScope.discount_id)
            .join(BundleRule, Discount.id == BundleRule.discount_id)
            .filter(
                BundleRule.bundle_type == "quantity",
                Discount.id == BundleRule.discount_id,
                DiscountScope.scope_type == "product",
                DiscountScope.scope_id == product_id,
                Discount.status == "active",
            )
            .all()
        )

        for discount, br in scoped:
            if not is_discount_valid(discount):
                continue
            amount = _calc_quantity_bundle_amount(db, br, quantity, original_subtotal)
            if amount > 0:
                applicable.append(
                    {
                        "discount": discount,
                        "bundle_rule": br,
                        "product_id": product_id,
                        "item_index": idx,
                        "amount": amount,
                        "type": "quantity_bundle",
                    }
                )

        # Also check bundle rules without scope (applies to all products)
        # These are bundle rules that don't have a scope — meaning they apply
        # to any product in the cart
        unscoped_rules = (
            db.query(BundleRule)
            .join(Discount, BundleRule.discount_id == Discount.id)
            .outerjoin(DiscountScope, Discount.id == DiscountScope.discount_id)
            .filter(
                BundleRule.bundle_type == "quantity",
                Discount.id == BundleRule.discount_id,
                Discount.status == "active",
                Discount.start_date <= now,
                or_(Discount.end_date.is_(None), Discount.end_date > now),
            )
            .all()
        )

        for br in unscoped_rules:
            discount = db.query(Discount).filter(Discount.id == br.discount_id).first()
            if not is_discount_valid(discount):
                continue

            # Check if this rule already covered via scope
            if any(
                a["bundle_rule"].id == br.id
                for a in applicable
                if a.get("bundle_rule") and a["bundle_rule"].id == br.id
            ):
                continue

            amount = _calc_quantity_bundle_amount(db, br, quantity, original_subtotal)
            if amount > 0:
                applicable.append(
                    {
                        "discount": discount,
                        "bundle_rule": br,
                        "product_id": product_id,
                        "item_index": idx,
                        "amount": amount,
                        "type": "quantity_bundle",
                    }
                )

    return applicable


def _check_free_shipping(
    db: Session,
    cart_items: list[dict],
    products: dict,
    winning_bundle_rule_id: int | None,
    winning_discount_id: int | None = None,
) -> bool:
    """
    Determine whether free shipping should be shown.
    - Standalone free_shipping discount applies if any product/category in cart matches.
    - Discount-level free_shipping flag applies if that discount is the winner.
    - Bundle rule with free_shipping flag applies if that bundle is the winner.
    """
    now = datetime.now()
    product_ids = set(item["product_id"] for item in cart_items)
    category_ids = set()
    for pid in product_ids:
        cat_id = _get_product_category(db, pid)
        if cat_id:
            category_ids.add(cat_id)

    # Check standalone free shipping discounts
    # First: storewide free_shipping (no scope records = applies to entire cart)
    storewide_fs = (
        db.query(Discount)
        .filter(
            Discount.type == "free_shipping",
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .outerjoin(DiscountScope, Discount.id == DiscountScope.discount_id)
        .filter(DiscountScope.id.is_(None))
        .all()
    )
    if storewide_fs:
        return True

    # Second: scoped free_shipping (specific product/category)
    standalone = (
        db.query(Discount)
        .join(DiscountScope, Discount.id == DiscountScope.discount_id)
        .filter(
            Discount.type == "free_shipping",
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    for d in standalone:
        scopes = db.query(DiscountScope).filter(DiscountScope.discount_id == d.id).all()
        for scope in scopes:
            if scope.scope_type == "product" and scope.scope_id in product_ids:
                return True
            if scope.scope_type == "category" and scope.scope_id in category_ids:
                return True

    # Check winning discount's free_shipping flag
    if winning_discount_id:
        winning_discount = (
            db.query(Discount).filter(Discount.id == winning_discount_id).first()
        )
        if winning_discount and winning_discount.free_shipping:
            return True

    # Check winning bundle rule's free_shipping flag
    if winning_bundle_rule_id:
        br = (
            db.query(BundleRule).filter(BundleRule.id == winning_bundle_rule_id).first()
        )
        if br and br.free_shipping:
            return True

    return False


def _check_spend_based_discount(
    db: Session,
    cart_items: list[dict],
    items_breakdown: list[dict],
    products_map: dict[int, Product],
) -> dict | None:
    """
    Calculate spend-based discount for the cart.

    Rules:
    - Only applies to non-BOGO items
    - Scope can be 'storewide' or 'category'
    - Only the highest applicable slab is used
    - Returns None if no spend-based rule applies
    """
    now = datetime.now()

    # Get all active spend-based rules
    rules = (
        db.query(SpendBasedRule)
        .join(Discount, SpendBasedRule.discount_id == Discount.id)
        .filter(
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    if not rules:
        return None

    # Calculate spend amount from non-BOGO items, filtered by rule scope
    best_discount = None
    best_rule = None
    best_slab = None
    best_spend = 0.0

    for rule in rules:
        discount = db.query(Discount).filter(Discount.id == rule.discount_id).first()
        if not is_discount_valid(discount):
            continue

        # Calculate spend amount for this rule's scope
        spend = 0.0
        for item in cart_items:
            pid = item["product_id"]
            item_attrs = item.get("selected_attributes")
            breakdown = next(
                (
                    i
                    for i in items_breakdown
                    if i["product_id"] == pid and i.get("selected_attributes") == item_attrs
                ),
                None,
            )
            if not breakdown:
                continue

            # Skip BOGO items - they're handled separately
            if breakdown.get("bonus_quantity", 0) > 0 and breakdown.get("bogo_info"):
                continue

            # Check scope
            if rule.scope_type == "category":
                product = products_map.get(pid)
                if not product or product.category_id != rule.scope_id:
                    continue
            elif rule.scope_type == "product":
                if pid != rule.scope_id:
                    continue
            # For 'storewide', no additional filtering

            # Use original subtotal (before any discount) for spend calculation
            spend += breakdown.get("original_subtotal", 0.0)

        if spend <= 0:
            continue

        # Find the highest applicable slab
        slabs = (
            db.query(SpendBasedSlab)
            .filter(SpendBasedSlab.spend_based_rule_id == rule.id)
            .order_by(SpendBasedSlab.min_spend_amount.desc())
            .all()
        )

        applicable_slab = None
        for slab in slabs:
            if spend >= float(slab.min_spend_amount):
                applicable_slab = slab
                break

        if not applicable_slab:
            continue

        # Calculate discount amount
        if applicable_slab.value_type == "percentage":
            discount_amount = spend * (float(applicable_slab.value) / 100.0)
        else:
            discount_amount = float(applicable_slab.value)

        # Track the best spend-based discount
        if best_discount is None or discount_amount > best_discount:
            best_discount = discount_amount
            best_rule = rule
            best_slab = applicable_slab
            best_spend = spend

    if best_discount is None:
        return None

    return {
        "discount_amount": round(best_discount, 2),
        "spend_amount": round(best_spend, 2),
        "rule_id": best_rule.id,
        "discount_id": best_rule.discount_id,
        "discount_name": discount.name if discount else None,
        "scope_type": best_rule.scope_type,
        "scope_id": best_rule.scope_id,
        "slab_min_spend": float(best_slab.min_spend_amount),
        "slab_value_type": best_slab.value_type,
        "slab_value": float(best_slab.value),
    }


# ============================================================
# Public API
# ============================================================


def calculate_cart_discounts(db: Session, cart_items: list[dict]) -> dict:
    """
    Calculate the best discount for an entire cart.

    Parameters
    ----------
    db : SQLAlchemy Session
    cart_items : list of dicts, each containing:
        - product_id  (int)
        - quantity    (int)
        - selected_attributes (str | None  – JSON string)
        - unit_price  (float | str  – original variant price)

    Returns
    -------
    dict with keys:
        - subtotal_before_discount : float
        - total_discount          : float
        - total_after_discount    : float
        - items                   : list[dict]  – per-item breakdown
        - discount_breakdown      : list[dict]  – winning rules
        - free_shipping           : bool
        - winning_rule            : dict | None
    """
    if not cart_items:
        return {
            "subtotal_before_discount": 0.0,
            "total_discount": 0.0,
            "total_after_discount": 0.0,
            "items": [],
            "discount_breakdown": [],
            "free_shipping": False,
            "winning_rule": None,
        }

    # Normalize cart items
    normalized = []
    for item in cart_items:
        up = float(item.get("unit_price", 0))
        qty = int(item.get("quantity", 0))
        normalized.append(
            {
                "product_id": int(item["product_id"]),
                "quantity": qty,
                "selected_attributes": item.get("selected_attributes"),
                "unit_price": up,
                "subtotal": up * qty,
            }
        )

    # Build product + category lookup
    product_ids = list(set(item["product_id"] for item in normalized))
    products_map: dict[int, Product] = {}
    category_ids: dict[int, int] = {}
    for pid in product_ids:
        prod = db.query(Product).filter(Product.id == pid).first()
        if prod:
            products_map[pid] = prod
            category_ids[pid] = prod.category_id

    subtotal_before = sum(item["subtotal"] for item in normalized)

    # ----------------------------------------------------------
    # 1. Per-product Best Discount Wins (price-related)
    # ----------------------------------------------------------
    per_product_best: dict[int, dict] = {}  # product_id -> best discount info

    for item in normalized:
        pid = item["product_id"]
        cat_id = category_ids.get(pid)
        original_subtotal = item["subtotal"]
        qty = item["quantity"]

        candidate_discounts: list[dict] = []

        # a) Scoped percentage / flat discounts
        scoped = _get_applicable_scoped_discounts(db, pid, cat_id)
        for discount, scope in scoped:
            amount = _calc_scoped_discount_amount(discount, original_subtotal, qty)
            candidate_discounts.append(
                {
                    "discount": discount,
                    "amount": amount,
                    "type": discount.type,
                    "value_type": discount.value_type,
                    "value": float(discount.value or 0),
                    "is_scoped": True,
                    "scope_type": scope.scope_type,
                    "scope_id": scope.scope_id,
                    "is_bundle": False,
                    "is_bogo": False,
                }
            )

        # b) Quantity-based bundle rules for this product
        now = datetime.now()
        qty_bundle_rules = (
            db.query(BundleRule)
            .join(Discount, BundleRule.discount_id == Discount.id)
            .join(DiscountScope, Discount.id == DiscountScope.discount_id)
            .filter(
                BundleRule.bundle_type == "quantity",
                DiscountScope.scope_type == "product",
                DiscountScope.scope_id == pid,
                Discount.status == "active",
                Discount.start_date <= now,
                or_(Discount.end_date.is_(None), Discount.end_date > now),
            )
            .all()
        )

        for br in qty_bundle_rules:
            discount = db.query(Discount).filter(Discount.id == br.discount_id).first()
            if not is_discount_valid(discount):
                continue
            amount = _calc_quantity_bundle_amount(db, br, qty, original_subtotal)
            if amount > 0:
                candidate_discounts.append(
                    {
                        "discount": discount,
                        "bundle_rule": br,
                        "amount": amount,
                        "type": "bundle",
                        "is_bundle": True,
                        "is_quantity_bundle": True,
                        "bundle_type": "quantity",
                        "min_quantity": _get_matching_slab_min(db, br, qty),
                    }
                )

        # Pick the best (highest amount) per product
        if candidate_discounts:
            best = max(candidate_discounts, key=lambda x: x["amount"])
            per_product_best[pid] = best
        else:
            per_product_best[pid] = None

    # ----------------------------------------------------------
    # 2. Combo bundles (product-group level)
    #    Compare combo discount vs sum of per-product best discounts
    # ----------------------------------------------------------
    combo_combos = _check_combo_bundles(db, normalized, products_map)
    combo_overrides: dict[int, dict] = {}  # product_id -> combo info

    for combo in combo_combos:
        combo_amount = combo["amount"]
        covered_ids = combo["items_covered"]

        # Sum of per-product best discounted amounts
        sum_best = sum(
            per_product_best.get(pid, {}).get("amount", 0) or 0 for pid in covered_ids
        )

        if combo_amount > sum_best:
            for pid in covered_ids:
                combo_overrides[pid] = {
                    "discount": combo["discount"],
                    "bundle_rule": combo["bundle_rule"],
                    "amount": combo_amount / len(covered_ids),  # prorated
                    "type": "combo_bundle",
                    "is_bundle": True,
                    "is_combo_bundle": True,
                    "free_shipping": combo["bundle_rule"].free_shipping,
                }

    # ----------------------------------------------------------
    # 3. Determine winning discount per item
    # ----------------------------------------------------------
    total_price_discount = 0.0
    items_breakdown = []
    discount_breakdown = []
    winning_rule_info = None

    for item in normalized:
        pid = item["product_id"]
        original_subtotal = item["subtotal"]
        qty = item["quantity"]
        up = item["unit_price"]

        # --- BOGO check FIRST (Rule 1: Absolute Priority) ---
        # If a BOGO rule applies to this product, NO other discount may apply.
        bogo_bonus = 0
        bogo_info = None
        bogo_pending = None
        bonus_price = 0.0
        bogo_savings_for_item = 0.0
        if qty > 0:
            bogo_bonus, bogo_info, bogo_pending = _calc_bogo_bonus(db, pid, qty, up)
            if bogo_bonus > 0 and bogo_info:
                pct = float(bogo_info["get_discount_percent"])
                bonus_price = bogo_bonus * up * ((100.0 - pct) / 100.0)
                bogo_savings_for_item = bogo_bonus * up * (pct / 100.0)

        # Rule 1: If BOGO applies, skip ALL other discount candidates
        bogo_applied = bogo_bonus > 0 and bogo_info is not None
        discount_amount = 0.0
        applied_rule = None

        if not bogo_applied:
            if pid in combo_overrides:
                winner = combo_overrides[pid]
            else:
                winner = per_product_best.get(pid)

            if winner:
                discount_amount = min(winner["amount"], original_subtotal)
                applied_rule = {
                    "discount_id": winner["discount"].id,
                    "discount_name": winner["discount"].name,
                    "type": winner.get("type", winner["discount"].type),
                    "amount": discount_amount,
                }
                if winner.get("is_bundle"):
                    applied_rule["bundle_rule_id"] = winner["bundle_rule"].id
                    applied_rule["bundle_type"] = winner.get("bundle_type", "quantity")
                total_price_discount += discount_amount
            else:
                applied_rule = None

        # subtotal_before must include ALL units (paid + bonus) at regular price,
        # then BOGO savings are subtracted once via bogo_savings_for_item.
        # For 100% free BOGO: bonus items are additional free items (added to total).
        # For partial BOGO: get items are discounted within the purchased quantity
        # (no extra items added).
        is_bogo_full_free = (
            bogo_info is not None
            and float(bogo_info.get("get_discount_percent", 0)) >= 100.0
        )
        if is_bogo_full_free:
            line_amount = original_subtotal + bogo_bonus * up
            total_qty = qty + bogo_bonus
        else:
            line_amount = original_subtotal
            total_qty = qty
        # For BOGO items: subtract BOGO savings (price already adjusted by group_size logic).
        # For non-BOGO items: show full price in the item subtotal; the discount
        # appears only in the Order Summary (via discount_breakdown).
        if bogo_applied:
            discounted_subtotal = line_amount - discount_amount - bogo_savings_for_item
        else:
            discounted_subtotal = original_subtotal

        items_breakdown.append(
            {
                "product_id": pid,
                "product_name": (
                    products_map.get(pid).name if products_map.get(pid) else "Unknown"
                ),
                "requested_quantity": qty,
                "quantity": qty,
                "bonus_quantity": bogo_bonus,
                "total_quantity": total_qty,
                "unit_price": up,
                "original_subtotal": original_subtotal,
                "bonus_price": round(bonus_price, 2),
                "discount_amount": discount_amount,
                "discounted_subtotal": round(discounted_subtotal, 2),
                "winning_rule": applied_rule,
                "bogo_info": bogo_info,
                "bogo_pending": bogo_pending,
                "selected_attributes": item.get("selected_attributes"),
            }
        )

    # ----------------------------------------------------------
    # 4. BOGO bonuses (free/discounted extra units, NOT a discount line)
    # ----------------------------------------------------------
    bogo_details = []
    bogo_savings_total = 0.0
    bogo_100_savings = 0.0  # savings from 100% free BOGO items only
    has_any_full_free_bogo = False

    for it in items_breakdown:
        if it["bonus_quantity"] > 0 and it.get("bogo_info"):
            info = it["bogo_info"]
            pct = float(info["get_discount_percent"])
            savings = it["bonus_quantity"] * it["unit_price"] * (pct / 100.0)
            bogo_savings_total += savings
            if pct >= 100.0:
                has_any_full_free_bogo = True
                bogo_100_savings += savings
            bogo_details.append(
                {
                    "product_id": it["product_id"],
                    "product_name": it.get("product_name"),
                    "selected_attributes": it.get("selected_attributes"),
                    "requested_quantity": it["requested_quantity"],
                    "bonus_quantity": it["bonus_quantity"],
                    "total_quantity": it["total_quantity"],
                    "get_discount_percent": info["get_discount_percent"],
                    "buy_quantity": info["buy_quantity"],
                    "get_quantity": info["get_quantity"],
                    "rule_id": info["rule_id"],
                    "discount_id": info["discount_id"],
                    "discount_name": info.get("discount_name"),
                    "unit_price": it["unit_price"],
                }
            )

    # Pending opt-in BOGO offers (partial <100% BOGO not yet accepted).
    # The front-end should display a consent prompt for these.
    pending_bogo_offers = []
    for it in items_breakdown:
        if it.get("bogo_pending"):
            offer = it["bogo_pending"]
            pending_bogo_offers.append(
                {
                    "product_id": it["product_id"],
                    "product_name": it["product_name"],
                    "buy_quantity": offer["buy_quantity"],
                    "get_quantity": offer["get_quantity"],
                    "get_discount_percent": offer["get_discount_percent"],
                    "extra_unit_price": offer["extra_unit_price"],
                    "extra_units": offer["extra_units"],
                    "extra_total": offer["extra_total"],
                    "rule_id": offer["rule_id"],
                    "discount_id": offer["discount_id"],
                    "type": "bogo",
                }
            )

    # ----------------------------------------------------------
    # 4.5 Calculate non-BOGO subtotal and spend-based discount
    # ----------------------------------------------------------
    non_bogo_subtotal = 0.0
    non_bogo_item_discount = 0.0
    for it in items_breakdown:
        has_bogo = it.get("bonus_quantity", 0) > 0 and it.get("bogo_info")
        if not has_bogo:
            non_bogo_subtotal += it.get("original_subtotal", 0.0)
            non_bogo_item_discount += it.get("discount_amount", 0.0)

    spend_based_result = _check_spend_based_discount(
        db, normalized, items_breakdown, products_map
    )
    spend_based_discount = 0.0
    if spend_based_result:
        spend_based_discount = spend_based_result["discount_amount"]

    # ----------------------------------------------------------
    # 5. Free shipping check
    # ----------------------------------------------------------
    winning_bundle_rule_id = None
    winning_discount_id = None
    for item_bd in items_breakdown:
        wr = item_bd.get("winning_rule")
        if wr:
            if wr.get("bundle_rule_id"):
                winning_bundle_rule_id = wr["bundle_rule_id"]
            if wr.get("discount_id") and not winning_discount_id:
                winning_discount_id = wr["discount_id"]
        elif item_bd.get("bogo_info") and not winning_discount_id:
            winning_discount_id = item_bd["bogo_info"]["discount_id"]
        if winning_bundle_rule_id and winning_discount_id:
            break

    # If spend-based discount is the winner, include its discount_id for free shipping check
    if spend_based_result and spend_based_discount > non_bogo_item_discount:
        winning_discount_id = spend_based_result["discount_id"]

    free_shipping = _check_free_shipping(
        db, normalized, products_map, winning_bundle_rule_id, winning_discount_id
    )

    # Also check if any combo that won has free_shipping
    if not free_shipping:
        for combo in combo_combos:
            covered = combo["items_covered"]
            if all(
                pid in [i["product_id"] for i in items_breakdown] for pid in covered
            ):
                if combo["bundle_rule"].free_shipping:
                    free_shipping = True
                    break

    # ----------------------------------------------------------
    # Assemble result
    # ----------------------------------------------------------
    # subtotal_before includes ALL units (paid + bonus) at regular price.
    # BOGO/other discounts are subtracted once via total_discount below.
    # Only add bonus units for 100% free BOGO (those are truly extra items).
    # For partial BOGO, the discounted items are within the purchased quantity.
    subtotal_before = 0.0
    for it in items_breakdown:
        bonus = it.get("bonus_quantity", 0)
        info = it.get("bogo_info")
        is_full_free = (
            info is not None
            and float(info.get("get_discount_percent", 0)) >= 100.0
        )
        bonus_subtotal = bonus * it["unit_price"] if is_full_free else 0.0
        subtotal_before += it.get("original_subtotal", 0.0) + bonus_subtotal

    # Spend-based discounts are shown ONLY in the Order Summary (not distributed
    # per-item), so each item retains its full price and the discount is
    # visible as a single summary line.
    explicit_discount = max(non_bogo_item_discount, spend_based_discount)

    # Final payable amount: subtotal minus explicit discount minus BOGO savings.
    total_after = subtotal_before - explicit_discount - bogo_savings_total

    # Determine display mode for EACH item:
    # - 100% BOGO with no other discounts on that item: simple flat total.
    # - Partial BOGO or other discounts on that item: show full breakdown.
    for it in items_breakdown:
        has_full_free_bogo = (
            it.get("bonus_quantity", 0) > 0
            and it.get("bogo_info")
            and float(it["bogo_info"].get("get_discount_percent", 0) or 0) >= 100.0
        )
        has_other_discounts = (it.get("discount_amount", 0) > 0)
        it["simple_bogo"] = has_full_free_bogo and not has_other_discounts

    # Cart-level simple_bogo is only true when ALL items are simple BOGO
    # and there are no other discounts anywhere.
    simple_bogo = all(
        it.get("simple_bogo", False) for it in items_breakdown
    ) and not any(it.get("discount_amount", 0) > 0 for it in items_breakdown)

    # `total_discount` is the aggregate discount shown as "Total Discount" in summaries.
    # For 100% free BOGO: the free items are shown as a separate "FREE" line in the
    # discount breakdown, so their value is excluded from Total Discount to avoid
    # double-counting. For partial (<100%) BOGO: BOGO savings are included because
    # the discount is applied within the purchased quantity (no extra free items).
    if has_any_full_free_bogo:
        total_discount = explicit_discount + (bogo_savings_total - bogo_100_savings)
    else:
        total_discount = explicit_discount + bogo_savings_total

    # `display_subtotal` is what the cart/order summary shows as "Items" total.
    # For 100% free BOGO: free bonus items are excluded from the subtotal so the
    # customer sees what they actually pay for (e.g. "6 + 2 FREE @ ৳600").
    # For partial BOGO or other discounts: shows the subtotal BEFORE discounts
    # so the saved amount is visible as a separate line (e.g. Items ৳8,000,
    # BOGO Applied -৳1,000, Total ৳7,000).
    if has_any_full_free_bogo:
        display_subtotal = subtotal_before - bogo_100_savings
    else:
        display_subtotal = subtotal_before

    # Build discount breakdown showing only WINNING discounts
    discount_breakdown = []

    # Determine which discount wins: spend-based vs per-product
    spend_won = spend_based_discount > non_bogo_item_discount

    # Show per-product discounts ONLY if they won (spend-based didn't beat them).
    # Use the actual winning rules from items_breakdown (not a re-query) so that
    # bundle/quantity discounts — which may have beaten scoped discounts — are
    # shown correctly and the losing scoped discount is hidden.
    if not spend_won:
        seen_discounts: dict[int, dict] = {}
        for item_bd in items_breakdown:
            wr = item_bd.get("winning_rule")
            if not wr or not wr.get("discount_id"):
                continue
            did = wr["discount_id"]
            if did not in seen_discounts:
                entry: dict = {
                    "type": wr.get("type", "price_discount"),
                    "name": wr.get("discount_name", "Discount"),
                    "discount_id": did,
                    "amount": 0.0,
                    "is_bundle": wr.get("bundle_rule_id") is not None,
                }
                if wr.get("bundle_rule_id"):
                    entry["bundle_rule_id"] = wr["bundle_rule_id"]
                    entry["bundle_type"] = wr.get("bundle_type", "quantity")
                seen_discounts[did] = entry
            seen_discounts[did]["amount"] += item_bd.get("discount_amount", 0.0)

        for entry in seen_discounts.values():
            entry["amount"] = round(entry["amount"], 2)
            discount_breakdown.append(entry)

    # Show spend-based discount ONLY if it won
    if spend_won and spend_based_result:
        slab_min_spend = spend_based_result.get("slab_min_spend", 0)
        slab_value_type = spend_based_result.get("slab_value_type", "")
        slab_value = spend_based_result.get("slab_value", 0)
        discount_name = spend_based_result.get("discount_name", "Spend-based Discount")
        if slab_min_spend and slab_value:
            descriptive_name = f"{discount_name} - {slab_value}% off on orders over ৳{slab_min_spend}"
        else:
            descriptive_name = discount_name
        discount_breakdown.append(
            {
                "type": "spend_based",
                "name": descriptive_name,
                "amount": round(spend_based_discount, 2),
                "spend_amount": spend_based_result.get("spend_amount"),
                "slab_min_spend": spend_based_result.get("slab_min_spend"),
                "slab_value_type": spend_based_result.get("slab_value_type"),
                "slab_value": spend_based_result.get("slab_value"),
            }
        )

    # Show BOGO details (always shown if BOGO applies, since it's independent)
    if bogo_savings_total > 0:
        for bd in bogo_details:
            pct = float(bd.get("get_discount_percent", 0))
            product_name = bd.get("product_name", "Unknown")
            selected_attrs = bd.get("selected_attributes")
            variant_info = ""
            if selected_attrs:
                try:
                    attrs = json.loads(selected_attrs)
                    if attrs:
                        resolved = resolve_attrs_display(db, attrs)
                        if resolved:
                            variant_parts = [f"{k}: {v}" for k, v in resolved.items()]
                            variant_info = f" ({', '.join(variant_parts)})"
                        else:
                            variant_parts = [f"{v}" for v in attrs.values()]
                            variant_info = f" ({', '.join(variant_parts)})"
                except (json.JSONDecodeError, TypeError):
                    pass
            if pct >= 100.0:
                label = f"BOGO Applied: {bd['bonus_quantity']} item free - {product_name}{variant_info}"
            else:
                saved = bd["bonus_quantity"] * bd["unit_price"] * (pct / 100.0)
                label = f"BOGO Applied: {bd['bonus_quantity']} item at {int(pct)}% off - {product_name}{variant_info} (saved ৳{round(saved, 2):.2f})"
            discount_breakdown.append(
                {
                    "type": "bogo",
                    "name": label,
                    "amount": 0.0 if pct >= 100.0 else round(bd["bonus_quantity"] * bd["unit_price"] * (pct / 100.0), 2),
                    "product_id": bd["product_id"],
                    "product_name": bd.get("product_name"),
                    "bonus_quantity": bd["bonus_quantity"],
                    "get_discount_percent": pct,
                }
            )

    if simple_bogo:
        total_items = sum(it.get("total_quantity", it.get("quantity", 0)) for it in items_breakdown)
        bogo_free_note = None
        for bd in bogo_details:
            if bd.get("get_discount_percent", 0) >= 100.0:
                bogo_free_note = (
                    f"BOGO Applied: {bd['bonus_quantity']} item free — "
                    f"so you got total {total_items} items in ৳{round(total_after, 2):,.2f}"
                )
                break
    else:
        bogo_free_note = None

    return {
        "subtotal_before_discount": round(subtotal_before, 2),
        "display_subtotal": round(display_subtotal, 2),
        "total_discount": round(total_discount, 2),
        "total_after_discount": round(total_after, 2),
        "items": items_breakdown,
        "discount_breakdown": discount_breakdown,
        "free_shipping": free_shipping,
        "winning_rule": winning_rule_info if total_price_discount > 0 else None,
        "bogo_details": bogo_details,
        "bogo_total": round(bogo_savings_total, 2),
        "price_discount_total": round(total_price_discount, 2),
        "spend_based_discount": round(spend_based_discount, 2),
        "non_bogo_subtotal": round(non_bogo_subtotal, 2),
        "pending_bogo_offers": pending_bogo_offers,
        "simple_bogo": simple_bogo,
        "bogo_free_note": bogo_free_note,
    }


def compute_simple_bogo(snapshot: dict) -> tuple[bool, str | None]:
    """
    Backward-compatible helper for order APIs.

    For orders whose ``discount_snapshot`` predates the ``simple_bogo`` /
    ``bogo_free_note`` fields, derive the same display rule directly from
    the stored ``bogo_details`` + ``discount_breakdown``.

    Returns ``(is_simple_bogo, bogo_free_note)``.
    """
    bogo_details = snapshot.get("bogo_details", []) or []
    discount_breakdown = snapshot.get("discount_breakdown", []) or []

    has_full_free_bogo = any(
        float(bd.get("get_discount_percent", 0) or 0) >= 100.0 for bd in bogo_details
    )
    has_other_discounts = any(
        entry.get("type") not in ("bogo",) for entry in discount_breakdown
    )

    if has_full_free_bogo and not has_other_discounts:
        note = None
        for bd in bogo_details:
            if float(bd.get("get_discount_percent", 0) or 0) >= 100.0:
                note = (
                    f"BOGO Applied: {bd['bonus_quantity']} item free — "
                    f"so you got total {bd.get('total_quantity', bd['bonus_quantity'])} items"
                )
                break
        return True, note

    return False, None


def _get_matching_slab_min(
    db: Session, bundle_rule: BundleRule, quantity: int
) -> int | None:
    """Return the min_quantity of the slab that matched for a quantity-based bundle."""
    slabs = (
        db.query(BundleSlab)
        .filter(BundleSlab.bundle_rule_id == bundle_rule.id)
        .order_by(BundleSlab.min_quantity.desc())
        .all()
    )
    for slab in slabs:
        if quantity >= slab.min_quantity:
            return slab.min_quantity
    return None


def get_product_discount_info(
    db: Session, product_id: int, unit_price: float = None
) -> dict:
    """
    Get discount information for a single product (used on product listing / detail pages).
    Returns badge text, original price, discounted price, free shipping flag, etc.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {}

    now = datetime.now()

    result = {
        "product_id": product_id,
        "badge": None,
        "badge_type": None,  # "discount" | "free_shipping" | "bogo"
        "original_price": None,
        "discounted_price": None,
        "original_price_range": None,
        "discounted_price_range": None,
        "free_shipping": False,
        "bundle_slabs": None,
        "bogo": None,
        "combo_products": None,
    }

    # Get the unit price (from variant or price_range min)
    if unit_price is None:
        from app.models.product_variant import ProductVariant as PV

        variant = (
            db.query(PV)
            .filter(PV.product_id == product_id, PV.is_active == True)
            .first()
        )
        unit_price = float(variant.price) if variant and variant.price else 0.0

    result["original_price"] = unit_price

    # --- Price-related discounts (product / category scoped) ---
    scoped = _get_applicable_scoped_discounts(db, product_id, product.category_id)
    best_price_discount = 0.0
    best_discount_info = None

    for discount, scope in scoped:
        if discount.type == "free_shipping":
            result["free_shipping"] = True
            continue

        amount = _calc_scoped_discount_amount(discount, unit_price, 1)
        if amount > best_price_discount:
            best_price_discount = amount
            if discount.value_type == "percentage":
                result["badge"] = f"{int(float(discount.value))}% OFF"
                result["badge_type"] = "discount"
                result["discounted_price"] = round(unit_price - amount, 2)
            else:
                result["badge"] = f"৳{float(discount.value):.0f} OFF"
                result["badge_type"] = "discount"
                result["discounted_price"] = round(unit_price - amount, 2)
            best_discount_info = discount

    # Compute discounted price range from variant prices (for listings / ranges)
    if best_discount_info and product:
        from app.models.product_variant import ProductVariant as PV

        variant_objs = (
            db.query(PV).filter(PV.product_id == product_id, PV.is_active == True).all()
        )
        variant_prices = [
            float(v.price)
            for v in variant_objs
            if v.price is not None and float(v.price) > 0
        ]
        if variant_prices:
            pp_min = min(variant_prices)
            pp_max = max(variant_prices)
            amt_min = _calc_scoped_discount_amount(best_discount_info, pp_min, 1)
            amt_max = _calc_scoped_discount_amount(best_discount_info, pp_max, 1)
            result["original_price_range"] = {
                "min": round(pp_min, 2),
                "max": round(pp_max, 2),
            }
            result["discounted_price_range"] = {
                "min": round(pp_min - amt_min, 2),
                "max": round(pp_max - amt_max, 2),
            }

    # --- Quantity-based bundles ---
    qty_bundle_rules = (
        db.query(BundleRule)
        .join(Discount, BundleRule.discount_id == Discount.id)
        .join(DiscountScope, Discount.id == DiscountScope.discount_id)
        .filter(
            BundleRule.bundle_type == "quantity",
            DiscountScope.scope_type == "product",
            DiscountScope.scope_id == product_id,
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    slabs_info = []
    for br in qty_bundle_rules:
        discount = db.query(Discount).filter(Discount.id == br.discount_id).first()
        if not is_discount_valid(discount):
            continue
        slab_objs = (
            db.query(BundleSlab)
            .filter(BundleSlab.bundle_rule_id == br.id)
            .order_by(BundleSlab.min_quantity)
            .all()
        )
        slab_list = []
        for slab in slab_objs:
            slab_amount = _calc_quantity_bundle_amount(db, br, 1, unit_price)
            slab_list.append(
                {
                    "min_quantity": slab.min_quantity,
                    "value_type": slab.value_type,
                    "value": float(slab.value),
                }
            )
        if slab_list:
            slabs_info.append(
                {
                    "bundle_rule_id": br.id,
                    "discount_name": discount.name,
                    "free_shipping": br.free_shipping,
                    "slabs": slab_list,
                }
            )
            if not result["badge"]:
                result["bundle_slabs"] = slab_list
                result["badge"] = (
                    f"{slab_list[0]['min_quantity']}টি কিনলে {int(slab_list[0]['value'])}% ছাড়"
                    if slab_list[0]["value_type"] == "percentage"
                    else f"{slab_list[0]['min_quantity']}টি কিনলে ৳{int(slab_list[0]['value'])} ছাড়"
                )
                result["badge_type"] = "discount"

    if slabs_info:
        result["bundle_slabs_info"] = slabs_info

    # --- BOGO ---
    bogo_rules = (
        db.query(BogoRule)
        .join(Discount, BogoRule.discount_id == Discount.id)
        .filter(
            BogoRule.product_id == product_id,
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    if bogo_rules:
        rule = bogo_rules[0]
        discount = db.query(Discount).filter(Discount.id == rule.discount_id).first()
        result["badge"] = f"{rule.buy_quantity}+{rule.get_quantity} FREE"
        result["badge_type"] = "bogo"
        result["bogo"] = {
            "discount_name": discount.name if discount else None,
            "buy_quantity": rule.buy_quantity,
            "get_quantity": rule.get_quantity,
            "get_discount_percent": float(rule.get_discount_percent),
        }

    # --- Combo bundles (where this product is part of a combo) ---
    combo_rules = (
        db.query(BundleRule)
        .join(Discount, BundleRule.discount_id == Discount.id)
        .filter(
            BundleRule.bundle_type == "combo",
            Discount.status == "active",
            Discount.start_date <= now,
            or_(Discount.end_date.is_(None), Discount.end_date > now),
        )
        .all()
    )

    combo_products = []
    for br in combo_rules:
        if br.required_products:
            try:
                req = json.loads(br.required_products)
            except (json.JSONDecodeError, TypeError):
                req = []
            if product_id in req:
                for pid in req:
                    if pid != product_id:
                        prod = db.query(Product).filter(Product.id == pid).first()
                        if prod:
                            combo_products.append(
                                {"id": pid, "name": prod.name, "slug": prod.slug}
                            )

    if combo_products:
        result["combo_products"] = combo_products

    # --- Free shipping standalone (already checked above) ---
    if result["free_shipping"] and not result["badge"]:
        result["badge"] = "ফ্রি শিপিং"
        result["badge_type"] = "free_shipping"

    return result


def record_discount_usage(
    db: Session,
    discount_id: int | None,
    order_id: int,
    applied_amount: float,
    discount_breakdown: list | None = None,
) -> None:
    """
    Record discount usage entries.
    - If discount_breakdown is provided, records one entry per winning discount (in BDT).
    - Otherwise records a single entry for `discount_id`.
    """
    if not applied_amount or applied_amount <= 0:
        return

    if discount_breakdown:
        recorded_any = False
        for entry in discount_breakdown:
            amt = float(entry.get("amount", 0) or 0)
            did = entry.get("discount_id") or entry.get("rule_id")
            if not did:
                continue
            # Compute BOGO amount from bonus_quantity * unit_price * get_discount_percent
            if amt == 0 and entry.get("bonus_quantity"):
                amt = (
                    float(entry["bonus_quantity"])
                    * float(entry.get("unit_price", 0) or 0)
                    * (float(entry.get("get_discount_percent", 0) or 0) / 100.0)
                )
            if amt > 0 and did:
                usage = DiscountUsage(
                    discount_id=int(did),
                    order_id=order_id,
                    applied_amount=round(amt, 2),
                )
                db.add(usage)
                recorded_any = True
        if recorded_any:
            db.commit()
        return

    if discount_id and applied_amount > 0:
        usage = DiscountUsage(
            discount_id=discount_id,
            order_id=order_id,
            applied_amount=round(applied_amount, 2),
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
