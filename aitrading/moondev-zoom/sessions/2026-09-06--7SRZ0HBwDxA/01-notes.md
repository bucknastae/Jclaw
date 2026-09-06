# Notes

> **Nothing here is from the video yet.** See `00-source.md` — the stream could not be
> reached. The `[BACKGROUND]` block is public context about how Moon Dev works generally,
> to give you something to take notes *against*. Delete or correct it once you've watched.

## From memory

**What was he trying to build?**

**How did he approach it?**

**What did he actually use?** (libraries, APIs, data sources, models)

**Where did he get stuck, and what did he do about it?**

**What did he say that I disagreed with or didn't follow?**

## Corrections after the transcript

---

## `[BACKGROUND]` — what to expect, from public sources

Not from this stream. Verify every line of it against what you actually watch.

**Format.** His live sessions typically run 4–8 hours and are unscripted — the pitch is
"a day in the life of a full-time algo trader" rather than a polished tutorial. Expect
long stretches of debugging. Those stretches are usually the most valuable part and the
part most viewers skip.

**The RBI framework** — Research, Backtest, Implement — is his organising idea and the
thing most worth copying:

- *Research*: pull strategies from anywhere — videos, PDFs, papers, ideas.
- *Backtest*: test each one repeatedly, across variations, before believing any of it.
- *Implement*: only what survives.

He has automated this as an "RBI agent": you hand it a YouTube URL, a PDF or a plain
text idea, an LLM extracts the strategy logic, generates `backtesting.py`-compatible
code, and runs it. Useful, and the exact place lookahead bias sneaks in — see the
don'ts in `../../ROADMAP.md`.

**Recurring themes:** AI agents for trading (his framework orchestrates a large number
of specialised agents), removing emotion and discretion from execution, and building in
public with everything open-sourced.

**His GitHub** (`github.com/moondevonyt`, ~27 public repos) is the durable version of
the streams. The ones most relevant to where you are:

| Repo | Why it matters to you |
|---|---|
| `Moon-Dev-Code` | Aggregated code from the YouTube projects — start here to find a stream's code |
| `Moon-Dev-AI-Trading-Battles` | Six frontier models each trading a real $100 Hyperliquid account |
| `Hyperliquid-Data-Layer-API` | Data infrastructure — relevant if you ever move past SOL/USDT |
| `Harvard-Algorithmic-Trading-with-AI` | The closest thing to a structured curriculum he has |
| `Trading-View-MCP-for-AI-by-Moon-Dev` | TradingView MCP, if you want charts wired into an agent |

Note that his live work leans toward Hyperliquid, Solana and prediction markets, while
your repo is SOL/USDT with a 12-month held-out window. Ideas port across venues; results
absolutely do not.

---

## RBI classification

Which stage was this stream actually about?

- [ ] **R** — a strategy or an idea
- [ ] **B** — backtesting method, validation, tooling
- [ ] **I** — execution, venue mechanics, live infrastructure

## Claims that need testing

| # | Claim | Testable? | Test it? |
|---|---|---|---|
| 1 | | | |

## Open questions

- [ ] Does this stream have code in `Moon-Dev-Code`, or its own repo?
- [ ] Which venue is he on, and does anything here port to SOL/USDT?
