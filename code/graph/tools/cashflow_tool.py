from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional

class DeterministicCashflowTool:
    """
    Deterministic 90-Day Daily Cashflow Simulator Tool.
    Detects recurring historical income/expense patterns and projects them
    forward for 90 days. Enforces the UNBREACHABLE MINIMUM BALANCE SAFETY RULE.
    """

    def parse_date(self, d_str: str) -> datetime:
        return datetime.strptime(d_str.split("T")[0], "%Y-%m-%d")

    def format_date(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")

    def project_recurring_events(self, events: List[Dict[str, Any]], start_dt: datetime, end_dt: datetime) -> List[Dict[str, Any]]:
        """
        Detects recurring series (events occurring monthly/regularly) and projects
        future occurrences between start_dt and end_dt.
        """
        projected = list(events)
        
        # Group events by category + direction + description
        groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for ev in events:
            key = (ev.get("category"), ev.get("direction"), ev.get("description", ""))
            if key not in groups:
                groups[key] = []
            groups[key].append(ev)

        for key, ev_list in groups.items():
            cat, direction, desc = key
            # Exclude one-off categories or unlinked single items
            if cat in ("purchase", "one_off", "emergency_expense", "investment"):
                continue

            # Sort by date
            sorted_evs = []
            for ev in ev_list:
                d_str = ev.get("settlement_date") or ev.get("event_date")
                if d_str:
                    try:
                        sorted_evs.append((self.parse_date(d_str), ev))
                    except Exception:
                        pass

            sorted_evs.sort(key=lambda x: x[0])
            if len(sorted_evs) < 2 and cat not in ("salary", "rent", "utilities", "subscription", "debt_repayment"):
                continue

            if not sorted_evs:
                continue

            last_dt, last_ev = sorted_evs[-1]
            last_amt = last_ev.get("amount", 0.0) or 0.0
            
            # Check for future updated amount from Node 1 message updates
            future_amt = last_ev.get("future_amount")
            future_eff_dt = last_ev.get("future_effective_date")

            # Project monthly forward up to end_dt
            curr_dt = last_dt
            while curr_dt <= end_dt:
                # Add one month approximately (or 30 days)
                month = curr_dt.month % 12 + 1
                year = curr_dt.year + (curr_dt.month // 12)
                day = min(curr_dt.day, 28)  # Safe day of month
                try:
                    curr_dt = datetime(year, month, day)
                except Exception:
                    curr_dt = curr_dt + timedelta(days=30)

                if curr_dt > end_dt:
                    break

                if curr_dt >= start_dt:
                    d_str = self.format_date(curr_dt)

                    amt_to_use = last_amt
                    if future_amt and future_eff_dt and d_str >= future_eff_dt:
                        amt_to_use = future_amt

                    # Check if already present on this date
                    already_exists = any(
                        (e.get("settlement_date") == d_str or e.get("event_date") == d_str) and e.get("category") == cat
                        for e in events
                    )

                    if not already_exists and amt_to_use > 0:
                        projected.append({
                            "event_id": f"projected_{last_ev['event_id']}_{d_str}",
                            "user_id": last_ev.get("user_id"),
                            "event_type": last_ev.get("event_type"),
                            "description": f"Projected {desc}",
                            "category": cat,
                            "direction": direction,
                            "amount": amt_to_use,
                            "currency": last_ev.get("currency"),
                            "event_date": d_str,
                            "settlement_date": d_str,
                            "status": "confirmed",
                            "flexibility": last_ev.get("flexibility", "fixed"),
                            "minimum_allowed_amount": last_ev.get("minimum_allowed_amount")
                        })

        return projected

    def simulate_90_days(
        self,
        start_balance: float,
        min_balance: float,
        events: List[Dict[str, Any]],
        scenario_payments: List[Tuple[str, float]],
        request_date_str: str,
        spending_changes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Simulates daily balance for 90 days from request_date_str.
        """
        start_dt = self.parse_date(request_date_str)
        end_dt = start_dt + timedelta(days=90)

        # 1. Project recurring events forward for 90 days
        all_events = self.project_recurring_events(events, start_dt, end_dt)

        # Index scenario payments by date
        payments_by_date: Dict[str, float] = {}
        for p_date, p_amt in scenario_payments:
            payments_by_date[p_date] = payments_by_date.get(p_date, 0.0) + p_amt

        # Process spending changes overrides
        disabled_event_ids = set()
        disabled_categories = set()
        reduced_event_amounts: Dict[str, float] = {}

        if spending_changes:
            for sc in spending_changes:
                ev_id = sc.get("event_id")
                cat = sc.get("category")
                if sc.get("action") == "stop":
                    if ev_id:
                        disabled_event_ids.add(ev_id)
                    if cat:
                        disabled_categories.add(cat)
                elif sc.get("action") == "reduce_to":
                    if ev_id:
                        reduced_event_amounts[ev_id] = sc.get("new_amount", 0.0)

        # Build daily delta schedule for [start_dt, end_dt]
        daily_deltas: Dict[str, float] = {}
        curr_dt = start_dt
        while curr_dt <= end_dt:
            daily_deltas[self.format_date(curr_dt)] = 0.0
            curr_dt += timedelta(days=1)

        # Apply event cashflows
        for ev in all_events:
            ev_id = ev.get("event_id")
            cat = ev.get("category")
            if ev_id in disabled_event_ids or cat in disabled_categories:
                continue

            status = ev.get("status")
            direction = ev.get("direction")
            settle_date_str = ev.get("settlement_date") or ev.get("event_date")
            if not settle_date_str:
                continue

            try:
                settle_dt = self.parse_date(settle_date_str)
            except Exception:
                continue

            # Pending debits reserve check
            if status == "pending" and direction == "debit":
                amt = ev.get("amount", 0.0) or 0.0
                start_balance -= amt  # Reserved immediately
                continue

            # Skip past events, pending credits, unrealized investments
            if status not in ("settled", "scheduled", "recurring", "confirmed"):
                continue

            if settle_dt < start_dt:
                # Past event already in bank balance
                continue

            if settle_dt > end_dt:
                # Beyond 90 days
                continue

            amt = ev.get("amount", 0.0) or 0.0
            if ev_id in reduced_event_amounts:
                amt = reduced_event_amounts[ev_id]

            if direction == "credit":
                daily_deltas[settle_date_str] = daily_deltas.get(settle_date_str, 0.0) + amt
            elif direction == "debit":
                daily_deltas[settle_date_str] = daily_deltas.get(settle_date_str, 0.0) - amt

        # Run day-by-day 90-day trajectory
        curr_balance = start_balance
        min_projected_balance = curr_balance
        violation_date = None
        is_safe = True

        curr_dt = start_dt
        while curr_dt <= end_dt:
            d_str = self.format_date(curr_dt)

            # Apply scenario payment
            if d_str in payments_by_date:
                curr_balance -= payments_by_date[d_str]

            # Apply regular daily cashflow
            curr_balance += daily_deltas.get(d_str, 0.0)

            if curr_balance < min_projected_balance:
                min_projected_balance = curr_balance

            # Safety Rule Check
            if curr_balance < min_balance and is_safe:
                is_safe = False
                violation_date = d_str

            curr_dt += timedelta(days=1)

        return {
            "is_safe": is_safe,
            "min_projected_balance": min_projected_balance,
            "safe_margin": min_projected_balance - min_balance,
            "violation_date": violation_date
        }

    def compute_amount_safe_to_pay(
        self,
        start_balance: float,
        min_balance: float,
        events: List[Dict[str, Any]],
        request_date_str: str,
        requested_amount: float
    ) -> float:
        """
        Calculates maximum amount safe to pay today.
        Uses two-step approach:
        1. Day-0 margin: balance right now minus pending debits minus min_balance
        2. If paying Day-0 margin as a lump sum still passes the full 90-day sim, return it
        Otherwise binary search downward to find the largest safe amount.
        """
        # Step 1: Deduct pending debits from start_balance (same logic as simulate_90_days)
        pending_debit_total = 0.0
        for ev in events:
            if ev.get("status") == "pending" and ev.get("direction") == "debit":
                pending_debit_total += float(ev.get("amount") or 0.0)

        effective_balance = start_balance - pending_debit_total
        day0_margin = max(0.0, effective_balance - min_balance)
        safe_candidate = min(requested_amount, day0_margin)

        if safe_candidate <= 0.0:
            return 0.0

        # Step 2: Verify paying safe_candidate today still passes the full 90-day sim
        res = self.simulate_90_days(
            start_balance=start_balance,
            min_balance=min_balance,
            events=events,
            scenario_payments=[(request_date_str, safe_candidate)],
            request_date_str=request_date_str
        )
        if res["is_safe"]:
            return safe_candidate

        # Step 3: Binary search for largest amount that keeps sim safe
        lo, hi = 0.0, safe_candidate
        for _ in range(20):
            mid = (lo + hi) / 2.0
            res = self.simulate_90_days(
                start_balance=start_balance,
                min_balance=min_balance,
                events=events,
                scenario_payments=[(request_date_str, mid)],
                request_date_str=request_date_str
            )
            if res["is_safe"]:
                lo = mid
            else:
                hi = mid
        return max(0.0, lo)

    def find_earliest_full_payment_date(
        self,
        start_balance: float,
        min_balance: float,
        events: List[Dict[str, Any]],
        request_date_str: str,
        requested_amount: float
    ) -> Tuple[Optional[str], float]:
        """
        Finds earliest date D in [request_date, request_date + 90] where paying
        full requested_amount as a single payment on date D keeps min balance protected.
        """
        start_dt = self.parse_date(request_date_str)
        end_dt = start_dt + timedelta(days=90)

        curr_dt = start_dt
        while curr_dt <= end_dt:
            d_str = self.format_date(curr_dt)
            sim_res = self.simulate_90_days(
                start_balance=start_balance,
                min_balance=min_balance,
                events=events,
                scenario_payments=[(d_str, requested_amount)],
                request_date_str=request_date_str
            )
            if sim_res["is_safe"]:
                return d_str, sim_res["min_projected_balance"]

            curr_dt += timedelta(days=1)

        return None, 0.0
