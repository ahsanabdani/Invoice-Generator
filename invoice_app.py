"""
Invoice Generator — Flask Backend
Generates professional A4 PDF invoices using ReportLab canvas.
"""
import io
from flask import Flask, request, send_file, send_from_directory
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────
# Color palette  (R, G, B  as 0–1 floats)
# ─────────────────────────────────────────────────────────────────
NAVY  = (0.106, 0.137, 0.251)   # #1b2340
AMBER = (0.769, 0.400, 0.114)   # #c4661d
LGRAY = (0.965, 0.961, 0.957)   # table row stripe
DGRAY = (0.200, 0.200, 0.220)   # body text
MGRAY = (0.530, 0.525, 0.545)   # secondary / captions
WHITE = (1.000, 1.000, 1.000)


# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _lines(text, max_lines=4):
    """Split a possibly-multi-line string, cap at max_lines."""
    return [l.strip() for l in str(text or '').split('\n') if l.strip()][:max_lines]


def _wrap(c, text, x, y, max_w, font, size, gap=13):
    """Draw word-wrapped text; returns the y position after the last line."""
    c.setFont(font, size)
    for word in str(text or '').split():
        test = (getattr(_wrap, '_line', '') + ' ' + word).strip()
        if c.stringWidth(test, font, size) <= max_w:
            _wrap._line = test
        else:
            c.drawString(x, y, getattr(_wrap, '_line', ''))
            y -= gap
            _wrap._line = word
    if getattr(_wrap, '_line', ''):
        c.drawString(x, y, _wrap._line)
        y -= gap
    _wrap._line = ''
    return y


# ─────────────────────────────────────────────────────────────────
# PDF Generation
# ─────────────────────────────────────────────────────────────────

