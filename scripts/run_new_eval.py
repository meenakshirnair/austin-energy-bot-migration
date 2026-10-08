import csv
import time
from pathlib import Path

import openpyxl

from router import respond

TEST_SET = Path("data/test_set.xlsx")
OUTPUT = Path("results/new_results.csv")
PAUSE_SECONDS = 0.5


def load_test_set():
    sheet = openpyxl.load_workbook(TEST_SET, read_only=True)["Test Set"]
    rows = list(sheet.iter_rows(values_only=True))
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:] if row[0]]


def main():
    tests = load_test_set()
    results = []
    for i, test in enumerate(tests, start=1):
        print(f"[{i}/{len(tests)}] {test['query_id']} {test['query']}")
        try:
            reply = respond(test["query"])
            error = ""
        except Exception as e:
            reply = {"route": "", "action": "error", "answer": "", "cited_pages": [], "offer_human": False,
                     "handoff_summary": "", "latency_s": 0, "input_tokens": 0, "output_tokens": 0}
            error = str(e)
        gold = {p.strip() for p in (test.get("gold_page_ids") or "").split(";") if p.strip()}
        results.append({
            "query_id": test["query_id"],
            "intent_group": test["intent_group"],
            "query_type": test["query_type"],
            "expected_behavior": test["expected_behavior"],
            "query": test["query"],
            "route": reply["route"],
            "action": reply["action"],
            "answer": reply["answer"],
            "cited_pages": ";".join(reply["cited_pages"]),
            "cited_gold_page": bool(gold & set(reply["cited_pages"])),
            "offer_human": reply["offer_human"],
            "handoff_summary": reply["handoff_summary"],
            "latency_s": reply["latency_s"],
            "input_tokens": reply["input_tokens"],
            "output_tokens": reply["output_tokens"],
            "must_include": test["must_include"],
            "error": error,
        })
        time.sleep(PAUSE_SECONDS)

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    errors = sum(1 for r in results if r["error"])
    print(f"\nSaved {len(results)} results to {OUTPUT}. Errors: {errors}")
    actions = {}
    for r in results:
        actions[r["action"]] = actions.get(r["action"], 0) + 1
    print("Actions taken:", actions)


if __name__ == "__main__":
    main()
