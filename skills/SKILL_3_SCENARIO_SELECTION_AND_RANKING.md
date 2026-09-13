# Skill 3: Scenario Synthesis, Ranking & Fallback Selection

## 1. Scenario Search Space Synthesis

Node 4 (Summarizer) builds all candidate payment paths:

1. **Full Payment Today**: Pay 100% on `request_date`.
2. **Provider Installment Options**: Options from `request_payment_options.csv` satisfying `number_of_payments <= user.max_installment_months` and permitted by user preferences.
3. **Partial Payment**: (If permitted by request & user)
   - Payment 1 on `request_date`: `amount_safe_to_pay`
   - Payment 2 on `earliest_date_for_full_payment`: `requested_amount - amount_safe_to_pay`
   - Requires $0 < \text{amount\_safe\_to\_pay} < \text{requested\_amount}$ and `earliest_date <= desired_completion_date`.
4. **Wait Scenario**: Pay 100% on `earliest_date_for_full_payment` (if $\le$ `desired_completion_date`).
5. **Flexible Spending Reductions**: Attach `stop:<event_id>` or `reduce_to:<event_id>:<amount>` changes for flexible recurring expenses if no zero-spending-change option is safe.

---

## 2. In-Context Case Retrieval (Matching `sample_requests.csv`)

Node 2 matches incoming requests against the 25 solved reference cases in `sample_requests.csv`:
- **Matching Heuristic**: Compare `request_type`, affordability ratio ($\frac{\text{requested}}{\text{available}}$), and permission flags (`allows_partial_payment`, `max_installment_months`).
- **Pattern Learning**: Use matched sample outputs to structure explanation phrasing and confirm recommendation styles.

---

## 3. Official 6-Tier Tie-Breaking Ranking Hierarchy

When Node 5 identifies multiple safe candidate scenarios (`is_safe == true`), Node 6 ranks them strictly in this order:

1. **Completion Deadline**: Must complete full request on or before `desired_completion_date`.
2. **Zero Spending Changes**: Options requiring NO spending changes (`spending_changes_needed = none`) rank higher than options requiring changes.
3. **Minimize Total Amount Paid**: Lower total payable amount ranks higher (e.g. zero financing fee over fee-bearing options).
4. **Start Date**: Earlier payment start date ranks higher.
5. **Payment Count**: Fewer total payments rank higher.
6. **Tie-Breaker**: Option with the lowest `payment_option_id` wins.

---

## 4. Fallback Selection Protocols

- **Tier 1 (Normal Selection)**: Select highest-ranked safe option from 6-tier hierarchy.
- **Tier 2 ("Wait" Fallback)**: If no immediate or installment plan is safe, check if `earliest_date_for_full_payment` exists and is $\le$ `desired_completion_date`.
  - Recommendation: `affordability_status = affordable_later`, `method = wait`, `payment_plan = <earliest_date>:<requested_amount>`.
- **Tier 3 ("Not Recommended" Fallback)**: If full payment cannot be safely completed within 90 days or before completion date:
  - Recommendation: `affordability_status = not_affordable`, `method = not_recommended`, `payment_plan = none`, `earliest_date_for_full_payment = ""`.

---

## 5. Grounded Explanation Templates

- **`affordable_now`**:
  `Pay [Currency] [Amount] today. This leaves at least [Currency] [Min_Available] available over the next 90 days.`
- **`affordable_with_plan` (installments)**:
  `Use [N] installments of [Currency] [Amount], starting [Date]. This leaves at least [Currency] [Min_Available] available.`
- **`affordable_with_plan` (partial)**:
  `Pay [Currency] [Safe_Today] today and the remaining [Currency] [Remainder] on [Earliest_Date]. This completes the full request and keeps the [Currency] [Min_Balance] minimum protected.`
- **`affordable_with_plan` (spending change)**:
  `Stop [Category], then pay [Currency] [Amount] today. This leaves at least [Currency] [Min_Available] available.`
- **`affordable_later` (wait)**:
  `Pay [Currency] [Amount] in full on [Earliest_Date]. Paying earlier would take the balance below the [Currency] [Min_Balance] minimum.`
- **`not_affordable`**:
  `Do not make this payment by [Completion_Date]. None of the available options keeps the [Currency] [Min_Balance] minimum protected.`
