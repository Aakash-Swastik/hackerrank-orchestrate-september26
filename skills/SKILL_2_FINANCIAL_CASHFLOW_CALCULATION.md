# Skill 2: Deterministic Financial Cashflow & Safety Simulation

## 1. Primary End Goal & Core Safety Constraint

> **THE UNBREACHABLE RULE**:
> Under **NO scenario** or recommendation can the user's projected daily available balance drop below their `minimum_balance_to_keep` on **ANY day** during the 90-day forecast period (`request_date` to `request_date + 90`).
>
> $$\forall t \in [\text{request\_date}, \text{request\_date} + 90], \quad \text{balance}(t) \ge \text{minimum\_balance\_to\_keep}$$

Any candidate scenario that violates this condition on even a single day is **strictly certified unsafe (`is_safe = false`)** and rejected.

---

## 2. Timeline & Information Cutoff Rules (Dual-Clock Engine)

To prevent information leakage and ensure compliance with contest rules:

1. **Information Horizon (`learned_at`)**:
   - `learned_at` is the date a message was sent (`messages.sent_at`) or an image was dated.
   - **If `learned_at > request_date`**: **STRICTLY DROP.** The information was not known on `request_date`.
2. **Effective Horizon (`effective_date`)**:
   - `effective_date` is when a financial change takes effect.
   - **If `effective_date > request_date` (with `learned_at <= request_date`)**: Today's available cash balance uses the earlier value. The forward 90-day simulation applies the new value starting on `effective_date`.

---

## 3. Cashflow Accounting Rules

- **Past Transactions (`settlement_date < request_date`)**: Already settled in `current_available_balance`. **Do NOT add or subtract again.**
- **Pending Debits**: Reserve immediately (deduct from starting balance).
- **Pending Credits / Bonuses / Commissions / Refunds / Lottery**: **DO NOT COUNT as cash** until settled before `request_date`.
- **Confirmed Future Income**: Count salary only on its explicit settlement date.
- **Native Currency Base**: All daily balance simulations for a user run natively in `user.home_currency`. Foreign currency items are converted directly to `home_currency` on their settlement date using `exchange_rates.csv`.

---

## 4. Exact Mathematical Formulas (Python Engine)

### A. Daily Balance Simulator
For each day $t \in [0, 90]$:
$$\text{balance}(t) = \text{current\_available\_balance} - \text{pending\_debits} + \sum_{d \le t} \text{confirmed\_incomes}(d) - \sum_{d \le t} \text{essential\_expenses}(d) - \sum_{d \le t} \text{scenario\_payments}(d)$$

### B. Baseline Safe Margin & `amount_safe_to_pay` Today
1. Run baseline simulation (zero request payments, zero optional spending changes).
2. Calculate baseline minimum margin:
   $$\text{safe\_margin} = \min_{t \in [0, 90]} \big(\text{balance}_{\text{baseline}}(t) - \text{minimum\_balance\_to\_keep}\big)$$
3. Calculate maximum safe payment today:
   $$\text{amount\_safe\_to\_pay} = \max\big(0.0, \min(\text{requested\_amount}, \text{safe\_margin})\big)$$

### C. `earliest_date_for_full_payment` Search Algorithm
1. Loop over target payment dates $D$ from `request_date` to `request_date + 90`:
2. Simulate paying full `requested_amount` as a single payment on date $D$.
3. If $\min_{t \in [0, 90]} \text{balance}(t) \ge \text{minimum\_balance\_to\_keep}$, then $D$ is safe!
4. `earliest_date_for_full_payment` is the **first such date $D$**. If no date in 90 days passes, set to empty string `""`.
