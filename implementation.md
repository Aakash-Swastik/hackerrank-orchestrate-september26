# LangGraph Implementation Plan & 3-Phase Roadmap: Buy or Wait?

This document outlines the 3-phase technical implementation plan for building the **Buy or Wait?** AI financial decision agent using **LangGraph** and modular skill references (`skills/`).

---

## 1. Modular Skills Reference Layout (`skills/`)

- **[skills.md](skills.md)**: Master Skills Index.
- **[skills/SKILL_1_OCR_EXTRACTION.md](skills/SKILL_1_OCR_EXTRACTION.md)**: OCR classification, candidate extraction, and JSON storage schema.
- **[skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md](skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md)**: Unbreachable minimum balance safety rule, dual-clock timeline, and 90-day cashflow simulation math.
- **[skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md](skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md)**: Candidate synthesis, sample pattern matching, 6-tier tie-breaking hierarchy, and 3-tier fallback protocols.

---

## 2. Workspace & Code Layout

```text
hackerrank-orchestrate-september26/
├── AGENTS.md
├── problem_statement.md
├── README.md
├── plan.md                           # LangGraph architecture reference
├── implementation.md                 # 3-phase build roadmap
├── progress.md                       # Phase checklist tracker
├── skills.md                         # Master skills index
├── skills/
│   ├── SKILL_1_OCR_EXTRACTION.md
│   ├── SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md
│   └── SKILL_3_SCENARIO_SELECTION_AND_RANKING.md
├── log.txt                           # Submission transcript log
├── output.csv                        # Final generated predictions
├── code/
│   ├── main.py                       # LangGraph execution entrypoint CLI
│   ├── graph/
│   │   ├── state.py                  # AgentState TypedDict
│   │   ├── workflow.py               # StateGraph builder, nodes & edges
│   │   ├── nodes/
│   │   │   ├── node1_reconciliation.py # Node 1: Fact Reconciliation
│   │   │   ├── node2_case_retriever.py # Node 2: Pattern Matcher (using skills/)
│   │   │   ├── node3_evidence.py       # Node 3: Profiles & Native FX
│   │   │   ├── node4_summarizer.py     # Node 4: Candidate Synthesizer
│   │   │   ├── node5_cashflow.py       # Node 5: 90-Day Cashflow Math
│   │   │   ├── node6_selector.py       # Node 6: Tie-Breaker Ranker & Explanation
│   │   │   └── node7_validator.py      # Node 7: Guardrail Validator
│   │   ├── tools/
│   │   │   ├── bedrock_client.py     # AWS Bedrock API client
│   │   │   ├── ocr_tool.py           # Multimodal OCR tool
│   │   │   ├── message_tool.py       # Message fact extractor
│   │   │   ├── calculator_tool.py    # Node 1 calculator tool
│   │   │   ├── fx_tool.py            # Direct FX converter
│   │   │   └── cashflow_tool.py      # Deterministic 90-day cashflow simulator
│   │   └── prompts/
│   │       ├── ocr_prompt.py         # OCR system prompt & schema
│   │       ├── message_prompt.py     # Message extraction prompt
│   │       ├── summarizer_prompt.py  # Scenario synthesis prompt
│   │       └── explanation_prompt.py # Decision explanation prompt
│   └── evaluation/
│       ├── main.py                   # Golden benchmark test runner
│       └── usage_report.md           # Token usage and cost report
└── dataset/                          # Challenge dataset files
```

---

## 3. 3-Phase Development Roadmap

### Phase 1: Node 1 Engine & Foundation
- **State Schema (`code/graph/state.py`)**: Define `AgentState` TypedDict.
- **CSV Loaders (`code/graph/tools/io_csv.py`)**: Load and index dataset files.
- **Bedrock API Client (`code/graph/tools/bedrock_client.py`)**: Converse API wrapper using `AWS_BEARER_TOKEN_BEDROCK`.
- **Multimodal OCR Tool (`code/graph/tools/ocr_tool.py` & `skills/SKILL_1_OCR_EXTRACTION.md`)**: Image extraction with JSON schema validation.
- **Message Tool (`code/graph/tools/message_tool.py`)**: Message fact extraction with `sent_at <= request_date` cutoff.
- **Node 1 Reconciliation Node (`code/graph/nodes/node1_reconciliation.py`)**: Run reconciliation and produce `updated_record`.

### Phase 2: Core LangGraph Nodes (Nodes 2, 3, 4, 5)
- **Node 2 Case Retriever (`code/graph/nodes/node2_case_retriever.py`)**: Pattern matcher using `skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md`.
- **Node 3 Evidence & Native FX (`code/graph/nodes/node3_evidence.py`)**: Profile constraints and native currency conversions.
- **Node 4 Scenario Summarizer (`code/graph/nodes/node4_summarizer.py`)**: Synthesize candidate scenarios.
- **Node 5 Cashflow Evaluator (`code/graph/nodes/node5_cashflow.py` & `skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md`)**: Deterministic 90-day daily balance simulation in Python enforcing the unbreachable minimum balance rule.

### Phase 3: Selector, Validator, Workflow Graph & Output
- **Node 6 Selector & Ranker (`code/graph/nodes/node6_selector.py`)**: 6-level tie-breaker hierarchy and decision explanation builder.
- **Node 7 Guardrail Validator (`code/graph/nodes/node7_validator.py`)**: Output schema, bounds, and sum equality checks.
- **LangGraph Workflow Builder (`code/graph/workflow.py`)**: Connect nodes, conditional edges, and compile `StateGraph`.
- **Main CLI Entrypoint (`code/main.py`)**: Run pipeline on `dataset/requests.csv` and write root `output.csv`.
- **Evaluation & Usage Report (`code/evaluation/`)**: Run golden benchmark on `sample_requests.csv` and generate token report.
