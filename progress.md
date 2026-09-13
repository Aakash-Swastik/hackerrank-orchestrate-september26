# Progress Tracker: Buy or Wait? AI Financial Agent

## Development Timeline & Status

- **Phase 1**: Node 1 Engine & Foundation (Data Ingestion, OCR, Messages, Calculator, Cache) `[x] Completed`
- **Phase 2**: Core Financial Engine & Scenario Solver (Nodes 2, 3, 4, 4.5, 5) `[x] Completed`
- **Phase 3**: Selector, Guardrail Validator, Golden Benchmark & Full Output Generation (Nodes 6, 7, Main Entrypoint) `[x] Completed`

---

## Phase Breakdown & Checklist

### Phase 1: Node 1 Engine & Foundation
- [x] **1.1 Data Loaders (`code/graph/tools/io_csv.py`)**: Implemented robust CSV parsers for all 9 dataset files with type safety and schema validation.
- [x] **1.2 Bedrock Client (`code/graph/tools/bedrock_client.py`)**: Built AWS Bedrock API client using `AWS_BEARER_TOKEN_BEDROCK`, single bearer token, SSL verify flag, and token usage counter.
- [x] **1.3 Persistent Caching (`code/cache/`)**: Implemented disk caching for OCR (`code/cache/ocr/`) and message extractions (`code/cache/messages/`).
- [x] **1.4 OCR Agent (`code/graph/tools/ocr_tool.py`)**: Built multimodal OCR prompt & tool with candidate extraction and selection logic for all 16 PNG images.
- [x] **1.5 Message Fact Extractor (`code/graph/tools/message_tool.py`)**: Implemented LLM message parser with strict `sent_at <= request_date` date cutoffs.
- [x] **1.6 Node 1 Calculator (`code/graph/tools/calculator_tool.py`)**: Python engine to reconcile past CSVs with extracted facts and produce `updated_record`.
- [x] **1.7 Phase 1 Verification**: Tested Node 1 pipeline across sample users and verified `updated_record` JSON outputs.

### Phase 2: Core Financial Engine & Scenario Solver
- [x] **2.1 Similar Case Retriever (`code/graph/nodes/node2_case_retriever.py` - Node 2)**: Implemented pattern matcher against `dataset/sample_requests.csv` using heuristics from `skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md`.
- [x] **2.2 Evidence Gathering & Native FX (`code/graph/nodes/node3_evidence.py` - Node 3)**: Compiled profile constraints, priorities, and direct `exchange_rates.csv` conversions to user `home_currency`.
- [x] **2.3 Scenario Summarizer (`code/graph/nodes/node4_summarizer.py` - Node 4)**: Generated candidate payment plans (Full, Installments, Partial, Wait, Spending Reductions).
- [x] **2.4 Deterministic Cashflow Simulator (`code/graph/tools/cashflow_tool.py` - Node 5)**: 90-day daily balance simulation, recurrence projection engine, `amount_safe_to_pay` calculation, and `earliest_date_for_full_payment` finder enforcing unbreachable minimum balance safety rule.
- [x] **2.5 Phase 2 Verification**: Unit tested Node 5 cashflow simulator against complex edge cases (future debit traps, salary rises, recurring schedules).

### Phase 3: Selector, Guardrail Validator & Full Pipeline
- [x] **3.1 Selector & Tie-Breaker (`code/graph/nodes/node6_selector.py` - Node 6)**: Implemented strict 6-level tie-breaking hierarchy and decision explanation builder.
- [x] **3.2 Guardrail Validator (`code/graph/nodes/node7_validator.py` - Node 7)**: Deterministic bounds checking, sum checks, date consistency, and output schema validation.
- [x] **3.3 Golden Benchmark (`code/evaluation/main.py`)**: Ran end-to-end evaluation against `sample_requests.csv` and measured 7-column accuracy.
- [x] **3.4 Main Entrypoint (`code/main.py`)**: Top-level CLI script processing all 250 rows in `dataset/requests.csv` and generating root `output.csv`.
- [x] **3.5 Usage Report (`code/evaluation/usage_report.md`)**: Generated token counts, API call counts, and estimated cost report.
- [x] **3.6 Phase 3 Verification**: Confirmed `output.csv` exists in repo root, contains 250 prediction rows + header, and satisfies all challenge rules.
