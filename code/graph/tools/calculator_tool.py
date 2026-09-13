import copy
from typing import Dict, List, Any, Tuple

class Node1CalculatorTool:
    """
    Node 1 Financial Calculator Tool.
    Applies extracted facts (OCR amounts and message facts) onto past CSV records
    to generate updated_record and track a change_list. Enforces request_date cutoff.
    """

    def reconcile_records(
        self,
        user_profile: Dict[str, Any],
        user_events: List[Dict[str, Any]],
        message_facts: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        request_date: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
        """
        Returns (past_record, updated_record, change_list)
        """
        # Past record snapshot
        past_record = {
            "profile": copy.deepcopy(user_profile),
            "events": copy.deepcopy(user_events)
        }

        # Updated record working copy
        updated_profile = copy.deepcopy(user_profile)
        updated_events = copy.deepcopy(user_events)
        change_list: List[Dict[str, Any]] = []

        # Map events by ID
        events_by_id = {e["event_id"]: e for e in updated_events}

        # 1. Apply OCR Extractions (Fill Blank Amounts)
        for ocr in ocr_results:
            if ocr.get("extraction_status") == "ok":
                rel_event_id = ocr.get("related_event_id")
                chosen_amt = ocr.get("selection", {}).get("chosen_amount")
                if rel_event_id and rel_event_id in events_by_id and chosen_amt is not None:
                    event = events_by_id[rel_event_id]
                    old_amt = event.get("amount")
                    event["amount"] = chosen_amt

                    # Update status if OCR confirmed payment
                    if "paid" in ocr.get("selection", {}).get("chosen_label", ""):
                        event["status"] = "settled"

                    change_list.append({
                        "event_id": rel_event_id,
                        "field": "amount",
                        "old_value": old_amt,
                        "new_value": chosen_amt,
                        "source": ocr.get("image_id"),
                        "reason": f"Filled blank amount from OCR ({ocr.get('selection', {}).get('chosen_label')})"
                    })

        # 2. Apply Message Facts (Date Cutoff & Future Staging)
        for msg_item in message_facts:
            msg_date = msg_item.get("sent_at", "").split("T")[0]
            if msg_date > request_date:
                # Information Leakage Protection: Drop message sent after request_date
                continue

            for fact in msg_item.get("facts", []):
                action = fact.get("action")
                eff_date = fact.get("effective_date", msg_date)
                amt = fact.get("amount")
                target_event_id = fact.get("related_event_id")

                if action == "salary_amount_change" and amt is not None:
                    # Find recurring salary event
                    salary_events = [e for e in updated_events if e["category"] == "salary" or "salary" in e["description"].lower()]
                    for sal_e in salary_events:
                        old_val = sal_e.get("amount")
                        
                        if eff_date <= request_date:
                            # Current value update
                            sal_e["amount"] = amt
                            in_force_today = True
                        else:
                            # Future value update staged on timeline
                            sal_e["future_amount"] = amt
                            sal_e["future_effective_date"] = eff_date
                            in_force_today = False

                        change_list.append({
                            "event_id": sal_e["event_id"],
                            "field": "amount",
                            "old_value": old_val,
                            "new_value": amt,
                            "effective_date": eff_date,
                            "in_force_on_request_date": in_force_today,
                            "source": msg_item.get("message_id"),
                            "reason": f"Salary updated via message ({action})"
                        })

                elif action == "rent_increase_percent" and amt is not None:
                    rent_events = [e for e in updated_events if e["category"] == "rent"]
                    for rent_e in rent_events:
                        old_val = rent_e.get("amount")
                        if old_val:
                            new_val = old_val * (1.0 + (amt / 100.0))
                            if eff_date <= request_date:
                                rent_e["amount"] = new_val
                                in_force_today = True
                            else:
                                rent_e["future_amount"] = new_val
                                rent_e["future_effective_date"] = eff_date
                                in_force_today = False

                            change_list.append({
                                "event_id": rent_e["event_id"],
                                "field": "amount",
                                "old_value": old_val,
                                "new_value": new_val,
                                "effective_date": eff_date,
                                "in_force_on_request_date": in_force_today,
                                "source": msg_item.get("message_id"),
                                "reason": f"Rent increased by {amt}%"
                            })

        updated_record = {
            "profile": updated_profile,
            "events": updated_events
        }

        return past_record, updated_record, change_list
