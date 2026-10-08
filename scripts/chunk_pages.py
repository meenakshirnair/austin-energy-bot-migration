import json
from pathlib import Path

CLEAN_DIR = Path("data/clean")
OUTPUT = Path("data/chunks.jsonl")
TARGET_WORDS = 250
OVERLAP_WORDS = 40


def read_page(path):
    text = path.read_text(encoding="utf-8")
    _, header, body = text.split("---", 2)
    meta = {}
    for line in header.strip().splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta, body.strip()


def split_into_chunks(body):
    lines = [line.strip() for line in body.splitlines() if line.strip() not in ("", "-")]
    chunks, current = [], []
    for line in lines:
        current.append(line)
        if sum(len(l.split()) for l in current) >= TARGET_WORDS:
            chunks.append(current)
            tail_words = " ".join(current).split()[-OVERLAP_WORDS:]
            current = [" ".join(tail_words)]
    if current and (not chunks or len(" ".join(current).split()) > OVERLAP_WORDS):
        chunks.append(current)
    return ["\n".join(c) for c in chunks]


def main():
    records = []
    for path in sorted(CLEAN_DIR.glob("P*.md")):
        meta, body = read_page(path)
        for i, chunk in enumerate(split_into_chunks(body), start=1):
            records.append({
                "id": f"{meta['page_id']}-{i:02d}",
                "page_id": meta["page_id"],
                "title": meta["title"],
                "url": meta["url"],
                "source": meta["source"],
                "intent_groups": meta["intent_groups"],
                "content": f"{meta['title']}\n{chunk}",
            })

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    sizes = [len(r["content"].split()) for r in records]
    print(f"{len(records)} chunks from {len({r['page_id'] for r in records})} pages")
    print(f"Words per chunk: min {min(sizes)}, average {sum(sizes) // len(sizes)}, max {max(sizes)}")


if __name__ == "__main__":
    main()
