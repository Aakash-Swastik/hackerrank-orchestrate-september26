# Financial Agent Skills Directory & Reference Index (`skills/`)

This directory contains the operational skills, domain knowledge, and exact mathematical/heuristic guidelines for the **Buy or Wait?** LangGraph financial decision agent.

---

## Skill Guides Index

1. **[Skill 1: Multimodal OCR Document Extraction & Target Selection](skills/SKILL_1_OCR_EXTRACTION.md)**
   - Document classification (payslips, rent receipts, bills, invoices, handwritten receipts).
   - Candidate amount extraction & matching rules for all document types.
   - Context injection structure & exact JSON cache storage schema.

2. **[Skill 2: Deterministic Financial Cashflow & Safety Simulation](skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md)**
   - **THE UNBREACHABLE RULE**: Under NO scenario can the daily available balance fall below `minimum_balance_to_keep` during the 90-day forecast.
   - Dual-clock timeline rules (`learned_at` vs `effective_date`).
   - Baseline 90-day daily balance simulation formula, `amount_safe_to_pay` math, and `earliest_date_for_full_payment` search algorithm.
   - Native `home_currency` base and direct exchange rate conversion rules.

3. **[Skill 3: Scenario Synthesis, Ranking & Fallback Selection](skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md)**
   - Scenario synthesis (Full Payment, Provider Installments, Partial Payment, Wait, Flexible Spending Reductions).
   - In-context pattern matching against `dataset/sample_requests.csv`.
   - Official 6-tier tie-breaking hierarchy (Deadline, Zero Spending Changes, Lowest Cost, Earlier Start, Fewer Payments, Lowest Option ID).
   - 3-tier fallback protocols (Normal Selection $\to$ Wait Fallback $\to$ Safe Not Recommended Fallback).
   - Grounded explanation templates matching `sample_requests.csv` ground truth.
