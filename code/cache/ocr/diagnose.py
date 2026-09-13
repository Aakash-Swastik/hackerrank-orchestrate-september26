import csv, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from graph.tools.io_csv import DataLoader
from graph.tools.cashflow_tool import CashflowSimulator
from datetime import date

dl = DataLoader('dataset')
data = dl.load_all()

failing = ['request_02', 'request_06', 'request_08', 'request_16', 'request_17',
           'request_21', 'request_22', 'request_23']

for row in data['requests']:
    if row['request_id'] not in failing:
        continue
    uid = row['user_id']
    prof = next((p for p in data['profiles'] if p['user_id'] == uid), {})
    item_cost = float(row.get('item_cost') or 0)
    balance = float(prof.get('current_balance') or 0)
    min_bal = float(prof.get('minimum_balance') or 0)
    currency = prof.get('home_currency', '')

    # Run cashflow sim
    sim = CashflowSimulator(data, uid, date.today())
    result = sim.simulate_90_days()
    safe = result.get('amount_safe_to_pay', 0)
    earliest = result.get('earliest_full_payment_date')
    min_monthly = result.get('min_monthly_income', 0)

    print(f"\n--- {row['request_id']} user={uid} ---")
    print(f"  item_cost={item_cost} | balance={balance} | min_bal={min_bal} | currency={currency}")
    print(f"  safe_to_pay={safe:.2f} | earliest={earliest} | min_monthly_income={min_monthly:.2f}")
    # Show projected events count
    events = [e for e in data['events'] if e['user_id'] == uid]
    incomes = [e for e in events if e['direction'] == 'credit' and e['event_type'] == 'income']
    print(f"  total_events={len(events)} | income_events={len(incomes)}")
