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
3. **Approval**: approvers review on GitHub with "Approve" or "Request changes" (see "Approval" below)
4. **Automatic merge**: once checks and approvals pass, the change merges, and the site rebuilds by the next day

There is no final review by an operator.

## Approval

**Who can approve** is decided automatically by [APPROVERS.md](APPROVERS.md), not by anyone's appointment: people with **3 or more merged proposals** here whose GitHub account is at least **90 days** old, plus the founding approvers listed there.

These don't count: the proposer and anyone who added commits to the proposal; people listed under "Removed"; approvals given to an earlier version of the proposal (any new commit resets approvals). Team members and large holders of a rated project must neither approve nor object (principle 4). A machine can't detect this, so people who break it get listed under "Removed".

| Kind of change | Merges when |
| --- | --- |
| Normal (scores, summaries, sources, adding a token) | approvals exceed objections by **2 or more**, or one approval stands for **14 days** with no objection from an approver |
| Rules and system (see "Changing these rules") | approvals exceed objections by **4 or more**. The 14-day path doesn't apply |

An objection stands until its author approves or dismisses it. Approvals and objections from non-approvers are ignored, so throwaway accounts can neither push nor block a change. The 14-day path exists so proposals don't stall while there are few approvers; a single objection turns it off.

**As an approver**: open the sources and check the proposal says only what they say (principles 1 and 3), then Approve or Request changes with your reason. Watch the repository for pull requests so you see new ones.

## When people disagree

- If the same item for the same token changes **3 or more times within 30 days**, it is marked "under discussion" and no further changes are accepted until the Issue reaches agreement
- Agreement goes to the side with the higher-priority source (see above)
- If that still doesn't settle it, the previous score stays, labeled "under discussion"

## What updates automatically

- **Revenue data** is pulled daily from DefiLlama's public data. It is shown for reference only. **Scores never change automatically**
- Only sourced, approved proposals change scores

## Changing these rules

Changes to these rules, the approver list (`APPROVERS.md`), the criteria (`data/criteria.json`), the page (`site/`), the automation (`scripts/`, `.github/`), `CONTRIBUTING.md` or the license follow the same process, but approvals must exceed objections by **4 or more**, checked automatically. Removing or renaming a token is treated the same way.

## Limits of this system

- **The repository owner can change GitHub's settings**, and could bypass these rules by doing so. Any such change still leaves a public record on GitHub
- **At first there are few approvers, so the founding approvers carry more weight.** That weight shrinks as approvers grow
- **A machine can't detect hidden interests.** If you find one, propose adding that person to "Removed", with sources
