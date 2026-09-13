from typing import Dict, Any, List
from graph.state import AgentState
from graph.tools.io_csv import DataLoader

def node2_retrieve_similar_cases(state: AgentState, data_loader: DataLoader) -> Dict[str, Any]:
    """
    Node 2: In-Context Pattern Matcher.
    Compares the incoming request against sample_requests.csv using Skill 3 heuristics
    (request_type match, affordability ratio, payment permissions).
    """
    req_type = state["request_data"].get("request_type")
    req_amt = float(state["request_data"].get("requested_amount", 0.0))
    allows_partial = state["request_data"].get("allows_partial_payment", "").lower() in ("true", "1", "yes")

    updated_rec = state.get("updated_record", {})
    available_bal = updated_rec.get("profile", {}).get("current_available_balance", 1.0)
    if available_bal <= 0:
        available_bal = 1.0

    affordability_ratio = req_amt / available_bal

    scored_cases: List[tuple] = []
    for sample in data_loader.sample_requests:
        score = 0.0
        # Category match
        if sample.get("request_type") == req_type:
            score += 10.0

        # Partial payment flag match
        sample_partial = sample.get("allows_partial_payment", "").lower() in ("true", "1", "yes")
        if sample_partial == allows_partial:
            score += 3.0

        # Affordability ratio similarity
        sample_amt = float(sample.get("requested_amount", 0.0))
        sample_ratio = sample_amt / max(1.0, float(sample.get("amount_safe_to_pay", 1.0)))
        diff = abs(affordability_ratio - sample_ratio)
        score += max(0.0, 5.0 - diff)

        scored_cases.append((score, sample))

    scored_cases.sort(key=lambda x: x[0], reverse=True)
    top_matches = [case for score, case in scored_cases[:2]]

    return {
        "similar_cases": top_matches
    }
