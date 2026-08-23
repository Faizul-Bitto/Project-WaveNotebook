"""
Invoice PDF generation service (system generated).

Single-page A4 invoice (multi-page only if there are many items):
- Teal header band with company logo, name, contact info & website link
- One large faint centered logo watermark across the page middle (anti-copy)
- Billed-to customer block, items table, discount breakdown, totals
- Generation timestamp footer in Bangladesh time (GMT+6)

Text is WRAPPED, never truncated. Fonts:
- Primary: best Latin font available on the host.
- Fallback (bundled): Noto Sans Bengali for Bangla glyphs (SIL OFL).
"""

import io
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fpdf import FPDF

MARGIN = 14
PAGE_W = 210
PAGE_H = 297
CONTENT_RIGHT = PAGE_W - MARGIN

TEAL = (13, 148, 136)
TEAL_DARK = (13, 116, 108)
DARK = (15, 23, 42)
GRAY = (100, 116, 139)
LIGHT_GRAY = (148, 163, 184)

# Bundled Bengali font - glyph fallback for Bangla characters that the
# primary font may lack. Ships inside the repo (SIL OFL licensed).
BUNDLED_BENGALI = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "NotoSansBengali-Regular.ttf"


def _fetch_logo_bytes(logo_url):
    """Download the application logo image bytes, or None on failure."""
    if not logo_url:
        return None
    try:
        resp = httpx.get(logo_url, timeout=10, follow_redirects=True)
        head = resp.content[:4]
        is_png = head.startswith(b"\x89PNG")
        is_jpg = resp.content[:3] == b"\xff\xd8\xff"
        if resp.status_code == 200 and (is_png or is_jpg):
            return resp.content
    except Exception:
        pass
    return None


def _ensure_scheme(url):
    """Guarantee a clickable http(s) prefix for website links."""
    url = str(url or "").strip()
    if not url:
        return ""
    if not urlparse(url).scheme:
        url = "https://" + url
    return url


def _strip_scheme(url):
    """Display version of a URL without the https:// prefix."""
    return str(url or "").replace("https://", "").replace("http://", "")


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.currency = "৳ "

    def _t(self, text):
        return str(text) if text is not None else ""

