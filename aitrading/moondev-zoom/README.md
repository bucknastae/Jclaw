# Moon Dev Zoom

Where every Moon Dev livestream / zoom session gets turned into something you can
actually use. One folder per session, always the same four files, so session #40
looks exactly like session #1 and the dashboard can read all of them the same way.

`../../dashboard.html` is the **project** dashboard — how the SOL research is doing.
`dashboard.html` in this folder is the **learning** dashboard — how *you* are doing.
Two different questions, deliberately two different pages.

## The one idea that makes this work

Moon Dev's material is a *strategy source*. Your Jclaw repo is a *strategy filter*.
They are two different stages of the same pipeline and you should never let them
touch:

| RBI stage | Who does it | Where it lives |
|---|---|---|
| **R**esearch — where does an idea come from | Moon Dev streams, his repos, papers | `sessions/*/01-notes.md` |
| **B**acktest — does the idea survive contact with data | You | `~/aitrading`, `backtest/walkforward.py` |
| **I**mplement — does it survive contact with a live venue | You, much later | not yet, and that is correct |

RBI (Research → Backtest → Implement) is his own framing, and it is the single most
useful thing to copy from him — more useful than any individual bot. A livestream can
only ever show you R. **Every demo you watch is in-sample by construction**: he found
the strategy, then showed it working, on the data where he found it. That is not a
result, it is a hypothesis. Your repo already has the machinery to test hypotheses
properly — walk-forward, out-of-sample scoring, an efficiency ratio, a degradation
check. So the division of labour is clean: take his ideas, run them through your
filter, believe only what comes out the far end.

If you internalise one thing: **you are not trying to reproduce his results, you are
trying to reproduce his process.**

## The loop, per session

Budget roughly 2× the stream length. A 4-hour stream is a ~8-hour commitment if you
do it properly, which is why you do fewer of them, properly, instead of all of them,
passively.

1. **Capture** — get the transcript before anything else (see `_template/00-source.md`).
   Livestreams get unlisted, trimmed, or taken down. The transcript is the only part
   you control.
2. **Watch once at speed, no laptop.** Just get the shape of it. What was he trying to
   do, what did he actually do, where did he get stuck.
3. **Notes** (`01-notes.md`) — written from memory *first*, then corrected against the
   transcript. What you can't recall unaided, you didn't learn.
4. **Rebuild** (`02-rebuild.md`) — retype it. Not copy-paste, not clone. Typing is where
   you find the twelve things you didn't actually understand.
5. **Review** (`03-review.md`) — what broke, what you'd do differently, and the single
   idea worth carrying into your own repo. One idea. Not eight.
6. **Tick the dashboard.** Update the skills matrix, log the session.

Steps 4 and 5 are the whole point. Steps 1–3 are logistics. It is extremely easy to
do 1–3 forever and feel productive; the dashboard exists specifically to make that
visible to you.

## Layout

```
moondev-zoom/
├── README.md                   this file
├── ROADMAP.md                  dos, don'ts, and the four learning stages
├── dashboard.html              learning progress — open it, no build step
├── _template/                  copy this whole folder for each new session
│   ├── 00-source.md            link, metadata, transcript, capture status
│   ├── 01-notes.md             what he did and why
│   ├── 02-rebuild.md           your reimplementation log
│   └── 03-review.md            what you actually learned
└── sessions/
    └── YYYY-MM-DD--<videoid>/  one per session, same four files
```

Starting a new session is one command:

```sh
cp -r _template "sessions/$(date +%F)--<videoid>"
```

## Ground rules

Copied here from `ROADMAP.md` because they matter more than anything else in this folder.

- **Paper and historical only.** Same rule as the parent repo. No wallet, no keys, no
  exchange orders — not for a strategy you watched someone demo, not ever, not "just
  small to test it".
- **Never commit a key.** Not in a notebook, not in a screenshot, not in a pasted
  traceback. His repos use `.env`; yours should too, and `.env` stays gitignored.
- **Read every line of AI-generated backtest code.** The RBI agent writes
  `backtesting.py` code from a video. It is genuinely useful and it will genuinely
  introduce lookahead bias if you don't check. See the don'ts in `ROADMAP.md`.
