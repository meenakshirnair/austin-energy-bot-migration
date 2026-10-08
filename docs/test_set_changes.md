# Test set changes

## 2026-10-08: gold page corrections (after retrieval run 1)
Rule: a page is added to gold_page_ids only if its text contains the must_include facts.
Applied to the whole intent group, not just failing rows. Legacy bot rescored with the same key.

- T001 to T010 (Report Outage): added P02, P03, P34, P35. All contain 512-322-9100 and outage reporting steps.
- T011 to T015 (Check Outage Status): added P36 (How We Restore Power), which explains restoration estimates.
- T117, T118: added P45, which contains the 35 feet rule and 512-322-9100.

No queries, intents, or types were changed.
