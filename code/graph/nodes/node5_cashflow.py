from typing import Dict, Any, List
from graph.state import AgentState
from graph.tools.cashflow_tool import DeterministicCashflowTool

def node5_cashflow_evaluator(state: AgentState) -> Dict[str, Any]:
    """
    Node 5: Financial Cashflow Evaluator.
    Runs deterministic 90-day daily balance simulation in Python enforcing
    Skill 2's Unbreachable Minimum Balance Safety Rule across all candidate scenarios.
    """
    evidence = state["evidence_pack"]
    req_data = state["request_data"]
    candidates = state.get("candidate_scenarios", [])

    request_date = state["request_date"]
    requested_amount = float(req_data.get("requested_amount", 0.0))
    desired_completion = req_data.get("desired_completion_date", request_date)
    allows_partial = req_data.get("allows_partial_payment", "").lower() in ("true", "1", "yes")

    start_balance = evidence["current_available_balance"]
    min_balance = evidence["minimum_balance_to_keep"]
    events = evidence["normalized_events"]
    considered_methods = evidence["payment_methods_user_will_consider"]

    tool = DeterministicCashflowTool()

    # 1. Compute amount_safe_to_pay today before spending changes
    amount_safe_today = tool.compute_amount_safe_to_pay(
        start_balance=start_balance,
        min_balance=min_balance,
        events=events,
        request_date_str=request_date,
        requested_amount=requested_amount
    )

    # 2. Compute earliest_date_for_full_payment
    earliest_full_date, earliest_min_bal = tool.find_earliest_full_payment_date(
        start_balance=start_balance,
        min_balance=min_balance,
        events=events,
        request_date_str=request_date,
        requested_amount=requested_amount
    )

    evaluated_scenarios: List[Dict[str, Any]] = []

    # 3. Evaluate each synthesized candidate scenario
    for cand in candidates:
        sim_res = tool.simulate_90_days(
            start_balance=start_balance,
            min_balance=min_balance,
            events=events,
            scenario_payments=cand["payments"],
            request_date_str=request_date,
            spending_changes=cand.get("spending_changes")
        )

        cand_eval = dict(cand)
        cand_eval["is_safe"] = sim_res["is_safe"]
        cand_eval["min_projected_balance"] = sim_res["min_projected_balance"]
        cand_eval["violation_date"] = sim_res["violation_date"]
        evaluated_scenarios.append(cand_eval)

    # 4. Check Partial Payment Candidate (If allowed & safe_today > 0)
    if allows_partial and ("partial_payment" in considered_methods or not considered_methods):
        if 0.0 < amount_safe_today < requested_amount and earliest_full_date and earliest_full_date <= desired_completion:
            remainder = requested_amount - amount_safe_today
            partial_payments = [(request_date, amount_safe_today), (earliest_full_date, remainder)]

            partial_sim = tool.simulate_90_days(
                start_balance=start_balance,
                min_balance=min_balance,
                events=events,
                scenario_payments=partial_payments,
                request_date_str=request_date
            )

            evaluated_scenarios.append({
                "scenario_id": "partial_payment_schedule",
                "recommended_payment_method": "partial_payment",
                "payments": partial_payments,
                "spending_changes": [],
                "payment_option_id": None,
                "total_cost": requested_amount,
                "is_safe": partial_sim["is_safe"],
                "min_projected_balance": partial_sim["min_projected_balance"],
                "violation_date": partial_sim["violation_date"]
            })

    # 5. Check Wait Candidate — always add if earliest_full_date found (selector handles deadline ranking)
    if earliest_full_date:
        wait_payments = [(earliest_full_date, requested_amount)]
        wait_sim = tool.simulate_90_days(
            start_balance=start_balance,
            min_balance=min_balance,
            events=events,
            scenario_payments=wait_payments,
            request_date_str=request_date
        )

        evaluated_scenarios.append({
            "scenario_id": "wait_full_payment",
            "recommended_payment_method": "wait",
            "payments": wait_payments,
            "spending_changes": [],
            "payment_option_id": None,
            "total_cost": requested_amount,
            "is_safe": wait_sim["is_safe"],
            "min_projected_balance": wait_sim["min_projected_balance"],
            "violation_date": wait_sim["violation_date"]
        })

    evidence["amount_safe_to_pay"] = amount_safe_today
    evidence["earliest_date_for_full_payment"] = earliest_full_date or ""

    return {
        "evaluated_scenarios": evaluated_scenarios,
        "evidence_pack": evidence
    }
