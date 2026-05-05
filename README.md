# 🧾 Invoice Generator -_-

A web-based invoice generator with Flask backend and ReportLab PDF engine.

## Quick Start

```bash
pip install -r requirements.txt
python invoice_app.py
# → Open http://localhost:5000
```

## Files

| File | Purpose |
|------|---------|
| `invoice_app.py`   | Flask server + ReportLab PDF builder |
| `index.html` | Web form |

## API

| Route | Method | Description |
|-------|--------|-------------|
| `/`         | GET  | Invoice form UI         |
| `/generate` | POST | Build + download PDF    |

## Form Fields

**Business:** `company_name`, `company_email`, `company_phone`, `company_address`  
**Invoice:** `invoice_number`, `issue_date`, `due_date`  
**Client:** `client_name`, `client_email`, `client_address`  
**Items:** `description[]`, `qty[]`, `price[]` *(parallel arrays)*  
**Summary:** `tax_rate`, `discount_rate`, `notes`

## Upgrade Ideas

1. **Email delivery** — `smtplib` to send the PDF directly to the client
2. **Invoice history** — SQLite DB to store and re-download past invoices
3. **Logo upload** — accept company logo PNG, embed in PDF header
4. **Multi-currency** — currency selector (USD/EUR/GBP) with symbol formatting
5. **Recurring invoices** — schedule auto-generation monthly via APScheduler


---

## 👤 Author -_-

#### AHSAN ALI (2K23/TCS/9) & MOHAMMAD OUNAIN (2K23/TCS/36)

---

## 📌 Notes

This project is just for of  learning purpose.

---
