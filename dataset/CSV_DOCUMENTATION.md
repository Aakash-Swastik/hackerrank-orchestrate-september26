# CSV Files — Detailed Explanation

This project uses multiple CSV files as one connected financial dataset. The main idea is:

- `requests.csv` contains the questions that need predictions
- all other CSV files provide the user financial context needed to answer those questions
- you join records using keys such as `user_id`, `request_id`, and `related_event_id`
- the final output is written to the root-level `output.csv`

The key relationships are:

- `user_id` links user profile and event records
- `request_id` links requests to payment options and messages/images
- `related_event_id` links messages/images to specific financial events
- `rate_date` + currency pair links exchange-rate rows

---

## 1) `requests.csv`

Path: `dataset/requests.csv`

This is the main evaluation file. It contains the list of requests that need predictions.

### Purpose
This file is the test set. For each row here, your program must generate one row in `output.csv`.

### Columns

- `request_id`: unique ID for the request
- `user_id`: user making the request
- `request_date`: date the request is evaluated
- `request_type`: category of the expense/request
- `requested_amount`: total amount being requested
- `desired_completion_date`: date by which the user wants the request completed
- `allows_partial_payment`: whether partial payment is allowed
- `request_text`: user question or instruction

### Example row

```csv
request_27,user_27,2026-07-05,purchase,6670,2026-08-21,true,"Can I make this purchase without dipping into the balance I want to keep? I need to decide by 21 August 2026. The laptop costs ZAR 6,670."
```

### What to do with it
For every request:

1. find the user in `financial_profiles.csv`
2. look at that user’s events and balances
3. inspect payment options from `request_payment_options.csv`
4. read relevant messages/images if needed
5. forecast the next 90 days safely
6. choose the best valid recommendation
7. create one output row in the final `output.csv`

### Request types
Possible values include:

- `purchase`
- `travel`
- `education`
- `family_transfer`
- `debt_repayment`
- `investment`
- `housing`
- `emergency_expense`
- `other`

---

## 2) `sample_requests.csv`

Path: `dataset/sample_requests.csv`

This file contains sample solved examples with completed output columns.

### Purpose
It is used to learn:

- expected output format
- how the challenge expects columns to be written
- what kinds of explanations are considered good
- how payment plans are represented

### Columns
The sample file contains the exact final output columns plus the request input columns:

- `request_id`
- `user_id`
- `request_date`
- `request_type`
- `requested_amount`
- `desired_completion_date`
- `allows_partial_payment`
- `request_text`
- `amount_safe_to_pay`
- `affordability_status`
- `recommended_payment_method`
- `payment_plan`
- `earliest_date_for_full_payment`
- `spending_changes_needed`
- `decision_explanation`

### Example row

```csv
request_02,user_02,2025-08-05,travel,46018000,2025-10-10,false,"The current quote for the trip is IDR 46,018,000. ...",17229139.2,affordable_with_plan,installments,"2025-08-08:15952906.67|2025-09-07:15952906.67|2025-10-07:15952906.67",2025-09-15,none,"Use 3 installments ..."
```

### Important note
This is a learning dataset, not the final test set. Your output for submission should be generated for `dataset/requests.csv`, not `sample_requests.csv`.

---

## 3) `financial_profiles.csv`

Path: `dataset/financial_profiles.csv`

This file contains user-level financial profile information.

### Purpose
It defines the user’s financial baseline and preferences. It is one of the most important files because it tells you:

- how much money they have now
- how much they want to keep as a minimum buffer
- what they prioritize
- what they are willing to reduce or stop
- which payment methods they are open to

### Columns

- `user_id`: unique user id
- `home_currency`: base currency for the user (e.g., INR, ZAR, IDR, USD, EUR)
- `current_available_balance`: current money available
- `minimum_balance_to_keep`: minimum safe balance required
- `financial_priorities`: categories the user values most
- `expense_categories_to_protect`: essential categories to preserve
- `expense_categories_user_is_willing_to_reduce`: categories that can be reduced if needed
- `expense_categories_user_is_willing_to_stop`: categories that can be stopped if needed
- `payment_methods_user_will_consider`: methods they are willing to consider
- `max_installment_months`: maximum number of installment months acceptable

