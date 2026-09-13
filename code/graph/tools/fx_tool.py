from typing import List, Dict, Any

class DirectFXTool:
    """
    Direct Exchange Rate Converter Tool.
    Converts foreign amounts directly into user's home_currency using dated rates in exchange_rates.csv.
    """

    def __init__(self, exchange_rates: List[Dict[str, Any]]):
        self.exchange_rates = exchange_rates
        # Index rates by (rate_date, from_curr, to_curr)
        self.rates_map: Dict[tuple, float] = {}
        for r in exchange_rates:
            date_str = r.get("rate_date")
            from_c = r.get("from_currency")
            to_c = r.get("to_currency")
            rate_val = float(r.get("rate", 1.0))
            if date_str and from_c and to_c:
                self.rates_map[(date_str, from_c, to_c)] = rate_val

    def convert_to_home(self, amount: float, from_currency: str, home_currency: str, settlement_date: str) -> float:
        if from_currency == home_currency or amount is None or amount == 0.0:
            return amount

        # Look for exact date match
        key = (settlement_date, from_currency, home_currency)
        if key in self.rates_map:
            return amount * self.rates_map[key]

        # Look for nearest available rate date
        available_rates = [
            (abs((r["rate_date"] - settlement_date)), r["rate"])
            for r in self.exchange_rates
            if r["from_currency"] == from_currency and r["to_currency"] == home_currency
        ]

        if available_rates:
            available_rates.sort(key=lambda x: x[0])
            nearest_rate = float(available_rates[0][1])
            return amount * nearest_rate

        # Fallback: Inverse rate lookup if direct pair is inverted
        inv_key_matches = [
            r["rate"] for r in self.exchange_rates
            if r["from_currency"] == home_currency and r["to_currency"] == from_currency
        ]
        if inv_key_matches:
            inv_rate = float(inv_key_matches[0])
            if inv_rate != 0:
                return amount / inv_rate

        return amount
