# Skill 1: Multimodal OCR Document Extraction & Target Selection

## 1. Domain Objective
Extract accurate, context-aware financial figures from document images (payslips, receipts, invoices, bills) linked to events with missing amounts, without misinterpreting line items, gross totals, or previous balances.

---

## 2. Document Taxonomy & Extraction Rules

### A. Payroll / Income Documents (e.g., `image_01`)
- **Document Features**: Displays gross salary, itemized allowances/deductions, tax, net pay, and amount in words.
- **Rule**: **Always pick `net_pay`**. The financial event represents the net cash deposited into the bank account.
- **Counter-example / Trap**: Never pick `total_earnings` or `gross_pay`.

### B. Rental Receipts & Outstanding Obligations (e.g., `image_02`)
- **Document Features**: Displays total rent agreement amount, previous payments received, balance due now.
- **Rule**: **Pick `balance_due`**. The financial event represents the remaining scheduled payment.
- **Counter-example / Trap**: Never pick the total agreement amount if part has already been paid.

### C. Retail, Grocery & E-commerce Invoices (e.g., `image_03`, `image_04`, `image_06`, `image_07`, `image_10`, `image_13`)
- **Document Features**: Itemized SKU list, subtotal, tax/GST, grand total, payment method.
- **Rule**: **Pick `grand_total` or `total_amount_received`**.
- **Counter-example / Trap**: Never pick an individual line item price or subtotal.

### D. Utility & Telecom Bills (e.g., `image_05`, `image_09`, `image_16`)
- **Document Features**: Previous balance, current charges, total amount due by due date, late payment fee.
- **Rule**: **Pick `amount_due_by_date`** or `total_amount_received` for settled payments.
- **Counter-example / Trap**: Never pick previous balance or amount due after late date.

### E. Medical & Hospital Bills (e.g., `image_11`)
- **Document Features**: Provisional billing summary, advance deposits paid, net balance payable.
- **Rule**: **Pick `balance_payable`**.
- **Counter-example / Trap**: Never pick advance payment paid earlier or individual ward/medication charges.

### F. Travel, Taxi & Airline Receipts (e.g., `image_12`, `image_15`)
- **Document Features**: Base fare, airport fees, taxes, grand total, cash tendered, change.
- **Rule**: **Pick `grand_total`**.
- **Counter-example / Trap**: Never pick cash tendered or change returned.

### G. Handwritten Receipts (e.g., `image_14`)
- **Document Features**: Handwritten SKU lines, tax, handwritten `TOTAL`.
- **Rule**: **Pick handwritten `TOTAL`**. Match against amount in words if available.

---

## 3. OCR Context Injection Structure
Every OCR request sends:
1. The PNG image bytes (`dataset/media/images/<image_id>.png`).
2. Linked event metadata: `event_id`, `event_type`, `category`, `description`, `direction`, `status`, `expected_currency`.
3. Related messages linked to the same event.

---

## 4. Exact Stored JSON Schema (`code/cache/ocr/{image_id}.json`)

```json
{
  "image_id": "image_01",
  "related_event_id": "event_253",
  "document_metadata": {
    "document_type": "payslip",
    "document_date": "2019-08-31",
    "currency": "IDR",
    "invoice_or_receipt_number": "PAY-2019-08"
  },
  "extracted_candidates": [
    { "label": "total_earnings", "amount": 4780800.0, "is_line_item": false },
    { "label": "deductions", "amount": 415800.0, "is_line_item": false },
    { "label": "net_pay", "amount": 4365000.0, "is_line_item": false }
  ],
  "amount_in_words": "Four Million Three Hundred Sixty Five Thousand Rupiahs",
  "selection": {
    "chosen_amount": 4365000.0,
    "chosen_label": "net_pay",
    "currency": "IDR",
    "confidence_score": 0.99,
    "selection_reasoning": "Event event_253 is a net salary income. Selected net_pay which matches amount in words."
  },
  "extraction_status": "ok"
}
```
