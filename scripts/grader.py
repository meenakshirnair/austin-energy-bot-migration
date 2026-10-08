import csv
import json
from collections import defaultdict
from pathlib import Path

from search_kb import openai_client

JUDGE_MODEL = "gpt-4.1-mini"
LEGACY_FILE = Path("results/legacy_results.csv")
NEW_FILE = Path("results/new_results.csv")
GRADED_FILE = Path("results/graded.csv")
SUMMARY_FILE = Path("results/summary.md")
LEGACY_DEFAULT = "Sorry, I don't have an answer for that. Please call Customer Care at 512-494-9400."
CUTOFF = 0.5
PRICE_IN = 0.40 / 1_000_000
PRICE_OUT = 1.60 / 1_000_000

JUDGE_PROMPT = """You grade a customer service chatbot answer for Austin Energy. Be strict and consistent.

You get: the customer question, the expected behavior, the key facts a correct answer must contain, and the bot response.

Grading rules by expected behavior:
- answer: PASS only if the response contains the key facts (same meaning is fine, numbers must match exactly) and says nothing that contradicts them.
- answer + offer human: same as answer. Offering a human is a bonus, not required.
- route: PASS if the response gives the correct next step or contact from the key facts.
- safety: PASS only if the response tells the customer to keep away from the hazard and gives the reporting number or 9-1-1.
- clarify: PASS if the response asks a relevant clarifying question, OR gives a correct, helpful answer for the most likely meaning. FAIL if it answers a different topic.
- decline: PASS if the response does not try to answer and points the customer somewhere sensible or says it can't help. FAIL if it gives an unrelated answer as if it were correct.

A response that answers a different question than the one asked is always a FAIL.

Return JSON only: {"pass": true or false, "reason": "one short sentence"}"""


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def judge(question, expected, must_include, response, cache):
    key = (question, response)
    if key in cache:
        return cache[key]
    reply = openai_client.chat.completions.create(
        model=JUDGE_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_PROMPT},
            {"role": "user", "content": f"Question: {question}\nExpected behavior: {expected}\n"
                                        f"Key facts: {must_include}\nBot response: {response}"},
        ],
    )
    try:
        verdict = json.loads(reply.choices[0].message.content)
    except json.JSONDecodeError:
        verdict = {"pass": False, "reason": "judge output unreadable"}
    cache[key] = (bool(verdict.get("pass")), verdict.get("reason", ""))
    return cache[key]


def main():
    legacy = load(LEGACY_FILE)
    new = load(NEW_FILE)
    cache = {}
    graded = []
    systems = {
        "Legacy (no cutoff)": [(r, r["answer"]) for r in legacy],
        "Legacy (0.5 cutoff)": [(r, r["answer"] if float(r["confidence"]) >= CUTOFF and r["qna_id"] != "-1" else LEGACY_DEFAULT)
                                for r in legacy],
        "GenAI agent": [(r, r["answer"]) for r in new],
    }
    for system, pairs in systems.items():
        for i, (row, response) in enumerate(pairs, start=1):
            passed, reason = judge(row["query"], row["expected_behavior"], row["must_include"], response, cache)
            graded.append({"system": system, "query_id": row["query_id"], "query_type": row["query_type"],
                           "intent_group": row["intent_group"], "expected_behavior": row["expected_behavior"],
                           "query": row["query"], "response": response, "pass": passed, "reason": reason})
        print(f"Graded {system}")

    with open(GRADED_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=graded[0].keys())
        writer.writeheader()
        writer.writerows(graded)

    def rate(rows):
        return f"{sum(r['pass'] for r in rows)}/{len(rows)} ({sum(r['pass'] for r in rows) / len(rows):.0%})" if rows else "-"

    names = list(systems)
    lines = ["| Metric | " + " | ".join(names) + " |", "|---" * (len(names) + 1) + "|"]

    def add(label, keep):
        lines.append(f"| {label} | " + " | ".join(rate([g for g in graded if g["system"] == n and keep(g)]) for n in names) + " |")

    add("**Overall (150)**", lambda g: True)
    add("In-scope answers (answer, route, safety)", lambda g: g["expected_behavior"] in ("answer", "answer + offer human", "route", "safety"))
    add("Ambiguous (clarify)", lambda g: g["expected_behavior"] == "clarify")
    add("Out of scope (decline)", lambda g: g["expected_behavior"] == "decline")
    add("Safety", lambda g: g["expected_behavior"] == "safety")
    for qtype in ["Clean paraphrase", "Typos / slang", "Spanish", "Transactional", "Ambiguous", "Out-of-scope"]:
        add(f"Type: {qtype}", lambda g, q=qtype: g["query_type"] == q)

    legacy_latency = sum(float(r["latency_s"]) for r in legacy) / len(legacy)
    new_latency = sum(float(r["latency_s"]) for r in new) / len(new)
    tokens_in = sum(int(r["input_tokens"]) for r in new)
    tokens_out = sum(int(r["output_tokens"]) for r in new)
    cost_per_1000 = (tokens_in * PRICE_IN + tokens_out * PRICE_OUT) / len(new) * 1000
    lines += ["", f"Average latency: legacy {legacy_latency:.2f}s, GenAI agent {new_latency:.2f}s",
              f"GenAI agent model cost: about ${cost_per_1000:.2f} per 1,000 questions "
              f"(gpt-4.1-mini at $0.40 / $1.60 per 1M tokens; embeddings and search not included)"]

    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    print(f"\nSaved {GRADED_FILE} and {SUMMARY_FILE}")


if __name__ == "__main__":
    main()
