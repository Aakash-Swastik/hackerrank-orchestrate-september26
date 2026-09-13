from typing import Dict, Any
from graph.state import AgentState
from graph.tools.io_csv import DataLoader
from graph.tools.fx_tool import DirectFXTool

def node3_gather_evidence(state: AgentState, data_loader: DataLoader) -> Dict[str, Any]:
    """
    Node 3: Evidence Gathering Node.
    Compiles user profile, balance, minimum buffer, protected vs flexible categories,
    available payment options, and converts foreign events to native home_currency.
    """
    req_id = state["request_id"]
    updated_rec = state.get("updated_record", {})
    profile = updated_rec.get("profile", {})
    events = updated_rec.get("events", [])
    home_currency = profile.get("home_currency", "USD")

    fx_tool = DirectFXTool(exchange_rates=data_loader.exchange_rates)

    # Normalize events into native home_currency
    normalized_events = []
    for ev in events:
        ev_copy = dict(ev)
        amt = ev_copy.get("amount")
        ev_curr = ev_copy.get("currency", home_currency)
        settle_date = ev_copy.get("settlement_date") or ev_copy.get("event_date")

        if amt is not None and ev_curr != home_currency:
            converted_amt = fx_tool.convert_to_home(
                amount=amt,
                from_currency=ev_curr,
                home_currency=home_currency,
                settlement_date=settle_date
            )
            ev_copy["amount"] = converted_amt
            ev_copy["currency"] = home_currency

        normalized_events.append(ev_copy)

    # Filter payment options for this request
    all_options = data_loader.get_request_options(req_id)
    max_months = profile.get("max_installment_months")
    considered_methods = profile.get("payment_methods_user_will_consider", [])

    eligible_options = []
    for opt in all_options:
        method = opt.get("payment_method")
        num_payments = opt.get("number_of_payments", 1)

        if method == "installments":
            if max_months is not None and num_payments > max_months:
                continue
            if "installments" not in considered_methods and "all" not in considered_methods:
                continue

        eligible_options.append(opt)

    evidence_pack = {
        "home_currency": home_currency,
        "current_available_balance": profile.get("current_available_balance", 0.0),
        "minimum_balance_to_keep": profile.get("minimum_balance_to_keep", 0.0),
        "financial_priorities": profile.get("financial_priorities", []),
        "expense_categories_to_protect": profile.get("expense_categories_to_protect", []),
        "expense_categories_user_is_willing_to_reduce": profile.get("expense_categories_user_is_willing_to_reduce", []),
        "expense_categories_user_is_willing_to_stop": profile.get("expense_categories_user_is_willing_to_stop", []),
        "payment_methods_user_will_consider": considered_methods,
        "max_installment_months": max_months,
        "normalized_events": normalized_events,
        "eligible_payment_options": eligible_options
    }

    return {
        "evidence_pack": evidence_pack
    }
