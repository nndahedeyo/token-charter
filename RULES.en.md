# Token Charter editing rules

Token Charter is a ledger that anyone can propose changes to. A change goes live automatically only when it meets these rules. The rules decide the scores, not an operator.

## Five principles

| # | Principle | What it means |
| --- | --- | --- |
| 1 | **Verifiability** | Every score cites a source anyone can check. Changes without a source are not accepted |
| 2 | **Neutrality** | Write facts and sources only. No judgment words like "scam" or "best". Scores are not investment advice |
| 3 | **No original research** | Summarize only what sources say. No guesses, and no new conclusions built by combining sources |
| 4 | **Disclose interests** | Team members and large holders of a rated project say so in their proposal. They may propose, but they cannot approve |
| 5 | **Civility** | Discuss the content, not the person. When people disagree, the better source wins |

## Source priority

1. On-chain records (transactions, contracts)
2. Official project documents and governance vote results
3. Data aggregators (DefiLlama, Tokenomist, L2BEAT, etc.)
4. News reports confirmed by more than one outlet

Changes based only on social media posts or anonymous blogs are not accepted.

## How a change goes live

1. **Propose**: open a pull request on GitHub. See [CONTRIBUTING.md](CONTRIBUTING.md)
2. **Automatic checks**: scores are 0–2, every change has a source link, the format is valid
3. **Approval**: **2** contributors other than the proposer approve. Approvals from people who disclosed an interest don't count
4. **Automatic merge**: once checks and approvals pass, the change merges and the site rebuilds

There is no final review by an operator.

## When people disagree

- If the same item for the same token changes **3 or more times within 30 days**, it is marked "under discussion" and no further changes are accepted until the Issue reaches agreement
- Agreement goes to the side with the higher-priority source (see above)
- If that still doesn't settle it, the previous score stays, labeled "under discussion"

## What updates automatically

- **Revenue data** is pulled daily from DefiLlama's public data. It is shown for reference only. **Scores never change automatically**
- Only sourced, approved proposals change scores

## Changing these rules

Changes to these rules, the criteria (`data/criteria.json`) or the automation (`scripts/`, `.github/`) follow the same process but need **4** approvals, also checked automatically.
