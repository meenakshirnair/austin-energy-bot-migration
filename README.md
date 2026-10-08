# Austin Energy Support Bot: Legacy to GenAI Migration

A portfolio project that treats a public utility help center like a client engagement.
I took an old style Q&A bot, rebuilt it as a GenAI agent, and measured both on the same 150 question exam.

*Independent demo. Not affiliated with or endorsed by Austin Energy or the City of Austin. Built only from public web pages.*

## Results

Both bots answered the same 150 test questions, written before the new bot existed.

| Metric | Legacy bot (best setting) | GenAI agent |
|---|---|---|
| **Overall pass rate** | 29% | **77%** |
| Real customer questions | 32% | **83%** |
| Out of scope handled correctly | 56% | **96%** |
| Safety (downed lines) | 40% | **100%** |
| Transactional (report outage, start or stop service, disputes) | 67% | **100%** |
| Clean paraphrases | 38% | **88%** |
| Spanish | 7% | 60% |
| Average latency | 1.5s | 2.5s |
| Model cost | n/a | about $0.68 per 1,000 questions |

Full table: [`results/summary.md`](results/summary.md). Every graded answer: [`results/graded.csv`](results/graded.csv).

Search alone, before any GPT:

| Search mode | Correct page in top 5 |
|---|---|
| Keyword (how the old bot matched) | 66% |
| Vector (meaning) | 90% |
| Hybrid (both) | 90% |

## The problem with the old bot

The legacy bot matches words, not meaning. Ask "my lights went out what now" and it answers with the street light card.

With no confidence cutoff it answers almost everything, but more than half its answers come from the wrong page. With a cutoff it stops embarrassing itself on off topic questions, but goes silent on most real ones. No setting fixes both. Right and wrong matches look the same to it.

## How the GenAI agent works

```
Customer message
  │
  ├─ Safety words? ──────────────► fixed safety message (no AI)
  │
  └─ AI classifier
        ├─ safety ───────────────► fixed safety message
        ├─ report outage, status,
        │  start/stop, dispute ───► scripted answer with verified facts
        ├─ out of scope ─────────► the right redirect (account login, 3-1-1, residential only)
        ├─ ambiguous ────────────► one clarifying question
        └─ informational ────────► hybrid search (top 5 passages) ─► GPT answer from sources only
                                                                   └─ not found ─► human handoff with summary
```

AI understands the message. Fixed text answers when the stakes are high. A phone number or a safety instruction should never be generated.

## What's in the repo

| Path | What it is |
|---|---|
| `docs/client_brief.md` | Users, 19 intent groups, scope, success metrics |
| `data/corpus.xlsx`, `data/scrape_list.csv` | 47 verified pages across austinenergy.com, coautilities.com, austintexas.gov |
| `data/clean/` | Scraped page text (about 37,000 words) |
| `data/legacy_kb.tsv` | Legacy knowledge base: 120 FAQ pairs + 50 written pairs |
| `data/chunks.jsonl` | 170 passages for the search index |
| `data/test_set.xlsx` | The 150 question exam with answer keys |
| `docs/test_set_changes.md` | Every change to the answer key, and why |
| `scripts/scrape.py` | Polite scraper with robots.txt check and quality flags |
| `scripts/build_legacy_kb.py` | Builds the legacy Q&A file |
| `scripts/query_legacy.py`, `run_legacy_eval.py` | Legacy bot client and exam run |
| `scripts/chunk_pages.py`, `build_search_index.py` | Chunking and Azure AI Search index |
| `scripts/search_kb.py`, `eval_retrieval.py` | Search and the search only benchmark |
| `scripts/answer.py` | Grounded answer from sources |
| `scripts/router.py` | Safety rule, classifier, flows, declines, handoff |
| `scripts/run_new_eval.py`, `grade.py` | GenAI exam run and grading of both bots |

## Stack

Azure AI Language custom question answering (legacy) · Azure AI Search, hybrid keyword and vector · Azure OpenAI GPT 4.1 mini and text embedding 3 small · Python

## How it was evaluated

* 150 questions across 20 intent groups: 60 paraphrases, 25 out of scope, 20 ambiguous, 15 typos, 15 transactional, 15 Spanish.
* Written before the new bot was built. Locked in git. Answer key fixes are logged in `docs/test_set_changes.md` and applied to both bots.
* The legacy bot is scored two ways, with and without a 0.5 confidence cutoff, so it is shown at its best.
* Answers graded by GPT 4.1 mini against each question's key facts. The grader does not know which bot wrote the answer. I reviewed all 34 GenAI failures and a random sample of passes. The grader was fair and slightly strict.

## Known issues (v1)

These are reported as is. Fixing them against this same test set would inflate the score.

1. **Over declines billing questions.** "Explain these charges on my bill" was treated as an account lookup. This also drags down Spanish.
2. **Rarely asks clarifying questions** (4 of 19). It usually answers the most likely meaning.
3. **"Disconnect notice" routed to the start/stop flow.** The classifier confused shut off with ending service.
4. **Safety rule is over cautious** on trees and a sparking outlet. Safe, but not ideal.
5. **Slower than the old bot.** 2.5s vs 1.5s.

## Findings about the source content

* **Conflicting text number.** Most pages say text OUT to **287846**. The Outage Map help page says **287246**. A GenAI bot repeats whatever it retrieves, so this is a content problem, not a model problem.
* **Duplicate content.** The same 8 outage FAQs appear word for word on two pages.
* **Vocabulary gap.** Customers say "moving". The site says "transfer" and never "moving".

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env needs: LANGUAGE_ENDPOINT, LANGUAGE_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY,
#             AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY
python scripts/router.py "my lights went out what now"
```

## Next

* Migration playbook: shadow mode, pilot percentage, rollback triggers, KB governance.
* v2 fixes for the known issues, tested on a fresh set of questions.
