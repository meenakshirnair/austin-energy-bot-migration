import csv
from collections import defaultdict
from pathlib import Path

import openpyxl

from search_kb import search_kb

TEST_SET = Path("data/test_set.xlsx")
OUTPUT = Path("results/retrieval_results.csv")
MODES = ["keyword", "vector", "hybrid"]
TOP_K = 5


def load_test_set():
    sheet = openpyxl.load_workbook(TEST_SET, read_only=True)["Test Set"]
    rows = list(sheet.iter_rows(values_only=True))
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:] if row[0]]


def gold_pages(test):
    raw = test.get("gold_page_ids") or ""
    return [p.strip() for p in raw.split(";") if p.strip()]


def first_hit_rank(hits, gold):
    for rank, hit in enumerate(hits, start=1):
        if hit["page_id"] in gold:
            return rank
    return None


def main():
    tests = [t for t in load_test_set() if gold_pages(t)]
    print(f"Scoring retrieval on {len(tests)} in-scope questions that have gold pages\n")
    rows = []
    for mode in MODES:
        for test in tests:
            hits = search_kb(test["query"], mode=mode, top=TOP_K)
            rank = first_hit_rank(hits, gold_pages(test))
            rows.append({
                "mode": mode,
                "query_id": test["query_id"],
                "query_type": test["query_type"],
                "intent_group": test["intent_group"],
                "query": test["query"],
                "gold_pages": ";".join(gold_pages(test)),
                "retrieved_pages": ";".join(h["page_id"] for h in hits),
                "first_correct_rank": rank or "",
            })
        print(f"Finished {mode}")

    OUTPUT.parent.mkdir(exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'mode':<8} {'hit@1':>7} {'hit@5':>7} {'MRR':>6}")
    for mode in MODES:
        ranks = [r["first_correct_rank"] for r in rows if r["mode"] == mode]
        n = len(ranks)
        hit1 = sum(1 for r in ranks if r == 1) / n
        hit5 = sum(1 for r in ranks if r) / n
        mrr = sum(1 / r for r in ranks if r) / n
        print(f"{mode:<8} {hit1:>7.0%} {hit5:>7.0%} {mrr:>6.2f}")

    print("\nHybrid hit@5 by question type:")
    by_type = defaultdict(list)
    for r in rows:
        if r["mode"] == "hybrid":
            by_type[r["query_type"]].append(bool(r["first_correct_rank"]))
    for qtype, hits in sorted(by_type.items()):
        print(f"  {qtype:<18} {sum(hits)}/{len(hits)}")

    misses = [r for r in rows if r["mode"] == "hybrid" and not r["first_correct_rank"]]
    print(f"\nHybrid misses ({len(misses)}):")
    for r in misses:
        print(f"  {r['query_id']} [{r['query_type']}] {r['query']}  -> got {r['retrieved_pages']}")
    print(f"\nSaved details to {OUTPUT}")


if __name__ == "__main__":
    main()
