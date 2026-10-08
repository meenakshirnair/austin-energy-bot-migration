import json
import sys
import time

from search_kb import openai_client, search_kb

CHAT_MODEL = "gpt-4.1-mini"
TOP_K = 5
FALLBACK = "I don't have that information. Please call City of Austin Utilities Customer Care at 512-494-9400."

SYSTEM_PROMPT = """You are the Austin Energy residential customer help assistant.

Rules:
1. Answer ONLY from the numbered sources provided. Never use outside knowledge.
2. After each fact, cite its source like [S1] or [S2].
3. Copy phone numbers, text codes, dollar amounts, and dates exactly as written in the sources.
4. If the sources do not contain the answer, set "answerable" to false and use this exact answer:
   "I don't have that information. Please call City of Austin Utilities Customer Care at 512-494-9400."
5. If two sources disagree, say so and give both versions with their citations. Do not pick one.
6. Reply in the same language the customer wrote in.
7. Keep answers short: 2 to 4 sentences, plain words, no marketing language.
8. Never ask for or repeat account numbers, card numbers, or other personal details.

Return JSON only:
{"answer": "...", "answerable": true or false, "sources_used": ["S1", "S3"]}"""


def format_sources(hits):
    blocks = []
    for i, hit in enumerate(hits, start=1):
        blocks.append(f"[S{i}] {hit['title']} ({hit['url']})\n{hit['content']}")
    return "\n\n".join(blocks)


def answer_question(question):
    start = time.perf_counter()
    hits = search_kb(question, mode="hybrid", top=TOP_K)
    response = openai_client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Sources:\n\n{format_sources(hits)}\n\nCustomer question: {question}"},
        ],
    )
    latency = time.perf_counter() - start

    try:
        result = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        result = {"answer": FALLBACK, "answerable": False, "sources_used": []}

    cited = []
    for label in result.get("sources_used", []):
        index = int(label.strip("S[] ")) - 1 if label.strip("S[] ").isdigit() else -1
        if 0 <= index < len(hits):
            cited.append(hits[index]["page_id"])

    return {
        "answer": result.get("answer", FALLBACK),
        "answerable": bool(result.get("answerable", False)),
        "cited_pages": sorted(set(cited)),
        "retrieved_pages": [h["page_id"] for h in hits],
        "latency_s": round(latency, 2),
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:])
    result = answer_question(question)
    print(result["answer"])
    print(f"\nanswerable: {result['answerable']}  cited: {result['cited_pages']}  "
          f"retrieved: {result['retrieved_pages']}")
    print(f"latency: {result['latency_s']}s  tokens: {result['input_tokens']} in / {result['output_tokens']} out")
