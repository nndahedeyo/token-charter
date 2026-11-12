# Token Charter

[日本語](README.md) · Live site: [English](https://nndahedeyo.github.io/token-charter/en/) / [日本語](https://nndahedeyo.github.io/token-charter/)

A public ledger that scores whether crypto projects **keep their promises, and whether anything makes them keep them**, across 10 items. Like Wikipedia, anyone can propose a sourced correction, and only changes that meet fixed rules go live, automatically.

## Why

In stock markets, exchanges, regulators and bond trustees make companies keep their promises. Crypto has no one in that role. Buybacks get cut, revenue-sharing switches never trigger, votes have no date, and large token reserves sit with no schedule.

Token Charter measures promises and their delivery with one yardstick, and publishes the result so anyone can check it.

## What it measures

| Group | Items |
| --- | --- |
| Issuer (6) | 1. Holder-return commitment 2. Delivery on commitments 3. Insider selling rules 4. Regular reporting 5. Penalties and collateral 6. Accountability |
| Mechanism (4) | 7. Fixed supply schedule 8. On-chain verifiability 9. Intervention by a few 10. Rule-change process |

Each item scores 0–2, converted to a 100-point scale. Tokens with no issuer (such as BTC) are scored on the 4 mechanism items only. Full criteria, in Japanese and English, are in [data/criteria.json](data/criteria.json).

**Scores are not investment advice.** They measure the reliability of promises, not price or prospects.

## Who decides the scores

The [editing rules (RULES.en.md)](RULES.en.md) do, not an operator.

1. Anyone can propose a correction with a source
2. Automatic checks verify format and sources
3. Approvers (decided automatically by track record) approve, and the change merges automatically ([RULES.en.md](RULES.en.md))
4. Revenue data is pulled daily for reference. Scores never change automatically

## Take part

- Found an error? [Open a correction](../../issues/new?template=correction.yml) with a source URL
- Want to change a score? See [CONTRIBUTING.md](CONTRIBUTING.md)
- Setting up this repository? See [SETUP.md](SETUP.md)

## License

- Data and text (`data/`, `*.md`): [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (same as Wikipedia)
- Code (`scripts/`, `site/`, `.github/`): MIT
