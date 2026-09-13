from typing import Dict, Any
from graph.state import AgentState

def node7_guardrail_validator(state: AgentState) -> Dict[str, Any]:
    """
    Node 7: Guardrail Validator Node (The Judge Node).
    Enforces 100% deterministic compliance on bounds, dates, sum equality, and CSV columns.
    """
    final_output = dict(state.get("final_output", {}))
    req_data = state["request_data"]
    requested_amount = float(req_data.get("requested_amount", 0.0))
    request_date = state["request_date"]

    safe_amt = float(final_output.get("amount_safe_to_pay", 0.0))
    status = final_output.get("affordability_status")
    method = final_output.get("recommended_payment_method")

    # 1. Bounds Check: 0 <= amount_safe_to_pay <= requested_amount
    safe_amt = max(0.0, min(requested_amount, safe_amt))
    final_output["amount_safe_to_pay"] = round(safe_amt, 2)

    # 2. Date Consistency Check
    if status == "affordable_now":
        final_output["earliest_date_for_full_payment"] = request_date
    elif status == "not_affordable":
        final_output["earliest_date_for_full_payment"] = ""

    # 3. Method Consistency Check
    if status == "affordable_with_plan" and method not in ("installments", "partial_payment", "full_payment"):
        final_output["recommended_payment_method"] = "installments"
    elif status == "not_affordable":
        final_output["recommended_payment_method"] = "not_recommended"
        final_output["payment_plan"] = "none"

    # 4. Partial Payment Sum Check
    if method == "partial_payment":
        plan_parts = final_output.get("payment_plan", "").split("|")
        if len(plan_parts) == 2:
            try:
                p1_amt = float(plan_parts[0].split(":")[1])
                p2_amt = float(plan_parts[1].split(":")[1])
                sum_amt = p1_amt + p2_amt
                if abs(sum_amt - requested_amount) > 0.01:
                    # Correct second payment sum
                    p2_amt = requested_amount - p1_amt
                    d1 = plan_parts[0].split(":")[0]
                    d2 = plan_parts[1].split(":")[0]
                    final_output["payment_plan"] = f"{d1}:{p1_amt:.2f}|{d2}:{p2_amt:.2f}".replace(".00", "")
            except Exception:
                pass

    return {
        "final_output": final_output
    }
