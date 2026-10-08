| Metric | Legacy (no cutoff) | Legacy (0.5 cutoff) | GenAI agent |
|---|---|---|---|
| **Overall (150)** | 40/150 (27%) | 44/150 (29%) | 116/150 (77%) |
| In-scope answers (answer, route, safety) | 34/106 (32%) | 29/106 (27%) | 88/106 (83%) |
| Ambiguous (clarify) | 3/19 (16%) | 1/19 (5%) | 4/19 (21%) |
| Out of scope (decline) | 3/25 (12%) | 14/25 (56%) | 24/25 (96%) |
| Safety | 2/5 (40%) | 0/5 (0%) | 5/5 (100%) |
| Type: Clean paraphrase | 23/60 (38%) | 15/60 (25%) | 53/60 (88%) |
| Type: Typos / slang | 4/15 (27%) | 3/15 (20%) | 10/15 (67%) |
| Type: Spanish | 1/15 (7%) | 1/15 (7%) | 9/15 (60%) |
| Type: Transactional | 6/15 (40%) | 10/15 (67%) | 15/15 (100%) |
| Type: Ambiguous | 3/20 (15%) | 1/20 (5%) | 5/20 (25%) |
| Type: Out-of-scope | 3/25 (12%) | 14/25 (56%) | 24/25 (96%) |

Average latency: legacy 1.49s, GenAI agent 2.53s
GenAI agent model cost: about $0.68 per 1,000 questions (gpt-4.1-mini at $0.40 / $1.60 per 1M tokens; embeddings and search not included)
