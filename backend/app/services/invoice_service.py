"""
Invoice PDF generation service (system generated).

Builds a clean A4 invoice PDF for an order using fpdf2:
- Company logo + name header (from site settings)
- Faint tiled logo watermark across the whole page (anti-copy)
- Billed-to customer block, items table, totals
- "System generated" note at the bottom
"""

import io

import httpx
from fpdf import FPDF

# Unicode fonts that may exist on the host (Bangla support via Nirmala/Vrinda)
FONT_CANDIDATES = [
    ("C:/Windows/Fonts/nirmala.ttf", "bangla"),
    ("C:/Windows/Fonts/vrinda.ttf", "bangla"),
    ("C:/Windows/Fonts/segoeui.ttf", "latin"),
    ("C:/Windows/Fonts/arial.ttf", "latin"),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "latin"),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "latin"),
]

PAGE_W = 210  # A4 mm
PAGE_H = 297


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


class InvoicePDF(FPDF):
    def __init__(self):
        super().__init__(format="A4")
        self.uni_font_loaded = False
        self.currency = "BDT "

    def _t(self, text):
        """Sanitize text when only latin-1 font is available."""
        text = str(text) if text is not None else ""
        if self.uni_font_loaded:
            return text
        return text.encode("latin-1", "replace").decode("latin-1")


def _bold_font(pdf, size, color=None):
    pdf.set_font("Uni", "B" if pdf.uni_font_loaded else "", size)
    if color:
        pdf.set_text_color(*color)


def _regular_font(pdf, size, color=None):
    pdf.set_font("Uni", "", size)
    if color:
        pdf.set_text_color(*color)


