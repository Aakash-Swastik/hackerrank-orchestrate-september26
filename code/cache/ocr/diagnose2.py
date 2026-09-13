import sys, json
sys.path.insert(0, 'code')
from graph.tools.io_csv import DataLoader
from graph.tools.cashflow_tool import DeterministicCashflowTool
from datetime import date

dl = DataLoader('dataset')
data = dl._load_all()

failing = ['request_02','request_06','request_08','request_16','request_21','request_22','request_23']
tool = DeterministicCashflowTool(data)

for row in data['requests']:
    if row['request_id'] not in failing:
        continue
    uid = row['user_id']
    prof = next((p for p in data['profiles'] if p['user_id'] == uid), {})
    item_cost = float(row.get('item_cost') or 0)
    balance = float(prof.get('current_balance') or 0)
    min_bal = float(prof.get('minimum_balance') or 0)
    currency = prof.get('home_currency', '')
    today = date.today().isoformat()
    result = tool.evaluate(uid, item_cost, currency, today, {})
    safe = result.get('amount_safe_to_pay', 0)
    earliest = result.get('earliest_full_payment_date', '?')
    proj_income = result.get('projected_income_90d', '?')
    print(f"{row['request_id']} uid={uid} cost={item_cost} bal={balance} min={min_bal} cur={currency}")
    print(f"   safe={safe} earliest={earliest} proj_income_90d={proj_income}")
    # Show income events
    incomes = [e for e in data['events'] if e['user_id']==uid and e['direction']=='credit']
    print(f"   income_events={len(incomes)}")
    if incomes:
        for e in incomes[-3:]:
            print(f"      {e['event_date']} {e['amount']} {e['currency']} {e['description']}")
    print()
