"""
Invoice PDF generation service (system generated).

Multi-page A4 invoice (single page for small orders, additional pages
automatically when there are many line items):
- Teal header band with company logo, name, contact info & website link
  (repeated on every page)
- One large faint centered logo watermark across the page middle (anti-copy)
- Billed-to customer block, items table (wrapping cells, zebra rows),
  discount breakdown, totals with teal grand-total band
- Generation timestamp footer in Bangladesh time (GMT+6)
- Page numbers on continuation pages

Text is WRAPPED, never truncated. Fonts:
- Primary: best Latin font available on the host.
- Fallback (bundled): Noto Sans Bengali for Bangla glyphs (SIL OFL).
"""

import io
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fpdf import FPDF

MARGIN = 14
PAGE_W = 210
PAGE_H = 297
CONTENT_RIGHT = PAGE_W - MARGIN
CONTENT_BOTTOM = PAGE_H - 26  # leave ~26 mm for footer on each page

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
    """Build a clean, multi-page invoice PDF for an order.

    All text is WRAPPED — never truncated. If content would extend beyond
    the footer margin, a new page is started automatically (header band and
    table header are repeated on every page).
    """
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

    bangla_loaded = False
    if BUNDLED_BENGALI.exists():
        try:
            pdf.add_font("Bng", "", str(BUNDLED_BENGALI))
            bangla_loaded = True
        except Exception:
            pass

    if not primary_loaded and bangla_loaded:
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

    # ---------- Column layout ----------
    # Use the full content width (182 mm). The Code column is widened so that
    # typical product codes (PROD-YYYYMMDD-XXXXX ≈ 19 chars, ~40 mm at 7.5 pt)
    # render on a single line instead of wrapping and looking "hidden".
    cols = [("Item", 62, "L"), ("Code", 48, "L"), ("Qty", 12, "C"),
            ("Unit Price", 26, "R"), ("Total", 34, "R")]

    # ---------- Header band (teal, full width) — drawn on every page ----------
    BAND_H = 36

    def draw_watermark():
        if not logo_bytes:
            return
        try:
            wm_w = 105
            with pdf.local_context(fill_opacity=0.04):
                pdf.image(
                    io.BytesIO(logo_bytes),
                    x=(PAGE_W - wm_w) / 2,
                    y=(PAGE_H - wm_w) / 2 + 8,
                    w=wm_w,
                )
        except Exception:
            pass

    def draw_header_band():
        """Draw the teal header band with logo, site name, contact info, and
        the INVOICE title.  No text is truncated — everything wraps."""
        pdf.set_fill_color(*TEAL_DARK)
        pdf.rect(0, 0, PAGE_W, BAND_H, "F")

        logo_w = 16
        if logo_bytes:
            try:
                pdf.set_fill_color(255, 255, 255)
                pdf.rect(MARGIN - 1, 8, logo_w + 2, logo_w + 2, "F")
                pdf.image(io.BytesIO(logo_bytes), x=MARGIN, y=9, w=logo_w, h=logo_w)
            except Exception:
                pass

        name_x = MARGIN + (logo_w + 8 if logo_bytes else 0)

        B(15, (255, 255, 255))
        pdf.set_xy(name_x, 8)
        pdf.cell(95, 6, site_name)

        # Contact info lines — WRAP, never truncate
        line_y = 14.8
        for part in [address, hotline, contact_email]:
            if not part:
                continue
            R(7.5, (204, 240, 238))
            pdf.set_xy(name_x, line_y)
            pdf.multi_cell(100, 4.4, str(part), link=None)
            line_y = pdf.get_y()

        if website:
            R(7.5, (204, 240, 238))
            pdf.set_xy(name_x, line_y)
            pdf.multi_cell(100, 4.4, _strip_scheme(website), link=website)

        # Right side: INVOICE title + meta
        created = order.created_at.strftime("%d %b %Y") if order.created_at else ""
        invoice_no = "INV-" + str(order.order_number).removeprefix("ORD-")

        meta_x = CONTENT_RIGHT - 70
        B(20, (255, 255, 255))
        pdf.set_xy(meta_x, 9)
        pdf.cell(70, 8, "INVOICE", align="R")

        R(8.5, (224, 247, 250))
        pdf.set_xy(meta_x, 18.5)
        pdf.cell(70, 4.2, f"Invoice No: {invoice_no}", align="R")
        pdf.set_xy(meta_x, 22.7)
        pdf.cell(70, 4.2, f"Date: {created}", align="R")

    def draw_table_header(y):
        pdf.set_fill_color(*TEAL_DARK)
        B(9, (255, 255, 255))
        x = MARGIN
        for label, w, align in cols:
            pdf.set_xy(x, y)
            pdf.cell(w, 8, label, fill=True, align=align)
            x += w
        return y + 8

    def ensure_page_break(y, needed):
        """If y + needed would exceed CONTENT_BOTTOM, start a new page,
        redraw the header band + watermark + table header, and return the
        new y for the first content row."""
        if y + needed > CONTENT_BOTTOM:
            pdf.add_page()
            draw_watermark()
            draw_header_band()
            return draw_table_header(BAND_H + 8)
        return None

    # ---------- Page 1 ----------
    pdf.add_page()
    draw_watermark()
    draw_header_band()

    # ---------- Billed To (left block) — first page only ----------
    user_snap = order.get_user_snapshot() or {}
    billed_name = order.full_name or user_snap.get("full_name") or "Customer"

    y = 44
    B(9, GRAY)
    pdf.set_xy(MARGIN, y)
    pdf.cell(60, 5, "BILLED TO")
    y += 7.5

    B(11, DARK)
    pdf.set_xy(MARGIN, y)
    pdf.multi_cell(100, 6, billed_name)
    y = pdf.get_y() + 2

    R(8.5, GRAY)
    phone_clean = re.sub(r"[^\d+]", "", str(order.phone_number or ""))
    phone_link = "tel:" + phone_clean
    for text, link in [
        (order.phone_number, phone_link),
        (order.email, f"mailto:{order.email}" if order.email else None),
        (order.address, None),
        (", ".join(filter(None, [str(order.thana or ''), str(order.district or '')])), None),
    ]:
        if not str(text or '').strip():
            continue
        pdf.set_xy(MARGIN, y)
        pdf.multi_cell(100, 4.6, str(text), link=link)
        y = pdf.get_y() + 1

    # ---------- Items Table ----------
    y = max(y, 70)

    # Pre-compute all rows so we can measure heights and handle page breaks
    # before committing any text to the page.
    row_data = []
    for item in items:
        psnap = item.get_product_snapshot() or {}
        vsnap = item.get_variant_snapshot() or {}

        p_name = psnap.get("name") or f"Product #{item.product_id}"
        attrs = vsnap.get("selected_attributes_display")
        unit_price = float(item.unit_price or 0)
        qty = int(item.quantity or 0)
        bonus = int(item.bonus_quantity or 0)
        line_total = float(item.price_at_purchase or 0)

        qty_display = str(qty) + (f" (+{bonus})" if bonus else "")
        code_txt = str(psnap.get("product_code") or "")
        name_text = p_name + (f"\n{attrs}" if attrs else "")

        name_w = cols[0][1] - 4
        code_w = cols[1][1] - 3

        B(9, DARK)
        name_lines = pdf.multi_cell(name_w, 4.6, name_text, dry_run=True, output="LINES")
        R(7.5, GRAY)
        code_lines = pdf.multi_cell(code_w, 3.8, code_txt, dry_run=True, output="LINES")
        name_h = len(name_lines) * 4.6
        code_h = len(code_lines) * 3.8
        row_h = max(name_h, code_h) + 5

        row_data.append({
            "name_text": name_text, "code_txt": code_txt,
            "unit_price": unit_price, "qty_display": qty_display,
            "line_total": line_total, "row_h": row_h,
        })

    # Draw table header (handle page break before first row)
    nb = ensure_page_break(y, 8)
    if nb is not None:
        y = nb
    else:
        y = draw_table_header(y)

    for item_idx, rd in enumerate(row_data):
        # Page-break check before drawing the row
        nb = ensure_page_break(y, rd["row_h"])
        if nb is not None:
            y = nb

        # Zebra stripe behind alternate rows
        if item_idx % 2 == 1:
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(MARGIN, y, CONTENT_RIGHT - MARGIN, rd["row_h"], "F")

        # Item column (wraps)
        pdf.set_xy(MARGIN + 2, y + 2)
        B(9, DARK)
        pdf.multi_cell(cols[0][1] - 4, 4.6, rd["name_text"])

        # Code column (wraps)
        pdf.set_xy(MARGIN + cols[0][1] + 2, y + 2)
        R(7.5, GRAY)
        pdf.multi_cell(cols[1][1] - 3, 3.8, rd["code_txt"])

        # Qty / Unit Price / Total
        cell_y = y + max((rd["row_h"] / 2) - 2.5, 2)
        pdf.set_xy(MARGIN + cols[0][1] + cols[1][1], cell_y)
        R(9, DARK)
        pdf.cell(cols[2][1], 5, rd["qty_display"], align="C")

        pdf.set_x(MARGIN + cols[0][1] + cols[1][1] + cols[2][1])
        pdf.cell(cols[3][1], 5, f"{pdf.currency}{rd['unit_price']:,.0f}", align="R")

        B(9, DARK)
        pdf.set_x(MARGIN + cols[0][1] + cols[1][1] + cols[2][1] + cols[3][1])
        pdf.cell(cols[4][1], 5, f"{pdf.currency}{rd['line_total']:,.0f}", align="R")

        # Row separator
        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.2)
        pdf.line(MARGIN, y + rd["row_h"], CONTENT_RIGHT, y + rd["row_h"])

        y += rd["row_h"]

    # ---------- Discount Breakdown ----------
    order_discount = float(order.total_discount or 0)
    grand_total = float(order.total_price or 0)
    total_disc = order_discount
    snap = json.loads(order.discount_snapshot or "{}")
    shown_subtotal = float(
        snap.get("subtotal_before_discount", grand_total + total_disc)
    )

    breakdown_entries = []
    try:
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
    y += 6
    totals_x = CONTENT_RIGHT - 82

    # Estimate height of the totals block so we can page-break if needed.
    # BOGO labels are long and wrap; assume up to 3 lines per entry.
    total_height_estimate = 6.5  # Subtotal line
    if total_disc > 0 or breakdown_entries:
        total_height_estimate += 5  # "DISCOUNT BREAKDOWN" header
        total_height_estimate += len(breakdown_entries) * (4.6 * 3 + 5 + 1.5)
        if total_disc > 0:
            total_height_estimate += 6.5  # Total Discount line
    total_height_estimate += 10  # Grand Total (strong, taller)
    total_height_estimate += 8   # footer gap

    nb = ensure_page_break(y, total_height_estimate)
    if nb is not None:
        y = nb

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

    total_line("Subtotal", f"{pdf.currency}{shown_subtotal:,.0f}")

    if total_disc > 0 or breakdown_entries:
        R(8.5, GRAY)
        pdf.set_xy(totals_x, y)
        pdf.cell(82, 5, "DISCOUNT BREAKDOWN")
        y += 6.5

        for label, value, color in breakdown_entries:
            R(9, color)
            pdf.set_xy(totals_x + 4, y)
            # Wrap label to available width; full text always shown
            pdf.multi_cell(50, 4.6, str(label))
            label_end_y = pdf.get_y()

            # Place value at the right, aligned with the last wrapped line
            value_x = totals_x + 56
            value_w = 26
            pdf.set_xy(value_x, label_end_y - 4.6)
            pdf.cell(value_w, 5, value, align="R")

            y = label_end_y + 1.5

        if total_disc > 0:
            total_line(
                "Total Discount",
                f"-{pdf.currency}{total_disc:,.0f}",
                color=(220, 38, 38),
            )
            y += 1

    total_line("Grand Total", f"{pdf.currency}{grand_total:,.0f}", strong=True)

    # ---------- Footer ----------
    # Position after content; if it would overflow, give the footer its own page.
    footer_y = max(y + 12, PAGE_H - 22)

    if footer_y > PAGE_H - 12:
        pdf.add_page()
        draw_header_band()
        footer_y = BAND_H + 40

    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, footer_y, CONTENT_RIGHT, footer_y)

    try:
        from zoneinfo import ZoneInfo
        now_bd = datetime.now(ZoneInfo("Asia/Dhaka"))
    except Exception:
        now_bd = datetime.now()

    R(8, LIGHT_GRAY)
    pdf.set_xy(MARGIN, footer_y + 2.5)
    pdf.multi_cell(
        CONTENT_RIGHT - MARGIN, 4,
        f"Invoice Generated: {now_bd.strftime('%d %b %Y, %I:%M:%S %p')} "
        f"(GMT+6:00, Bangladesh Time)",
    )

    footer_contact = ", ".join(filter(None, [hotline, contact_email]))

    # Thank-you note
    R(8, GRAY)
    pdf.set_xy(MARGIN, footer_y + 6.5)
    pdf.cell(CONTENT_RIGHT - MARGIN, 4, "Thank you for your order!", align="C")

    pdf.set_xy(MARGIN, footer_y + 10.5)
    second_line = "System Generated Invoice"
    if footer_contact:
        second_line += f" | {site_name} | {footer_contact}"
    R(7.5, LIGHT_GRAY)
    pdf.cell(CONTENT_RIGHT - MARGIN, 3.5, second_line, align="C")

    # Page number (only when there are multiple pages)
    if pdf.page_no() > 1:
        R(7.5, LIGHT_GRAY)
        pdf.set_xy(CONTENT_RIGHT - 20, footer_y + 10.5)
        pdf.cell(20, 3.5, f"Page {pdf.page_no()}", align="R")

    return bytes(pdf.output())