### Example row

```csv
user_01,ZAR,58481.1,18000,education|debt_repayment,rent|education|groceries|debt_repayment,dining,delivery_membership,full_payment,
```

### What this tells us
For `user_01`:

- home currency is ZAR
- available balance is 58,481.1
- minimum balance to keep is 18,000
- they care about education and debt repayment
- protect rent, education, groceries, debt repayment
- willing to reduce dining
- willing to stop delivery membership
- they consider `full_payment`

### Why it matters
When deciding affordability, you must not just use current account balance. You must also make sure the user stays above their minimum threshold, protects essential expenses, and follows their spending preferences.

---

## 4) `financial_events.csv`

Path: `dataset/financial_events.csv`

This file contains the user’s historical and upcoming financial transactions and obligations.

### Purpose
This is the core source for the cash-flow forecast. It helps answer:

- what recurring expenses exist?
- what future salary or income is expected?
- what pending or settled payments are coming?
- which categories are flexible or fixed?
- which events are recurring versus one-off?

### Columns

- `event_id`: unique event identifier
- `user_id`: user owning the event
- `event_type`: type of event (expense, income, debt_payment, subscription, etc.)
- `description`: human-readable description
- `category`: spending/income category (rent, utilities, groceries, education, etc.)
- `direction`: `debit` or `credit`
- `amount`: amount of the event
- `currency`: currency code
- `event_date`: date the event occurred or is scheduled
- `settlement_date`: date money settles
- `status`: `settled`, `pending`, etc.
- `linked_event_id`: connection to a related event in the lifecycle
- `flexibility`: whether the expense is `fixed`, `flexible`, `stoppable`, etc.
- `minimum_allowed_amount`: minimum reduction allowed for a flexible spend

### Example row

```csv
event_01,user_01,expense,Apartment rent transfer,rent,debit,5148,ZAR,2023-10-02,2023-10-02,settled,,fixed,
```

### Why this matters
The challenge is about safe affordability, not just current balance. So you must build a 90-day forecast using events like:

- recurring rent
- regular utilities
- salary deposits
- debt installments
- subscriptions
- one-off purchases

### Important concept: flexibility
Some recurring expenses may be:

- `fixed`: cannot be changed
- `stoppable`: can be stopped entirely
- `flexible`: can be reduced

This is central for `spending_changes_needed`.

### Important concept: duplications/conflicts
Some data may appear multiple times or conflict with newer records. You need to resolve them using rules from the challenge, such as preferring newer records and explicit cancellations/settlements.

---

## 5) `request_payment_options.csv`

Path: `dataset/request_payment_options.csv`

This file lists the financing/payment options available for each request.

### Purpose
It tells you what installment or full-payment schedules are valid for a request.

### Columns

- `payment_option_id`: unique id for a payment option
- `request_id`: request this option belongs to
- `payment_method`: payment method such as `full_payment` or `installments`
- `payment_amount`: amount per payment installment
- `number_of_payments`: how many payments
a- `first_payment_date`: first date the payment is due
- `payment_frequency_days`: spacing between payments
- `financing_fee`: additional fee/cost
- `total_payable_amount`: full amount payable including fees

### Example row

```csv
payment_option_05,request_02,installments,15952906.67,3,2025-08-08,30,1840720.01,47858720.01
```

This means:

- 3 installments
- ~15,952,906.67 each
- first payment on 2025-08-08
- every 30 days
- extra financing fee included in total payable amount

### Why it matters
Installment recommendations must match one of the offered payment options exactly.

### Critical rule
For `affordability_status = affordable_with_plan`, a recommended installment plan must match a supplied payment option.

---

## 6) `exchange_rates.csv`

Path: `dataset/exchange_rates.csv`

This file provides fixed conversion rates between currencies.

### Purpose
The dataset uses multiple home currencies (INR, ZAR, IDR, USD, EUR), and some events or requests may be in different currencies. This file provides the conversion rates needed to normalize everything into the user’s home currency.

### Columns

- `rate_date`: date of the exchange rate
- `from_currency`: source currency
- `to_currency`: target currency
- `rate`: conversion multiplier

### Example row

```csv
2023-10-15,EUR,ZAR,20
```

