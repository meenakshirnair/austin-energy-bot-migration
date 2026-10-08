import csv
import time
from pathlib import Path

import openpyxl

from query_legacy import ask_legacy

TEST_SET = Path("data/test_set.xlsx")
RESULTS_DIR = Path("results")
OUTPUT = RESULTS_DIR / "legacy_results.csv"
THRESHOLD = 0.5
PAUSE_SECONDS = 0.5


def load_test_set():
    sheet = openpyxl.load_workbook(TEST_SET, read_only=True)["Test Set"]
    rows = list(sheet.iter_rows(values_only=True))
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:] if row[0]]


def gold_pages(test):
    raw = test.get("gold_page_ids") or ""
    return {p.strip().lower() for p in raw.split(";") if p.strip()}


def main():
    tests = load_test_set()
    RESULTS_DIR.mkdir(exist_ok=True)
    results = []
    for i, test in enumerate(tests, start=1):
        print(f"[{i}/{len(tests)}] {test['query_id']} {test['query']}")
        try:
            reply = ask_legacy(test["query"])
            error = ""
        except Exception as e:
            reply = {"answer": "", "confidence": 0, "qna_id": -1, "metadata": {}, "latency_s": 0}
            error = str(e)

        matched_page = reply["metadata"].get("page", "")
        answered = reply["qna_id"] != -1
        results.append({
            "query_id": test["query_id"],
            "intent_group": test["intent_group"],
            "query_type": test["query_type"],
            "expected_behavior": test["expected_behavior"],
            "query": test["query"],
            "answer": reply["answer"],
            "confidence": reply["confidence"],
            "qna_id": reply["qna_id"],
            "matched_page": matched_page,
            "answered_raw": answered,
            "answered_at_threshold": answered and reply["confidence"] >= THRESHOLD,
            "page_in_gold": matched_page in gold_pages(test),
            "latency_s": reply["latency_s"],
            "must_include": test["must_include"],
            "error": error,
        })
        time.sleep(PAUSE_SECONDS)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    in_scope = [r for r in results if r["expected_behavior"] != "decline"]
    out_scope = [r for r in results if r["expected_behavior"] == "decline"]
    errors = [r for r in results if r["error"]]
    print(f"\nSaved {len(results)} results to {OUTPUT}")
    print(f"Errors: {len(errors)}")
    print(f"In scope ({len(in_scope)}): answered {sum(r['answered_raw'] for r in in_scope)}, "
          f"answered from a correct page {sum(r['answered_raw'] and r['page_in_gold'] for r in in_scope)}")
    print(f"Out of scope ({len(out_scope)}): correctly said 'no answer' {sum(not r['answered_raw'] for r in out_scope)} raw, "
          f"{sum(not r['answered_at_threshold'] for r in out_scope)} with {THRESHOLD} cutoff")
    print(f"Average latency: {sum(r['latency_s'] for r in results) / len(results):.2f}s")


if __name__ == "__main__":
    main()