def build_pdf(d: dict) -> tuple[io.BytesIO, float]:
    """
    Render the invoice to a BytesIO PDF buffer.
    Returns (buffer, total_amount).
    """
    buf = io.BytesIO()
    W, H = A4          # 595 × 842 pt
    M    = 50          # left / right margin
    CW   = W - 2 * M  # content width  ≈ 495 pt
    c    = rl_canvas.Canvas(buf, pagesize=A4)

    # ── Full-width header bar ─────────────────────────────────────
    BAR_H = 68
    c.setFillColorRGB(*NAVY)
    c.rect(0, H - BAR_H, W, BAR_H, fill=1, stroke=0)

    # Company name (left, inside bar)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(M, H - BAR_H + 24, d.get('company_name') or 'Your Company')

    # "INVOICE" wordmark (right, inside bar)
    c.setFillColorRGB(*AMBER)
    c.setFont("Helvetica-Bold", 32)
    c.drawRightString(W - M, H - BAR_H + 18, "INVOICE")

    # Amber accent strip under bar
    c.setFillColorRGB(*AMBER)
    c.rect(0, H - BAR_H - 4, W, 4, fill=1, stroke=0)

    y = H - BAR_H - 22

    # ── Company details (left) & Invoice meta (right) ────────────
    detail_y = y
    c.setFont("Helvetica", 8.5)
    c.setFillColorRGB(*MGRAY)
    for line in _lines(d.get('company_address'), 3):
        c.drawString(M, detail_y, line)
        detail_y -= 12
    if d.get('company_email'):
        c.drawString(M, detail_y, d['company_email'])
        detail_y -= 12
    if d.get('company_phone'):
        c.drawString(M, detail_y, d['company_phone'])

    # Meta block (right-aligned)
    meta_y = y
    meta_rows = [
        ("Invoice #",  d.get('invoice_number') or '—'),
        ("Issue Date", d.get('issue_date') or '—'),
        ("Due Date",   d.get('due_date')   or '—'),
    ]
    for label, value in meta_rows:
        c.setFillColorRGB(*MGRAY)
        c.setFont("Helvetica", 7.5)
        c.drawRightString(W - M, meta_y, label)
        c.setFillColorRGB(*NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(W - M, meta_y - 12, value)
        meta_y -= 28

    # ── Divider ───────────────────────────────────────────────────
    rule_y = min(detail_y, meta_y) - 16
    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1.2)
    c.line(M, rule_y, W - M, rule_y)
    y = rule_y

    # ── Bill To ───────────────────────────────────────────────────
    y -= 18
    c.setFillColorRGB(*AMBER)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(M, y, "BILL TO")

    y -= 16
    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(M, y, d.get('client_name') or '—')

    y -= 14
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*DGRAY)
    for line in _lines(d.get('client_address'), 3):
        c.drawString(M, y, line)
        y -= 12
    if d.get('client_email'):
        c.drawString(M, y, d['client_email'])
        y -= 12

    # ── Items Table ───────────────────────────────────────────────
    y -= 16

    # Column x anchors
    X_DESC  = M + 4
    X_QTY   = M + CW * 0.565      # right-edge of qty col
    X_PRICE = M + CW * 0.735      # right-edge of price col
    X_AMT   = W - M - 4           # right-edge of amount col

    # Header row
    TH = 22
    c.setFillColorRGB(*NAVY)
    c.rect(M, y - TH + 6, CW, TH, fill=1, stroke=0)
    c.setFillColorRGB(*WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(X_DESC, y - 9, "DESCRIPTION")
    c.drawRightString(X_QTY,   y - 9, "QTY")
    c.drawRightString(X_PRICE, y - 9, "UNIT PRICE")
    c.drawRightString(X_AMT,   y - 9, "AMOUNT")
    y -= TH - 4

    # Item rows
    ROW_H    = 22
    subtotal = 0.0
    items    = d.get('items', [])

    for i, item in enumerate(items):
        if i % 2 == 0:
            c.setFillColorRGB(*LGRAY)
            c.rect(M, y - ROW_H + 8, CW, ROW_H, fill=1, stroke=0)

        qty    = float(item.get('qty',   1)   or 1)
        price  = float(item.get('price', 0)   or 0)
        amount = qty * price
        subtotal += amount

        y -= ROW_H
        c.setFillColorRGB(*DGRAY)
        c.setFont("Helvetica", 9)

        desc = str(item.get('description', ''))[:60]
        qty_str = str(int(qty)) if qty == int(qty) else f"{qty:.2f}"

        c.drawString(X_DESC, y + 8, desc)
        c.drawRightString(X_QTY,   y + 8, qty_str)
        c.drawRightString(X_PRICE, y + 8, f"${price:,.2f}")
        c.drawRightString(X_AMT,   y + 8, f"${amount:,.2f}")

    # Bottom border of table
    y -= 6
    c.setStrokeColorRGB(0.78, 0.78, 0.80)
    c.setLineWidth(0.5)
    c.line(M, y, W - M, y)

    # ── Totals Block ──────────────────────────────────────────────
    tax_rate      = float(d.get('tax_rate',      0) or 0)
    discount_rate = float(d.get('discount_rate', 0) or 0)
    tax_amt       = subtotal * tax_rate  / 100
    discount_amt  = subtotal * discount_rate / 100
    total         = subtotal + tax_amt - discount_amt

    y -= 12
    LX = W - M - 120    # left edge of totals label column
    RX = W - M          # right edge

    def totals_row(label, value_str, bold=False, size=9, color=DGRAY):
        nonlocal y
        c.setFillColorRGB(*MGRAY)
        c.setFont("Helvetica", size - 0.5)
        c.drawString(LX, y, label)
        c.setFillColorRGB(*color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawRightString(RX, y, value_str)
        y -= 15

    totals_row("Subtotal", f"${subtotal:,.2f}")
    if tax_rate:
        totals_row(f"Tax  ({tax_rate:.1f}%)", f"${tax_amt:,.2f}")
    if discount_rate:
        totals_row(f"Discount  ({discount_rate:.1f}%)", f"−${discount_amt:,.2f}")

    # Grand total line
    y -= 4
    c.setStrokeColorRGB(*NAVY)
    c.setLineWidth(1)
    c.line(LX - 10, y + 2, RX, y + 2)
    y -= 10

    c.setFillColorRGB(*NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(LX, y, "TOTAL")
    c.setFillColorRGB(*AMBER)
    c.setFont("Helvetica-Bold", 15)
    c.drawRightString(RX, y - 2, f"${total:,.2f}")

    # ── Notes ─────────────────────────────────────────────────────
    notes = (d.get('notes') or '').strip()
    if notes:
        y -= 38
        c.setFillColorRGB(*AMBER)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(M, y, "NOTES & PAYMENT TERMS")
        y -= 14
        c.setFillColorRGB(*DGRAY)
        y = _wrap(c, notes, M, y, CW - 10, "Helvetica", 9, 13)

    # ── Footer ────────────────────────────────────────────────────
    FY = 26
    c.setStrokeColorRGB(0.80, 0.80, 0.82)
    c.setLineWidth(0.5)
    c.line(M, FY + 14, W - M, FY + 14)

    # Amber left footer bar
    c.setFillColorRGB(*AMBER)
    c.rect(0, 0, 6, FY + 14, fill=1, stroke=0)

    c.setFillColorRGB(*MGRAY)
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(W / 2, FY, "Thank you for your business!")

    c.save()
    buf.seek(0)
    return buf, total


# ─────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# Serve CSS
@app.route('/styles.css')
def styles():
    return send_from_directory('static', 'styles.css')

# Serve JS
@app.route('/script.js')
def script():
    return send_from_directory('static', 'script.js')


@app.route('/generate', methods=['POST'])
def generate():
    f = request.form

    # Build items list (parallel arrays from form)
    items = []
    descs  = f.getlist('description[]')
    qtys   = f.getlist('qty[]')
    prices = f.getlist('price[]')
    for desc, qty, price in zip(descs, qtys, prices):
        if desc.strip():
            items.append({
                'description': desc.strip(),
                'qty':   float(qty   or 1),
                'price': float(price or 0),
            })

    data = {
        'company_name':    f.get('company_name',    '').strip(),
        'company_email':   f.get('company_email',   '').strip(),
        'company_phone':   f.get('company_phone',   '').strip(),
        'company_address': f.get('company_address', '').strip(),
        'invoice_number':  f.get('invoice_number',  'INV-001').strip(),
        'issue_date':      f.get('issue_date',       '').strip(),
        'due_date':        f.get('due_date',          '').strip(),
        'client_name':     f.get('client_name',      '').strip(),
        'client_email':    f.get('client_email',     '').strip(),
        'client_address':  f.get('client_address',   '').strip(),
        'tax_rate':        float(f.get('tax_rate',      0) or 0),
        'discount_rate':   float(f.get('discount_rate', 0) or 0),
        'notes':           f.get('notes',             '').strip(),
        'items':           items or [{'description': 'Services', 'qty': 1, 'price': 0}],
    }

    pdf_buf, _ = build_pdf(data)
    filename   = f"invoice_{data['invoice_number']}.pdf"

    return send_file(
        pdf_buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf',
    )


if __name__ == '__main__':
    print("🧾  Invoice Generator running at http://localhost:5000")
    app.run(debug=True, port=5000)