def build_invoice_pdf(order, items, settings) -> bytes:
    """Build the invoice PDF for an order."""
    site_name = getattr(settings, "site_name", None) or "WaveNotebook"
    hotline = getattr(settings, "hotline_number", None) or getattr(settings, "contact_phone", None) or ""
    contact_email = getattr(settings, "contact_email", None) or ""
    address = getattr(settings, "contact_address", None) or ""
    logo_url = getattr(settings, "logo_url", None)

    pdf = InvoicePDF()
    pdf.set_auto_page_break(auto=True, margin=22)

    # ---------- Font setup (Unicode for Bangla names / Taka sign) ----------
    uni_loaded = False
    is_bangla_capable = False
    bold_ok = False
    for path, kind in FONT_CANDIDATES:
        try:
            pdf.add_font("Uni", "", path)
            try:
                pdf.add_font("Uni", "B", path)
                bold_ok = True
            except Exception:
                pass
            uni_loaded = True
            is_bangla_capable = kind == "bangla"
            break
        except Exception:
            continue

    pdf.uni_font_loaded = uni_loaded
    if uni_loaded:
        pdf.currency = "\u09f3 " if is_bangla_capable else "BDT "
        try:
            pdf.set_text_shaping(True)
        except Exception:
            pass

    def B(size, color=None):
        _bold = "B" if uni_loaded and bold_ok else ""
        pdf.set_font("Uni", _bold, size)
        if color:
            pdf.set_text_color(*color)

    def R(size, color=None):
        pdf.set_font("Uni", "", size)
        if color:
            pdf.set_text_color(*color)

    pdf.add_page()

    logo_bytes = _fetch_logo_bytes(logo_url)

    # ---------- Watermark: faint tiled logo over the whole page ----------
    wm_size = 46
    step_x, step_y = 62, 48
    try:
        if logo_bytes:
            y = 14
            row_idx = 0
            while y < PAGE_H - wm_size:
                x = 12 if row_idx % 2 == 0 else 42
                while x < PAGE_W - wm_size:
                    with pdf.local_context(fill_opacity=0.045):
                        pdf.image(io.BytesIO(logo_bytes), x=x, y=y, w=wm_size)
                    x += step_x
                y += step_y
                row_idx += 1
    except Exception:
        pdf.set_font("Uni" if uni_loaded else "Helvetica", "", 24)
        pdf.set_text_color(238, 243, 243)
        y = 20
        row_idx = 0
        while y < PAGE_H - 20:
            x = 15 if row_idx % 2 == 0 else 55
            while x < PAGE_W - 40:
                pdf.set_xy(x, y)
                pdf.cell(0, 10, pdf._t(site_name))
                x += 75
            y += 30
            row_idx += 1
        pdf.set_text_color(30, 41, 59)

    # ---------- Header ----------
    logo_w = 20
    if logo_bytes:
        try:
            pdf.image(io.BytesIO(logo_bytes), x=14, y=12, w=logo_w, h=logo_w)
        except Exception:
            pass

    name_x = 14 + (logo_w + 6 if logo_bytes else 0)
    B(19, (15, 23, 42))
    pdf.set_xy(name_x, 13)
    pdf.cell(0, 9, pdf._t(site_name))

    R(9, (100, 116, 139))
    info_line = ", ".join(filter(None, [address.strip(), hotline.strip()]))[:80]
    pdf.set_x(name_x)
    pdf.cell(0, 5, pdf._t(info_line))
    if contact_email:
        pdf.set_x(name_x)
        pdf.cell(0, 5, pdf._t(contact_email))

    # INVOICE label on the right
    B(24, (13, 148, 136))
    pdf.set_xy(-72, 14)
    pdf.cell(58, 10, "INVOICE", align="R")

    created = order.created_at.strftime("%d %b %Y") if order.created_at else ""
    R(9, (71, 85, 105))
    pdf.set_xy(-72, 25)
    pdf.cell(58, 5, pdf._t(f"Invoice No: {order.order_number}"), align="R")
    pdf.set_x(-72)
    pdf.cell(58, 5, pdf._t(f"Date: {created}"), align="R")

    # Divider
    pdf.set_draw_color(13, 148, 136)
    pdf.set_line_width(0.6)
    pdf.line(14, 42, PAGE_W - 14, 42)
    pdf.set_y(50)

    # ---------- Billed To ----------
    user_snap = order.get_user_snapshot() or {}
    billed_name = order.full_name or user_snap.get("full_name", "") or "Customer"
    B(10, (100, 116, 139))
    pdf.set_x(14)
    pdf.cell(0, 6, "BILLED TO")
    pdf.set_y(pdf.get_y() + 7)

    R(11, (15, 23, 42))
    pdf.set_x(14)
    pdf.multi_cell(95, 6, pdf._t(billed_name))

    R(9.5, (71, 85, 105))
    contact_lines = [
        order.phone_number,
        order.email,
        order.address,
        ", ".join(filter(None, [str(order.thana or ""), str(order.district or "")])),
    ]
    for line in filter(None, [str(l).strip() for l in contact_lines]):
        pdf.set_x(14)
        pdf.multi_cell(95, 5, pdf._t(line))

    status_label = str(order.status or "").upper()
    status_y = max(pdf.get_y() - 30, 52)
    R(9.5, (71, 85, 105))
    pdf.set_xy(-87, status_y)
    pdf.cell(73, 5, pdf._t(f"Order Status: {status_label}"), align="R")


    # ---------- Items Table ----------
    col_widths = [88, 28, 14, 32, 34]  # Item, Code, Qty, Unit Price, Total
    table_x = 14

    def table_header():
        pdf.set_fill_color(15, 118, 110)
        pdf.set_text_color(255, 255, 255)
        B(9.5)
        pdf.set_x(table_x)
        headers = ["Item", "Code", "Qty", "Unit Price", "Total"]
        for i, h in enumerate(headers):
            align = "C" if i == 2 else ("R" if i >= 3 else "L")
            pdf.cell(col_widths[i], 9, h, align=align, fill=True)
        pdf.ln(9)

    table_header()

    grand_total = float(order.total_price or 0)
    subtotal = 0.0
    item_discount_total = 0.0
    fill = False

    for item in items:
        psnap = item.get_product_snapshot() or {}
        vsnap = item.get_variant_snapshot() or {}

        p_name = psnap.get("name") or f"Product #{item.product_id}"
        attrs = vsnap.get("selected_attributes_display")
        unit_price = float(item.unit_price or 0)
        qty = int(item.quantity or 0)
        bonus = int(item.bonus_quantity or 0)
        line_total = float(item.price_at_purchase or 0)
        line_discount = float(item.discount_amount or 0)

        qty_display = str(qty) + (f" (+{bonus})" if bonus else "")

        if pdf.get_y() > PAGE_H - 70:
            pdf.add_page()
            table_header()

        fill = not fill
        if fill:
            pdf.set_fill_color(246, 251, 250)

        start_y = pdf.get_y()

        # Item cell (name + variant attributes)
        pdf.set_xy(table_x + 2, start_y)
        B(9, (15, 23, 42))
        text = pdf._t(p_name) + (f"\n{pdf._t(attrs)}" if attrs else "")
        pdf.multi_cell(col_widths[0] - 4, 6, text, fill=True)
        row_h = max(pdf.get_y() - start_y, 10)

        code_txt = str(psnap.get("product_code") or "")
        R(8.5, (100, 116, 139))
        pdf.set_xy(table_x + col_widths[0], start_y)
        pdf.cell(col_widths[1], row_h, pdf._t(code_txt[:14]), fill=fill)

        R(9, (15, 23, 42))
        pdf.set_x(table_x + col_widths[0] + col_widths[1])
        pdf.cell(col_widths[2], row_h, qty_display, fill=fill, align="C")

        pdf.set_x(table_x + sum(col_widths[:3]))
        pdf.cell(col_widths[3], row_h, f"{pdf.currency}{unit_price:,.0f}", fill=fill, align="R")

        B(9, (15, 23, 42))
        pdf.set_x(table_x + sum(col_widths[:4]))
        pdf.cell(col_widths[4], row_h, f"{pdf.currency}{line_total:,.0f}", fill=fill, align="R")

        pdf.set_draw_color(226, 232, 240)
        pdf.set_line_width(0.2)
        pdf.line(table_x, start_y + row_h, PAGE_W - 14, start_y + row_h)
        pdf.set_y(start_y + row_h + 1)

        subtotal += unit_price * qty
        item_discount_total += line_discount

    order_discount = float(order.total_discount or 0)

    # ---------- Totals ----------
    pdf.ln(4)
    if pdf.get_y() > PAGE_H - 55:
        pdf.add_page()

    totals_x = PAGE_W - 84

    def total_row(label, value, strong=False, color=(15, 23, 42)):
        if strong:
            B(11, color)
        else:
            R(10, color)
        pdf.set_x(totals_x)
        pdf.cell(44, 7, pdf._t(label), align="L")
        pdf.set_x(totals_x + 44)
        pdf.cell(26, 7, pdf._t(value), align="R")
        pdf.ln(7)

    shown_subtotal = subtotal if subtotal > 0 else grand_total + order_discount + item_discount_total
    total_row("Subtotal", f"{pdf.currency}{shown_subtotal:,.0f}")
    total_disc = order_discount + item_discount_total
    if total_disc > 0:
        total_row("Discount", f"-{pdf.currency}{total_disc:,.0f}", color=(220, 38, 38))

    pdf.set_fill_color(13, 148, 136)
    B(12, (255, 255, 255))
    pdf.set_x(totals_x)
    pdf.cell(44, 10, "Grand Total", fill=True, align="L")
    pdf.set_x(totals_x + 44)
    pdf.cell(26, 10, f"{pdf.currency}{grand_total:,.0f}", fill=True, align="R")
    pdf.ln(12)

    # ---------- Footer Note (system generated) ----------
    note_y = PAGE_H - 26
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.3)
    pdf.line(14, note_y - 4, PAGE_W - 14, note_y - 4)

    R(8.5, (148, 163, 184))
    pdf.set_xy(14, note_y)
    pdf.cell(0, 5, "This is a computer generated invoice and does not require a signature.")

    footer_contact = ", ".join(filter(None, [hotline.strip(), contact_email.strip()]))
    if footer_contact:
        pdf.set_xy(14, note_y + 5)
        pdf.cell(0, 5, pdf._t(f"{site_name} | {footer_contact}"))

    return bytes(pdf.output())
    pdf.set_y(max(pdf.get_y(), 108))