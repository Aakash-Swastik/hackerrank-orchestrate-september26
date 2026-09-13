from datetime import datetime, timedelta
from typing import Dict, Any, List
from graph.state import AgentState

class ScenarioSynthesizer:
    """
    Node 4: Candidate Scenario Synthesizer.
    Generates the complete search space of candidate scenarios (Full Payment, Installments, Partial Payment, Wait, Spending Changes).
    """

    def parse_date(self, d_str: str) -> datetime:
        return datetime.strptime(d_str.split("T")[0], "%Y-%m-%d")

    def format_date(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")

    def synthesize(self, state: AgentState) -> List[Dict[str, Any]]:
        req_data = state["request_data"]
        evidence = state["evidence_pack"]

        req_id = state["request_id"]
        request_date = state["request_date"]
        requested_amount = float(req_data.get("requested_amount", 0.0))
        desired_completion = req_data.get("desired_completion_date", request_date)
        allows_partial = req_data.get("allows_partial_payment", "").lower() in ("true", "1", "yes")

        considered_methods = evidence.get("payment_methods_user_will_consider", [])
        eligible_options = evidence.get("eligible_payment_options", [])
        stoppable_categories = evidence.get("expense_categories_user_is_willing_to_stop", [])
        reducible_categories = evidence.get("expense_categories_user_is_willing_to_reduce", [])
        normalized_events = evidence.get("normalized_events", [])

        scenarios: List[Dict[str, Any]] = []

        # Candidate 1: Full Payment Today
        if "full_payment" in considered_methods or not considered_methods:
            scenarios.append({
                "scenario_id": "full_payment_today",
                "recommended_payment_method": "full_payment",
                "payments": [(request_date, requested_amount)],
                "spending_changes": [],
                "payment_option_id": None,
                "total_cost": requested_amount
            })

        # Candidate 2+: Provider Installment Offers
        for opt in eligible_options:
            if opt.get("payment_method") == "installments":
                opt_id = opt["payment_option_id"]
                amt_per = opt["payment_amount"]
                num_p = opt["number_of_payments"]
                first_d_str = opt["first_payment_date"]
                freq_days = opt["payment_frequency_days"]
                total_cost = opt["total_payable_amount"]

                # Build installment dates schedule
                inst_payments = []
                first_dt = self.parse_date(first_d_str)
                for i in range(num_p):
                    p_dt = first_dt + timedelta(days=i * freq_days)
                    inst_payments.append((self.format_date(p_dt), amt_per))

                scenarios.append({
                    "scenario_id": f"installment_{opt_id}",
                    "recommended_payment_method": "installments",
                    "payments": inst_payments,
                    "spending_changes": [],
                    "payment_option_id": opt_id,
                    "total_cost": total_cost
                })

        # Candidate 3+: Spending Changes Permutations
        spending_permutations = []
        # Find eligible stoppable events
        for ev in normalized_events:
            ev_cat = ev.get("category")
            ev_id = ev.get("event_id")
            flex = ev.get("flexibility")
            if ev_cat in stoppable_categories and flex in ("stoppable", "flexible"):
                spending_permutations.append([{
                    "event_id": ev_id,
                    "category": ev_cat,
                    "action": "stop",
                    "new_amount": 0.0
                }])

            if ev_cat in reducible_categories and flex in ("flexible", "reducible"):
                min_allowed = ev.get("minimum_allowed_amount", 0.0) or 0.0
                curr_amt = ev.get("amount", 0.0) or 0.0
                if curr_amt > min_allowed:
                    spending_permutations.append([{
                        "event_id": ev_id,
                        "category": ev_cat,
                        "action": "reduce_to",
                        "new_amount": min_allowed
                    }])

        for sp in spending_permutations[:3]:  # Max 3 permutations
            scenarios.append({
                "scenario_id": f"full_payment_with_spending_change_{sp[0]['event_id']}",
                "recommended_payment_method": "full_payment",
                "payments": [(request_date, requested_amount)],
                "spending_changes": sp,
                "payment_option_id": None,
                "total_cost": requested_amount
            })

        return scenarios

def node4_synthesize_scenarios(state: AgentState) -> Dict[str, Any]:
    synthesizer = ScenarioSynthesizer()
    scenarios = synthesizer.synthesize(state)
    return {
        "candidate_scenarios": scenarios
    }