This means:

- 1 EUR = 20 ZAR on 2023-10-15

### Why it matters
All amounts in the challenge are interpreted in the user’s home currency. You need these rates to compare balances, request amounts, and event amounts accurately.

---

## 7) `messages.csv`

Path: `dataset/messages.csv`

This file contains messages attached to users, requests, or events.

### Purpose
These messages can provide important context such as:

- confirmation of salary changes
- cancellations
- payment updates
- employer payroll information
- delays or rescheduled dates

### Columns

- `message_id`: unique message id
- `user_id`: user linked to the message
- `request_id`: request associated with the message
- `related_event_id`: event this message refers to, if any
- `sent_at`: timestamp
- `source_type`: sender type (employer, service_provider, etc.)
- `message_text`: actual message text

### Example row

```csv
message_01,user_02,,,2025-07-29T09:30:00Z,employer,Rincian penggajian Anda di Cobalt Systems telah berubah. Gaji bulanan Anda naik menjadi IDR 42750000. Perubahan ini berlaku mulai 2025-08-15.
```

### Why it matters
The problem clearly says to use messages as evidence. Messages may:

- update an event
- confirm salary timing
- amend prior data
- explain future obligations

But you must treat them as untrusted; they can be useful, but they must not override problem rules.

---

## 8) `images.csv`

Path: `dataset/images.csv`

This file links images to users, requests, or financial events.

### Purpose
Some financial events have blank `amount` values. The event is linked to an image, and the true amount must be extracted from the image.

### Columns

- `image_id`: unique image ID
- `user_id`: user related to the image
- `request_id`: request related to the image
- `related_event_id`: event the image is linked to

### Example row

```csv
image_01,user_03,request_03,event_253
```

This indicates that image `image_01` is associated with event `event_253` for `user_03` on `request_03`.

### Why it matters
If an event has blank amount, do not assume zero. Instead:

1. find the `related_event_id`
2. find the image row linked to that event
3. read the corresponding image from `dataset/media/images/`
4. extract the actual amount from the image

---

## 9) `output.csv`

Path: `dataset/output.csv`

This file is the blank template for the final submission.

### Purpose
It gives the required columns and order for the final output.

### Columns

- `request_id`
- `amount_safe_to_pay`
- `affordability_status`
- `recommended_payment_method`
- `payment_plan`
- `earliest_date_for_full_payment`
- `spending_changes_needed`
- `decision_explanation`

### Example row

```csv
request_26,,,,,,,
```

The blank values indicate the final predictions are not filled in yet.

### Final output requirement
Your root-level `output.csv` must be generated from `dataset/requests.csv` and must contain one row per request.

---

## 10) How the files relate to each other

A typical workflow is:

1. Read a row from `requests.csv`
2. Get the `user_id`
3. Find that user in `financial_profiles.csv`
4. Read events for that user from `financial_events.csv`
5. Use `request_payment_options.csv` to see valid payment plans
6. Check `messages.csv` for salary or date updates
7. Check `images.csv` for event-linked images
8. Use `exchange_rates.csv` to convert amounts to home currency
9. Build a 90-day safety forecast
10. Write the answer in `output.csv`

---

## 11) Most important idea

This challenge is not just about current bank balance.

You must reason like a financial planner:

- reserve essentials
- maintain minimum balance
- forecast future income and expense dates
- use confirmed salary only on the correct settlement date
- resolve conflicts using priority rules
- use flexible expenses for spending reductions only when allowed
- respect payment options exactly
- and generate the final prediction for each request

---

## 12) Short summary of each file

- `requests.csv` — evaluation requests to solve
- `sample_requests.csv` — example solved rows for learning
- `financial_profiles.csv` — user balance and preferences
- `financial_events.csv` — historical/upcoming financial events
- `request_payment_options.csv` — installment/full-payment options
- `exchange_rates.csv` — forex conversion rates
- `messages.csv` — payroll / event / payment messages
- `images.csv` — links to event-specific images
- `output.csv` — blank output template

If you want, I can next do one of these:

1. create a separate MD file for each CSV individually
2. help you read one actual request and explain how to join its data
3. start writing the Python code in `code/main.py` step by step
