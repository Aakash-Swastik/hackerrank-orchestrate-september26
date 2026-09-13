# Complete LangGraph Agent Architecture: Buy or Wait?

This document defines the complete **LangGraph StateGraph** architecture, state schema, node transitions, tool ecosystem, prompt templates, modular skills directory (`skills/`), and folder layout for the **Buy or Wait?** AI financial agent.

---

## 1. LangGraph Architecture & Workflow Diagram

```text
                  ┌─────────────────────────────────────────┐
                  │              START NODE                 │
                  │       (Ingests dataset/requests.csv)    │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       NODE 1: Reconcile Records         │
                  │   (OCR Tool, Message Tool, Calculator)  │
                  └────────────────────┬────────────────────┘
                                       │
                  ┌────────────────────┴────────────────────┐
                  │                                         │
                  ▼                                         ▼
   ┌─────────────────────────────┐           ┌─────────────────────────────┐
   │    NODE 2: Case Retriever   │           │  NODE 3: Evidence Gatherer  │
   │  (Matches sample_requests)  │           │   (Profiles, Native FX)     │
   └──────────────┬──────────────┘           └──────────────┬──────────────┘
                  │                                         │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      NODE 4: Scenario Summarizer        │
                  │    (Synthesizes Candidate Plans)        │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    NODE 5: Cashflow Evaluator           │
                  │  (Deterministic 90-Day Math Engine)     │
                  │   *Enforces Unbreachable Min Balance*   │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      NODE 6: Selector & Ranker          │
                  │   (Strict Tie-Breaking Hierarchy)       │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │    NODE 7: Guardrail Validator          │
                  │     (Output Bounds & Sum Checks)        │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │              END NODE                   │
                  │      (Writes root-level output.csv)     │
                  └─────────────────────────────────────────┘
```

---

## 2. Core Unbreachable Safety Rule & End Goal

> **END GOAL & UNBREACHABLE RULE**:
> The agent's primary directive is to maximize affordable user purchases **WITHOUT EVER ALLOWING** the projected daily available balance to dip below `minimum_balance_to_keep` on ANY day during the 90-day forecast (`request_date` to `request_date + 90`).
>
> $$\forall t \in [\text{request\_date}, \text{request\_date} + 90], \quad \text{balance}(t) \ge \text{minimum\_balance\_to\_keep}$$

---

## 3. Skills Directory Layout (`skills/`)

- **[skills.md](skills.md)**: Master Index of agent skills and domain references.
- **[skills/SKILL_1_OCR_EXTRACTION.md](skills/SKILL_1_OCR_EXTRACTION.md)**: Multimodal OCR document classification, context injection, candidate extraction, and JSON storage schema.
- **[skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md](skills/SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md)**: Dual-clock rules, 90-day daily balance simulation, `amount_safe_to_pay` math, and unbreachable minimum balance safety constraint.
- **[skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md](skills/SKILL_3_SCENARIO_SELECTION_AND_RANKING.md)**: Scenario synthesis, sample pattern matching, official 6-tier tie-breaker hierarchy, 3-tier fallback selection, and explanation templates.

---

## 4. LangGraph State Schema (`AgentState`)

```python
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    # Request Inputs
    request_id: str
    request_data: Dict[str, Any]
    user_id: str
    request_date: str
    
    # Node 1 Outputs
    past_record: Dict[str, Any]
    updated_record: Dict[str, Any]
    change_list: List[Dict[str, Any]]
    
    # Node 2 & 3 Outputs
    similar_cases: List[Dict[str, Any]]
    evidence_pack: Dict[str, Any]
    
    # Node 4, 5, 6, 7 Outputs
    candidate_scenarios: List[Dict[str, Any]]
    evaluated_scenarios: List[Dict[str, Any]]
    winning_scenario: Optional[Dict[str, Any]]
    final_output: Dict[str, Any]
    
    # Audit & Error Handling
    audit_log: Dict[str, Any]
    error_state: Optional[str]
```

---

## 5. LangGraph Code Base Layout

```text
hackerrank-orchestrate-september26/
├── AGENTS.md                         # Contest agent guidelines
├── problem_statement.md              # Full problem spec
├── README.md                         # Project overview
├── plan.md                           # LangGraph architecture design
├── implementation.md                 # 3-phase build plan
├── progress.md                       # Phase completion checklist tracker
├── skills.md                         # Master skills index
├── skills/
│   ├── SKILL_1_OCR_EXTRACTION.md
│   ├── SKILL_2_FINANCIAL_CASHFLOW_CALCULATION.md
│   └── SKILL_3_SCENARIO_SELECTION_AND_RANKING.md
├── log.txt                           # Submission transcript log
├── output.csv                        # Final predictions output
├── code/
│   ├── main.py                       # LangGraph execution entrypoint CLI
│   ├── graph/
│   │   ├── state.py                  # AgentState TypedDict
│   │   ├── workflow.py               # StateGraph builder, nodes & edges
│   │   ├── nodes/
│   │   │   ├── node1_reconciliation.py
│   │   │   ├── node2_case_retriever.py
│   │   │   ├── node3_evidence.py
│   │   │   ├── node4_summarizer.py
│   │   │   ├── node5_cashflow.py
│   │   │   ├── node6_selector.py
│   │   │   └── node7_validator.py
│   │   ├── tools/
│   │   │   ├── bedrock_client.py
│   │   │   ├── ocr_tool.py
│   │   │   ├── message_tool.py
│   │   │   ├── calculator_tool.py
│   │   │   ├── fx_tool.py
│   │   │   └── cashflow_tool.py
│   │   └── prompts/
│   │       ├── ocr_prompt.py
│   │       ├── message_prompt.py
│   │       ├── summarizer_prompt.py
│   │       └── explanation_prompt.py
│   └── evaluation/
│       ├── main.py
│       └── usage_report.md
└── dataset/
```
