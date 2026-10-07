import csv
import re
from pathlib import Path

DATA = Path("data")
CLEAN_DIR = DATA / "clean"
MANUAL_FILE = DATA / "legacy_manual_pairs.csv"
OUTPUT_FILE = DATA / "legacy_kb.tsv"

QUESTION_START = re.compile(
    r"^(?P<q>(What|How|Why|When|Where|Who|Which|Can|Could|Do|Does|Did|Is|Are|Will|Should|May|Am|If)\b[^?]{3,200}\?)\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
STOP_LINES = ("Date last reviewed", "Contact City of Austin Customer Care")
MIN_PAIRS_PER_PAGE = 5


def load_legacy_pages():
    with open(DATA / "scrape_list.csv", newline="", encoding="utf-8") as f:
        return [row for row in csv.DictReader(f) if row["in_legacy_qa"] == "Yes"]


def read_body(page_id):
    text = (CLEAN_DIR / f"{page_id}.md").read_text(encoding="utf-8")
    return text.split("---", 2)[2]


def clean_line(line):
    return line.strip().lstrip("-").strip()


def extract_faq_pairs(body):
    pairs = []
    question, answer = None, []
    for raw in body.splitlines():
        line = clean_line(raw)
        if not line:
            continue
        if line.startswith(STOP_LINES):
            break
        match = QUESTION_START.match(line)
        if match:
            if question and answer:
                pairs.append((question, " ".join(answer)))
            question = match.group("q").strip()
            answer = [match.group("rest")] if match.group("rest") else []
        elif question:
            answer.append(line)
    if question and answer:
        pairs.append((question, " ".join(answer)))
    return pairs


def slug(value):
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def load_manual_pairs():
    if not MANUAL_FILE.exists():
        return []
    with open(MANUAL_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    pages = load_legacy_pages()
    groups = {p["page_id"]: p["intent_groups"].split(";")[0].strip() for p in pages}
    rows = []
    no_faq = []
    for page in pages:
        pairs = extract_faq_pairs(read_body(page["page_id"]))
        if len(pairs) < MIN_PAIRS_PER_PAGE:
            pairs = []
        if not pairs:
            no_faq.append(page["page_id"])
        for q, a in pairs:
            rows.append((q, a, page["page_id"], groups[page["page_id"]]))
        print(f"{page['page_id']}: {len(pairs)} FAQ pairs")

    manual = load_manual_pairs()
    for m in manual:
        rows.append((m["question"], m["answer"], m["page_id"], groups.get(m["page_id"], "unknown")))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Question\tAnswer\tMetadata\n")
        for q, a, pid, group in rows:
            q = q.replace("\t", " ").replace('"', "'")
            a = a.replace("\t", " ").replace('"', "'")
            f.write(f"{q}\t{a}\tpage:{pid.lower()}|intent:{slug(group)}\n")

    print(f"\n{len(rows) - len(manual)} FAQ pairs + {len(manual)} manual pairs = {len(rows)} total")
    print("Pages with no FAQ pairs (write manual pairs for these):", " ".join(no_faq))


if __name__ == "__main__":
    main()
