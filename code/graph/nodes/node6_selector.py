from typing import Dict, Any, List, Optional
from graph.state import AgentState

class ScenarioSelectorRanker:
    """
    Node 6 Selector & Ranker Node.
    Ranks safe scenarios strictly according to Skill 3's 6-tier tie-breaking hierarchy:
    1. Completion Deadline
    2. Zero Spending Changes
    3. Minimize Total Amount Paid
    4. Start Payment Earlier
    5. Use Fewer Payments
    6. Lowest payment_option_id
    """

    def rank_and_select(self, state: AgentState) -> Dict[str, Any]:
        evaluated = state.get("evaluated_scenarios", [])
        evidence = state["evidence_pack"]
        req_data = state["request_data"]

        req_id = state["request_id"]
        request_date = state["request_date"]
        requested_amount = float(req_data.get("requested_amount", 0.0))
        desired_completion = req_data.get("desired_completion_date", request_date)

        currency = evidence.get("home_currency", "USD")
        min_balance = evidence.get("minimum_balance_to_keep", 0.0)
        safe_today = evidence.get("amount_safe_to_pay", 0.0)
        earliest_full_date = evidence.get("earliest_date_for_full_payment", "")

        # Filter safe scenarios
        safe_scenarios = [s for s in evaluated if s.get("is_safe")]

        if not safe_scenarios:
            # Fallback: if a wait date exists, use wait fallback
            if earliest_full_date:
                return self._format_wait_output(
                    req_id=req_id,
                    currency=currency,
                    amount=requested_amount,
                    earliest_date=earliest_full_date,
                    safe_today=safe_today,
                    min_balance=min_balance
                )
            else:
                # Not Affordable Fallback
                return self._format_not_affordable_output(
                    req_id=req_id,
                    currency=currency,
                    amount=requested_amount,
                    desired_completion=desired_completion,
                    safe_today=safe_today,
                    min_balance=min_balance
                )

        # Sort by 6-tier hierarchy
        def sort_key(s):
            # 1. Complete on or before desired_completion
            last_payment_date = max([p[0] for p in s["payments"]]) if s.get("payments") else request_date
            meets_deadline = 0 if last_payment_date <= desired_completion else 1

            # 2. Require no spending changes
            spending_changes_count = len(s.get("spending_changes", []))

            # 3. Minimize total cost
            total_cost = s.get("total_cost", requested_amount)

            # 4. Start earlier
            first_payment_date = min([p[0] for p in s["payments"]]) if s.get("payments") else request_date

            # 5. Fewer payments
            num_payments = len(s.get("payments", []))

            # 6. Lowest payment_option_id
            opt_id_str = s.get("payment_option_id") or "z_999"

            return (meets_deadline, spending_changes_count, total_cost, first_payment_date, num_payments, opt_id_str)

        safe_scenarios.sort(key=sort_key)
        winner = safe_scenarios[0]

        # Format output fields for winning scenario
        return self._format_winning_output(
            winner=winner,
            req_id=req_id,
            currency=currency,
            amount=requested_amount,
            request_date=request_date,
            desired_completion=desired_completion,
            safe_today=safe_today,
            earliest_full_date=earliest_full_date,
            min_balance=min_balance
        )

    def _format_winning_output(self, winner, req_id, currency, amount, request_date, desired_completion, safe_today, earliest_full_date, min_balance) -> Dict[str, Any]:
        method = winner.get("recommended_payment_method")
        payments = winner.get("payments", [])
        spending_changes = winner.get("spending_changes", [])

        # Build payment_plan string
        plan_str = "none"
        if payments:
            plan_str = "|".join([f"{p[0]}:{p[1]:.2f}".rstrip("0").rstrip(".") for p in payments])

        # Build spending_changes_needed string
        changes_str = "none"
        if spending_changes:
            ch_parts = []
            for sc in spending_changes:
                ev_id = sc["event_id"]
                act = sc["action"]
                if act == "stop":
                    ch_parts.append(f"stop:{ev_id}")
                elif act == "reduce_to":
                    new_a = sc["new_amount"]
                    ch_parts.append(f"reduce_to:{ev_id}:{new_a:.2f}".rstrip("0").rstrip("."))
            changes_str = "|".join(ch_parts)

        # Determine affordability_status
        if method == "full_payment" and not spending_changes:
            aff_status = "affordable_now"
            earliest_full_date = request_date
            explanation = f"Pay {currency} {amount:,.2f}".replace(".00", "") + f" today. This leaves at least {currency} {winner.get('min_projected_balance', min_balance):,.2f}".replace(".00", "") + " available over the next 90 days."
        elif method == "installments":
            aff_status = "affordable_with_plan"
            num_p = len(payments)
            inst_amt = payments[0][1] if payments else 0.0
            first_d = payments[0][0] if payments else request_date
            explanation = f"Use {num_p} installments of {currency} {inst_amt:,.2f}".replace(".00", "") + f", starting {first_d}. This leaves at least {currency} {winner.get('min_projected_balance', min_balance):,.2f}".replace(".00", "") + " available."
        elif method == "partial_payment":
            aff_status = "affordable_with_plan"
            safe_p = payments[0][1] if payments else safe_today
            rem_p = payments[1][1] if len(payments) > 1 else 0.0
            rem_d = payments[1][0] if len(payments) > 1 else earliest_full_date
            explanation = f"Pay {currency} {safe_p:,.2f}".replace(".00", "") + f" today and the remaining {currency} {rem_p:,.2f}".replace(".00", "") + f" on {rem_d}. This completes the full request and keeps the {currency} {min_balance:,.2f}".replace(".00", "") + " minimum protected."
        elif spending_changes:
            aff_status = "affordable_with_plan"
            explanation = f"Adjust flexible spending, then pay {currency} {amount:,.2f}".replace(".00", "") + f" today. This leaves at least {currency} {min_balance:,.2f}".replace(".00", "") + " available."
        elif method == "wait":
            aff_status = "affordable_later"
            explanation = f"Pay {currency} {amount:,.2f}".replace(".00", "") + f" in full on {earliest_full_date}. Paying earlier would take the balance below the {currency} {min_balance:,.2f}".replace(".00", "") + " minimum."
        else:
            aff_status = "not_affordable"
            method = "not_recommended"
            plan_str = "none"
            explanation = f"Do not make this payment by {desired_completion}. None of the available options keeps the {currency} {min_balance:,.2f}".replace(".00", "") + " minimum protected."

        return {
            "winning_scenario": winner,
            "final_output": {
                "request_id": req_id,
                "amount_safe_to_pay": safe_today,
                "affordability_status": aff_status,
                "recommended_payment_method": method,
                "payment_plan": plan_str,
                "earliest_date_for_full_payment": earliest_full_date if aff_status != "not_affordable" else "",
                "spending_changes_needed": changes_str,
                "decision_explanation": explanation
            }
        }

    def _format_wait_output(self, req_id, currency, amount, earliest_date, safe_today, min_balance) -> Dict[str, Any]:
        return {
            "winning_scenario": {"recommended_payment_method": "wait"},
            "final_output": {
                "request_id": req_id,
                "amount_safe_to_pay": safe_today,
                "affordability_status": "affordable_later",
                "recommended_payment_method": "wait",
                "payment_plan": f"{earliest_date}:{amount:.2f}".rstrip("0").rstrip("."),
                "earliest_date_for_full_payment": earliest_date,
                "spending_changes_needed": "none",
                "decision_explanation": f"Pay {currency} {amount:,.2f}".replace(".00", "") + f" in full on {earliest_date}. Paying earlier would take the balance below the {currency} {min_balance:,.2f}".replace(".00", "") + " minimum."
            }
        }

    def _format_not_affordable_output(self, req_id, currency, amount, desired_completion, safe_today, min_balance) -> Dict[str, Any]:
        return {
            "winning_scenario": {"recommended_payment_method": "not_recommended"},
            "final_output": {
                "request_id": req_id,
                "amount_safe_to_pay": safe_today,
                "affordability_status": "not_affordable",
                "recommended_payment_method": "not_recommended",
                "payment_plan": "none",
                "earliest_date_for_full_payment": "",
                "spending_changes_needed": "none",
                "decision_explanation": f"Do not make this payment by {desired_completion}. None of the available options keeps the {currency} {min_balance:,.2f}".replace(".00", "") + " minimum protected."
            }
        }

def node6_selector_ranker(state: AgentState) -> Dict[str, Any]:
    ranker = ScenarioSelectorRanker()
    return ranker.rank_and_select(state)
