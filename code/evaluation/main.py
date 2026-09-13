import os
import sys
import csv

# Add code/ folder to sys.path
code_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from graph.tools.io_csv import DataLoader
from graph.tools.bedrock_client import BedrockClient
from graph.workflow import build_agent_graph

REQUIRED_COLUMNS = [
    "amount_safe_to_pay",
    "affordability_status",
    "recommended_payment_method",
    "payment_plan",
    "earliest_date_for_full_payment",
    "spending_changes_needed"
]

def run_golden_benchmark():
    print("=" * 60)
    print("Running Golden Benchmark against sample_requests.csv (25 Solved Samples)")
    print("=" * 60)

    data_loader = DataLoader(dataset_dir="dataset")
    bedrock_client = BedrockClient()

    graph = build_agent_graph(data_loader=data_loader, bedrock_client=bedrock_client)

    matches = {col: 0 for col in REQUIRED_COLUMNS}
    total_samples = len(data_loader.sample_requests)

    for idx, sample in enumerate(data_loader.sample_requests, 1):
        req_id = sample["request_id"]
        user_id = sample["user_id"]
        req_date = sample["request_date"]

        initial_state = {
            "request_id": req_id,
            "request_data": sample,
            "user_id": user_id,
            "request_date": req_date,
            "past_record": {},
            "updated_record": {},
            "change_list": [],
            "similar_cases": [],
            "evidence_pack": {},
            "candidate_scenarios": [],
            "evaluated_scenarios": [],
            "winning_scenario": None,
            "final_output": {},
            "audit_log": {},
            "error_state": None
        }

        try:
            res_state = graph.invoke(initial_state)
            pred = res_state.get("final_output", {})

            for col in REQUIRED_COLUMNS:
                gt_val = str(sample.get(col, "")).strip()
                pred_val = str(pred.get(col, "")).strip()

                if col == "amount_safe_to_pay":
                    try:
                        gt_num = float(gt_val)
                        pred_num = float(pred_val)
                        if abs(gt_num - pred_num) <= 1.0:
                            matches[col] += 1
                    except Exception:
                        pass
                else:
                    if gt_val == pred_val:
                        matches[col] += 1

            print(f"Sample [{idx}/{total_samples}] {req_id}: Method={pred.get('recommended_payment_method')} (GT: {sample.get('recommended_payment_method')}) | Status={pred.get('affordability_status')} (GT: {sample.get('affordability_status')})")

        except Exception as e:
            print(f"Sample [{idx}/{total_samples}] {req_id} Exception: {e}")

    print("=" * 60)
    print("Golden Benchmark Column Accuracy Summary:")
    print("=" * 60)
    for col, count in matches.items():
        pct = (count / max(1, total_samples)) * 100.0
        print(f" - {col:30s}: {count}/{total_samples} ({pct:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    run_golden_benchmark()