def build_invoice_pdf(order, items, settings) -> bytes:
    """Build a clean invoice PDF for an order (wrapping text, no truncation)."""
    site_name = getattr(settings, "site_name", None) or "WaveNotebook"
    hotline = str(getattr(settings, "hotline_number", None)
                  or getattr(settings, "contact_phone", None) or "").strip()
    contact_email = str(getattr(settings, "contact_email", None) or "").strip()
    address = str(getattr(settings, "contact_address", None) or "").strip()
    website = _ensure_scheme(getattr(settings, "website_url", None))
    logo_url = getattr(settings, "logo_url", None)

    pdf = InvoicePDF()
    pdf.set_auto_page_break(False)

    # ---------- Fonts ----------
    # Primary: best Unicode Latin font available on this host.
    primary_loaded = False
    for path in [
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ]:
        if Path(path).exists():
            try:
                pdf.add_font("Main", "", path)
                pdf.add_font("Main", "B", path)
                primary_loaded = True
                break
            except Exception:
                continue

    # Bundled Bengali font: used directly when no host font exists, and as a
    # glyph fallback for Bangla characters otherwise.
    bangla_loaded = False
    if BUNDLED_BENGALI.exists():
        try:
            pdf.add_font("Bng", "", str(BUNDLED_BENGALI))
            bangla_loaded = True
        except Exception:
            pass

    if not primary_loaded and bangla_loaded:
        # Last resort: Bengali font handles everything it can.
        pdf.add_font("Main", "", str(BUNDLED_BENGALI))
        pdf.add_font("Main", "B", str(BUNDLED_BENGALI))
        primary_loaded = True

    if not primary_loaded:
        raise RuntimeError("No usable font found for invoice generation.")

    if bangla_loaded:
        try:
            pdf.set_fallback_fonts(["Bng"])
        except Exception:
            pass
        try:
            pdf.set_text_shaping(True)
        except Exception:
            pass

    def B(size, color=None):
        pdf.set_font("Main", "B", size)
        if color:
            pdf.set_text_color(*color)

    def R(size, color=None):
        pdf.set_font("Main", "", size)
        if color:
            pdf.set_text_color(*color)

    logo_bytes = _fetch_logo_bytes(logo_url)
    pdf.add_page()

    # ---------- Watermark: large faint centered logo ----------
    try:
        if logo_bytes:
            wm_w = 105
            with pdf.local_context(fill_opacity=0.05):
                pdf.image(
                    io.BytesIO(logo_bytes),
                    x=(PAGE_W - wm_w) / 2,
                    y=(PAGE_H - wm_w) / 2 + 8,
                    w=wm_w,
                )
    except Exception:
        pass

    # ---------- Header band (teal, full width) ----------
    BAND_H = 36
    pdf.set_fill_color(*TEAL_DARK)
    pdf.rect(0, 0, PAGE_W, BAND_H, "F")

    # Logo inside a white chip
    logo_w = 16
    if logo_bytes:
        try:
            pdf.set_fill_color(255, 255, 255)
            pdf.rect(MARGIN - 1, 8, logo_w + 2, logo_w + 2, "F")
            pdf.image(io.BytesIO(logo_bytes), x=MARGIN, y=9, w=logo_w, h=logo_w)
        except Exception:
            pass

    name_x = MARGIN + (logo_w + 8 if logo_bytes else 0)

    def header_link(text, url, x, y, w):
        """Small light text line inside the band; clickable when url given."""
        R(7.5, (204, 240, 238))
        pdf.set_xy(x, y)
        pdf.cell(w, 4.2, fit_local(text, w), link=url or None)

    def fit_local(text, width_mm):
        text = str(text) if text is not None else ""
        while text and pdf.get_string_width(text + "...") > width_mm:
            text = text[:-1]
        return text + ("..." if text != str(text) else "")

    B(15, (255, 255, 255))
    pdf.set_xy(name_x, 8)
    pdf.cell(95, 6, site_name)

    line_y = 14.8
    for part in [address, hotline]:
        if part:
            header_link(part, f"tel:{hotline}" if part == hotline else None,
                        name_x, line_y, 100)
            line_y += 4.4
    if contact_email:
        header_link(contact_email, f"mailto:{contact_email}",
                    name_x, line_y, 100)
        line_y += 4.4
    if website:
        header_link(_strip_scheme(website), website, name_x, line_y, 100)

    # Right side: INVOICE title + meta
    meta_x = CONTENT_RIGHT - 70
    B(20, (255, 255, 255))
    pdf.set_xy(meta_x, 9)
    pdf.cell(70, 8, "INVOICE", align="R")

    created = order.created_at.strftime("%d %b %Y") if order.created_at else ""
    invoice_no = "INV-" + str(order.order_number).removeprefix("ORD-")
    R(8.5, (224, 247, 250))
    pdf.set_xy(meta_x, 18.5)
    pdf.cell(70, 4.2, f"Invoice No: {invoice_no}", align="R")
    pdf.set_xy(meta_x, 22.7)
    pdf.cell(70, 4.2, f"Date: {created}", align="R")

    # ---------- Billed To (left block) ----------
    user_snap = order.get_user_snapshot() or {}
    billed_name = order.full_name or user_snap.get("full_name") or "Customer"

    y = 44
    B(9, GRAY)
    pdf.set_xy(MARGIN, y)
    pdf.cell(60, 5, "BILLED TO")
    y += 7.5

    B(11, DARK)
    pdf.set_xy(MARGIN, y)
    pdf.cell(100, 6, billed_name)
    y += 8

    R(8.5, GRAY)
    phone_link = "tel:" + __import__("re").sub(r"[^+\d]", "", str(order.phone_number or ""))
    for text, link in [
        (order.phone_number, phone_link),
        (order.email, f"mailto:{order.email}" if order.email else None),
        (order.address, None),
        (", ".join(filter(None, [str(order.thana or ''), str(order.district or '')])), None),
    ]:
        if not str(text or '').strip():
            continue
        pdf.set_xy(MARGIN, y)
        pdf.cell(100, 4.6, str(text), link=link)
        y += 5

    # ---------- Items Table (wrapping cells, zebra rows) ----------
    cols = [("Item", 78, "L"), ("Code", 32, "L"), ("Qty", 12, "C"),
            ("Unit Price", 28, "R"), ("Total", 32, "R")]

    def draw_table_header(y):
        pdf.set_fill_color(*TEAL_DARK)
        B(9, (255, 255, 255))
        x = MARGIN
        for label, w, align in cols:
            pdf.set_xy(x, y)
            pdf.cell(w, 8, label, fill=True, align=align)
            x += w
        return y + 8

    y = draw_table_header(max(y + 4, 70))

    subtotal = 0.0
    item_discount_total = 0.0

    for item_idx, item in enumerate(items):
        psnap = item.get_product_snapshot() or {}
        vsnap = item.get_variant_snapshot() or {}

        p_name = psnap.get("name") or f"Product #{item.product_id}"
        attrs = vsnap.get("selected_attributes_display")
        unit_price = float(item.unit_price or 0)
        qty = int(item.quantity or 0)
        bonus = int(item.bonus_quantity or 0)
        line_total = float(item.price_at_purchase or 0)
        item_discount_total += float(item.discount_amount or 0)

        qty_display = str(qty) + (f" (+{bonus})" if bonus else "")
        code_txt = str(psnap.get("product_code") or "")
        name_text = p_name + (f"\n{attrs}" if attrs else "")

        name_w = cols[0][1] - 4
        code_w = cols[1][1] - 3

        # Measure wrapped heights BEFORE drawing (so the zebra rect fits).
        B(9, DARK)
        name_lines = pdf.multi_cell(name_w, 4.6, name_text,
                                    dry_run=True, output="LINES")
        R(7.5, GRAY)
        code_lines = pdf.multi_cell(code_w, 3.8, code_txt,
                                    dry_run=True, output="LINES")
        row_h = max(len(name_lines), len(code_lines)) * 4.4 + 3.5

        # Zebra stripe behind alternate rows
        if item_idx % 2 == 1:
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(MARGIN, y, CONTENT_RIGHT - MARGIN, row_h, "F")

        # Item column (wraps to as many lines as needed)
        pdf.set_xy(MARGIN + 2, y + 1.5)
        B(9, DARK)
        pdf.multi_cell(name_w, 4.6, name_text)

        # Code column (also wraps when very long)
        pdf.set_xy(MARGIN + cols[0][1] + 2, y + 1.5)
        R(8, GRAY)
        pdf.multi_cell(code_w, 3.8, code_txt)

        # Qty / Unit Price / Total: vertically centered single lines
        cell_y = y + max((row_h / 2) - 2.5, 1.5)
        pdf.set_xy(MARGIN + cols[0][1] + cols[1][1], cell_y)
        R(9, DARK)
        pdf.cell(cols[2][1], 5, qty_display, align="C")

        pdf.set_x(MARGIN + cols[0][1] + cols[1][1] + cols[2][1])
        pdf.cell(cols[3][1], 5, f"{pdf.currency}{unit_price:,.0f}", align="R")

        B(9, DARK)
        pdf.set_x(MARGIN + cols[0][1] + cols[1][1] + cols[2][1] + cols[3][1])
        pdf.cell(cols[4][1], 5, f"{pdf.currency}{line_total:,.0f}", align="R")

        # Row separator
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.2)
        pdf.line(MARGIN, y + row_h, CONTENT_RIGHT, y + row_h)

        y += row_h


    # ---------- Discount Breakdown ----------
    order_discount = float(order.total_discount or 0)
    breakdown_entries = []
    try:
        snap = json.loads(order.discount_snapshot or "{}")
        raw = list(snap.get("discount_breakdown", [])) + list(
            snap.get("bogo_details", [])
        )
        for entry in raw:
            amount = float(entry.get("amount") or 0)
            etype = str(entry.get("type") or "")
            is_bogo = etype == "bogo"
            if amount <= 0 and not is_bogo:
                continue
            label = entry.get("name") or (
                "Discount" if etype == "price_discount" else etype
            )
            pct = float(entry.get("get_discount_percent") or 0)
            if is_bogo and pct >= 100:
                value = "FREE"
                color = TEAL_DARK
            else:
                value = f"-{pdf.currency}{amount:,.0f}"
                color = (220, 38, 38)
            breakdown_entries.append((str(label), value, color))
    except Exception:
        breakdown_entries = []

    # ---------- Totals ----------
    y += 8
    totals_x = CONTENT_RIGHT - 82

    def total_line(label, value, strong=False, color=DARK):
        nonlocal y
        h = 10 if strong else 6.5
        if strong:
            pdf.set_fill_color(*TEAL)
            B(11.5, (255, 255, 255))
        elif color != DARK:
            R(9.5, color)
        else:
            R(10, color)
        pdf.set_xy(totals_x, y)
        pdf.cell(50, h, label, fill=strong, align="L")
        pdf.set_xy(totals_x + 50, y)
        pdf.cell(32, h, value, fill=strong, align="R")
        y += h

    grand_total = float(order.total_price or 0)
    total_disc = order_discount + item_discount_total
    shown_subtotal = subtotal if subtotal > 0 else (grand_total + total_disc)

    total_line("Subtotal", f"{pdf.currency}{shown_subtotal:,.0f}")

    if total_disc > 0 or breakdown_entries:
        R(8.5, GRAY)
        pdf.set_xy(totals_x, y)
        pdf.cell(82, 5, "DISCOUNT BREAKDOWN")
        y += 6.5

        for label, value, color in breakdown_entries:
            entry_start_y = y
            R(9, color)
            pdf.set_xy(totals_x + 4, y)
            pdf.multi_cell(48, 4.6, label)
            pdf.set_xy(totals_x + 54, entry_start_y)
            pdf.cell(30, 5, value, align="R")
            y = max(pdf.get_y(), entry_start_y + 5) + 1

        if total_disc > 0:
            total_line(
                "Total Discount",
                f"-{pdf.currency}{total_disc:,.0f}",
                color=(220, 38, 38),
            )
            y += 1

    total_line("Grand Total", f"{pdf.currency}{grand_total:,.0f}", strong=True)

    # ---------- Footer: generation details (Bangladesh time) ----------
    note_y = PAGE_H - 20
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, note_y, CONTENT_RIGHT, note_y)

    try:
        from zoneinfo import ZoneInfo

        now_bd = datetime.now(ZoneInfo("Asia/Dhaka"))
    except Exception:
        now_bd = datetime.now()

    R(8, LIGHT_GRAY)
    pdf.set_xy(MARGIN, note_y + 2.5)
    pdf.cell(
        0, 4,
        f"Invoice Generated: {now_bd.strftime('%d %b %Y, %I:%M:%S %p')} "
        f"(GMT+6:00, Bangladesh Time)",
    )

    footer_contact = ", ".join(filter(None, [hotline, contact_email]))
    second_line = "System Generated Invoice"
    if footer_contact:
        second_line += f" | {site_name} | {footer_contact}"
    pdf.set_xy(MARGIN, note_y + 6.5)
    pdf.cell(0, 4, second_line)

    return bytes(pdf.output())