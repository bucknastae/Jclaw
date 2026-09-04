# Jclaw

Project dashboard for the SOL / crypto strategy-research work.

`dashboard.html` is a self-contained page — open it in a browser, no build step, no
dependencies. It has six sections in a left-hand rail:

| Section | What's in it |
|---|---|
| Overview | Headline numbers and the state of each workstream |
| What we built | Full inventory across all seven workstreams |
| Progress | The six-stage validation pipeline, plus the overfitting and survivorship charts |
| Bot field | All 81 price-testable bots, sortable and filterable |
| To-do | Twelve items in priority order, with checkboxes |
| What's next | Eight suggested directions |

Every figure comes from the SEPA matrix run generated 2026-09-04, held out on the
12 months ending 2025-09-02: one symbol (SOL/USDT), 0.10% fee and 0.05% slippage
per side, $10,000 notional start.

**Paper and historical only.** No wallet, no keys, no exchange orders anywhere.

## Note on where the code lives

As of this commit the backtester (`~/aitrading`), the bot library (`~/moondev_bots`)
and the reference corpus (`~/aitrading/moondev-repos`) exist only on one machine and
have never been pushed. Getting them into this repository is item one on the to-do list.
