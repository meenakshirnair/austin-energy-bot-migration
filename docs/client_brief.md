# Client Brief: Austin Energy Residential Support Bot Migration

*Independent portfolio demo. Not affiliated with or endorsed by Austin Energy or the City of Austin. Built only from publicly available web pages, which are credited in the README.*

**Prepared by:** Meenakshi Nair
**Status:** Draft v0.1 (October 2026)

---

## 1. The problem

Residential customers have questions about outages, bills, rebates and service changes. The answers exist, but they are spread across two websites (austinenergy.com and coautilities.com) and many separate FAQ pages. A customer who can't find an answer calls customer service or 3-1-1.

The current state, modeled for this project, is a classic Q&A bot: a fixed list of questions and answers, matched by keyword similarity. It works when people ask questions the way they were written. It breaks when they phrase them differently, ask in Spanish, or ask something the list never covered.

**Goal:** migrate to a GenAI agent that answers from the real help content, routes "do something for me" requests to the right place, and hands off to a human when it isn't sure. Then prove with numbers whether it is actually better.

## 2. Users

| User | What they need |
|---|---|
| Customer during an outage | What to do, how to report it, and when power is coming back. Often on a phone, often stressed |
| Customer with a high or confusing bill | What the line items mean, payment options, and whether they qualify for help |
| Customer moving in or out | Start, stop or transfer service |
| Customer looking to save money | Rebates, GreenChoice, solar, EV charging |
| Spanish-speaking customer | Same needs, in Spanish. The source site is English only (machine translation) |

## 3. Intents

19 intent groups in scope, plus out of scope. These labels match the Intent Group
column in data/corpus.xlsx and the test set plan.

**Informational: answered from help content (RAG)**

| # | Intent group | Example user message |
|---|---|---|
| 1 | Safety | "power's out what do i do" |
| 2 | Outage Alerts | "how do I get texts when there's an outage" |
| 3 | Understand My Bill | "what is the power supply adjustment on my bill" |
| 4 | Payment Options | "can I pay by phone" |
| 5 | Payment Arrangement | "can i get more time to pay this month" |
| 6 | Collections | "got a disconnection notice what do i do" |
| 7 | CAP | "I can't afford my bill, is there help" |
| 8 | Weatherization | "free home weatherization program" |
| 9 | Rebates | "do you give rebates for a new AC" |
| 10 | GreenChoice | "how do I switch to wind power" |
| 11 | Home Solar | "does Austin Energy buy back solar power" |
| 12 | EV Programs | "rebate for home EV charger" |
| 13 | Scam Awareness | "someone called saying they'll cut my power today" |
| 14 | Tree Trimming | "tree branches touching the power line in my yard" |

**Transactional: scripted flow, not free text**

| # | Intent group | Flow ends with |
|---|---|---|
| 15 | Report Outage | Outage reporting link, text code and outage phone line |
| 16 | Check Outage Status | Outage map link. The bot never guesses a restoration time |
| 17 | Start/Stop/Transfer Service | Steps and link to the utilities portal |
| 18 | Bill Dispute | Steps, bill dispute page and offer of human handoff |

**Safety critical**

| # | Intent group | Behavior |
|---|---|---|
| 19 | Downed Power Lines | Skips everything else. Returns the emergency message and outage phone line first. Mentions of sparks or fire do the same |

**Always on**

- **Talk to a person:** handoff with a short conversation summary.
- **Collections and Bill Dispute** always offer a human, because the customer may be stressed.
- **Out of scope:** declined politely and pointed to the right place (see Section 4).
  
## 4. Out of scope

The bot says so politely and points to the right place:

- Commercial, multifamily-owner and contractor topics (rates, construction, pole attachments)
- Anything account-specific: balances, payment history, usage. The bot has no account access by design
- Corporate topics: RFPs, reports, careers, news
- Other City of Austin services (water, trash, permits). Point to 3-1-1

## 5. How success is measured

Both bots are tested on the **same 150-query test set**, written before the new bot is built.

| Metric | Definition |
|---|---|
| Answer accuracy | % of in-scope questions answered correctly |
| Containment | % of conversations resolved without a human |
| Out-of-scope refusal | % of out-of-scope questions correctly declined |
| Handoff accuracy | % of handoffs that should have happened, and none that shouldn't have |
| Spanish accuracy | Answer accuracy on the 15 Spanish queries only |
| Latency | Average seconds per answer |
| Cost | Approximate cost per 1,000 queries |

Results are reported honestly, including where the new bot does worse.

## 6. Constraints

- Public pages only. No customer data, no logins, no PII.
- Residential content only. Roughly 40 to 60 pages.
- Source content is English. Spanish is handled by the GenAI agent across languages, not by a translated knowledge base.
- Budget: Azure for Students credit. Target under $30 total.

## 7. Deliverables

1. This brief
2. Legacy Q&A bot (baseline)
3. 150-query test set
4. GenAI agent with routing, guardrails and handoff
5. Before/after evaluation report
6. Migration playbook (cutover plan, risks, KB governance)
7. README, demo video and write-up

## 8. Data sources

- austinenergy.com: residential, outages, rates, rebates, green power, safety and FAQ pages
- coautilities.com: start/stop service, billing, payments, bill disputes, Customer Assistance Program
