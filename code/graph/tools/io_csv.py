import os
import csv
from typing import Dict, List, Any, Optional

class DataLoader:
    """
    Robust CSV Data Loader for the Buy or Wait dataset.
    Loads and indexes all files inside dataset/ directory.
    """

    def __init__(self, dataset_dir: str = "dataset"):
        self.dataset_dir = dataset_dir
        self.requests: List[Dict[str, Any]] = []
        self.sample_requests: List[Dict[str, Any]] = []
        self.profiles_by_user: Dict[str, Dict[str, Any]] = {}
        self.events_by_user: Dict[str, List[Dict[str, Any]]] = {}
        self.payment_options_by_request: Dict[str, List[Dict[str, Any]]] = {}
        self.exchange_rates: List[Dict[str, Any]] = []
        self.messages_by_user: Dict[str, List[Dict[str, Any]]] = {}
        self.images_by_user: Dict[str, List[Dict[str, Any]]] = {}
        self.images_by_event: Dict[str, Dict[str, Any]] = {}

        self._load_all()

    def _read_csv(self, filename: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.dataset_dir, filename)
        if not os.path.exists(path):
            return []
        with open(path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]

    def _load_all(self):
        # 1. Requests
        self.requests = self._read_csv("requests.csv")

        # 2. Sample Requests
        self.sample_requests = self._read_csv("sample_requests.csv")

        # 3. Financial Profiles
        profiles_raw = self._read_csv("financial_profiles.csv")
        for p in profiles_raw:
            user_id = p["user_id"]
            bal = p.get("current_available_balance", "").strip()
            min_b = p.get("minimum_balance_to_keep", "").strip()
            max_m = p.get("max_installment_months", "").strip()

            self.profiles_by_user[user_id] = {
                "user_id": user_id,
                "home_currency": p["home_currency"],
                "current_available_balance": float(bal) if bal != "" else 0.0,
                "minimum_balance_to_keep": float(min_b) if min_b != "" else 0.0,
                "financial_priorities": [x.strip() for x in p.get("financial_priorities", "").split("|") if x.strip()],
                "expense_categories_to_protect": [x.strip() for x in p.get("expense_categories_to_protect", "").split("|") if x.strip()],
                "expense_categories_user_is_willing_to_reduce": [x.strip() for x in p.get("expense_categories_user_is_willing_to_reduce", "").split("|") if x.strip()],
                "expense_categories_user_is_willing_to_stop": [x.strip() for x in p.get("expense_categories_user_is_willing_to_stop", "").split("|") if x.strip()],
                "payment_methods_user_will_consider": [x.strip() for x in p.get("payment_methods_user_will_consider", "").split("|") if x.strip()],
                "max_installment_months": int(max_m) if max_m.isdigit() else None
            }

        # 4. Financial Events
        events_raw = self._read_csv("financial_events.csv")
        for e in events_raw:
            user_id = e["user_id"]
            if user_id not in self.events_by_user:
                self.events_by_user[user_id] = []
            
            amt_str = e.get("amount", "").strip()
            min_amt_str = e.get("minimum_allowed_amount", "").strip()

            amt = float(amt_str) if amt_str != "" else None
            min_amt = float(min_amt_str) if min_amt_str != "" else None

            event_obj = {
                "event_id": e["event_id"],
                "user_id": user_id,
                "event_type": e["event_type"],
                "description": e["description"],
                "category": e["category"],
                "direction": e["direction"],
                "amount": amt,
                "currency": e["currency"],
                "event_date": e["event_date"],
                "settlement_date": e["settlement_date"],
                "status": e["status"],
                "linked_event_id": e.get("linked_event_id") or None,
                "flexibility": e.get("flexibility") or "fixed",
                "minimum_allowed_amount": min_amt
            }
            self.events_by_user[user_id].append(event_obj)

        # 5. Request Payment Options
        options_raw = self._read_csv("request_payment_options.csv")
        for opt in options_raw:
            req_id = opt["request_id"]
            if req_id not in self.payment_options_by_request:
                self.payment_options_by_request[req_id] = []
            
            amt_str = opt.get("payment_amount", "").strip()
            num_p_str = opt.get("number_of_payments", "").strip()
            freq_str = opt.get("payment_frequency_days", "").strip()
            fee_str = opt.get("financing_fee", "").strip()
            tot_str = opt.get("total_payable_amount", "").strip()

            opt_obj = {
                "payment_option_id": opt["payment_option_id"],
                "request_id": req_id,
                "payment_method": opt["payment_method"],
                "payment_amount": float(amt_str) if amt_str != "" else 0.0,
                "number_of_payments": int(num_p_str) if num_p_str.isdigit() else 1,
                "first_payment_date": opt.get("first_payment_date", ""),
                "payment_frequency_days": int(freq_str) if freq_str.isdigit() else 0,
                "financing_fee": float(fee_str) if fee_str != "" else 0.0,
                "total_payable_amount": float(tot_str) if tot_str != "" else 0.0
            }
            self.payment_options_by_request[req_id].append(opt_obj)

        # 6. Exchange Rates
        rates_raw = self._read_csv("exchange_rates.csv")
        for r in rates_raw:
            rate_val_str = r.get("rate", "").strip()
            self.exchange_rates.append({
                "rate_date": r["rate_date"],
                "from_currency": r["from_currency"],
                "to_currency": r["to_currency"],
                "rate": float(rate_val_str) if rate_val_str != "" else 1.0
            })

        # 7. Messages
        messages_raw = self._read_csv("messages.csv")
        for m in messages_raw:
            user_id = m["user_id"]
            if user_id not in self.messages_by_user:
                self.messages_by_user[user_id] = []
            self.messages_by_user[user_id].append(m)

        # 8. Images
        images_raw = self._read_csv("images.csv")
        for img in images_raw:
            user_id = img["user_id"]
            rel_event = img.get("related_event_id")
            if user_id not in self.images_by_user:
                self.images_by_user[user_id] = []
            self.images_by_user[user_id].append(img)
            if rel_event:
                self.images_by_event[rel_event] = img

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.profiles_by_user.get(user_id)

    def get_user_events(self, user_id: str) -> List[Dict[str, Any]]:
        return self.events_by_user.get(user_id, [])

    def get_request_options(self, request_id: str) -> List[Dict[str, Any]]:
        return self.payment_options_by_request.get(request_id, [])

    def get_user_messages(self, user_id: str) -> List[Dict[str, Any]]:
        return self.messages_by_user.get(user_id, [])

    def get_event_image(self, event_id: str) -> Optional[Dict[str, Any]]:
        return self.images_by_event.get(event_id)
