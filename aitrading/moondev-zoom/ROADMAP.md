# Roadmap, dos and don'ts

Two parts: the **stages** (where you are, and what proves you've left a stage), and the
**rules** (the dos and don'ts that hold at every stage).

Read the don'ts first. At this point in your learning they are worth more than the dos,
because the dos only make you slower when you get them wrong, and the don'ts cost money.

---

## Part 1 — The four stages

The trap in learning from a livestream mentor is that stage 1 *feels* like stage 4. You
watch someone build a live trading bot, you build the same bot, it runs, and it is very
easy to conclude you have arrived. You haven't — you've reproduced a demo. Each stage
below has an **exit test** for exactly that reason. Don't self-promote on vibes; promote
when you pass the test.

### Stage 0 — Observer
*Goal: understand what you're even looking at.*

You can follow a stream without pausing. You know what a backtest is, what a fill is,
what slippage and fees do to a result, and why "it made 400% in the backtest" is not
information yet.

**Exit test:** watch a full session and write `01-notes.md` from memory before opening
the transcript, and have it be more than 60% right.

### Stage 1 — Typist
*Goal: your hands know the tools.*

You retype his builds rather than cloning them. You hit the errors he didn't hit, and
you fix them yourself. You are learning the API surface — `backtesting.py`, the exchange
client, the data layer — through your fingers.

**Exit test:** rebuild a session's bot from your own notes only, no video open, and get
it running end to end.

### Stage 2 — Tinkerer
*Goal: you can change it and predict what happens.*

You change a parameter, or a rule, and you say out loud what you expect to happen
*before* you run it. Then you run it. The gap between prediction and result is the
entire lesson. This is where most of the real learning is, and it's the stage people
skip because it produces nothing to show anyone.

**Exit test:** take one of his strategies, state a change and a predicted effect on
Sharpe / drawdown / trade count, run it, and be directionally right three times running.

### Stage 3 — Researcher
*Goal: his ideas go into your filter, not into your wallet.*

You stop rebuilding and start harvesting. Every session yields at most one idea, which
becomes a hypothesis, which goes through `backtest/walkforward.py` — in-sample selection,
out-of-sample scoring, efficiency ratio, degradation check — like anything else in your
repo. Most will die there. That is the system working, not the system failing.

**Exit test:** an idea sourced from a stream survives out-of-sample walk-forward with an
efficiency ratio you'd have accepted from your own idea. And separately: you have killed
at least five that didn't.

### Stage 4 — Operator
*Goal: forward-testing, still on paper.*

Paper-trade the survivors forward. Reconcile live paper fills against what the backtester
predicted — the parent repo's to-do list already has this as a gap. If predicted and
actual diverge, your backtest is wrong, and you'd rather learn that for free.

**Exit test:** 60+ days of forward paper results that match backtest expectations within
a band you defined in advance.

Real money is not stage 5 on this roadmap. It's a separate decision, made with a
position-sizing plan, a maximum loss you've written down, and ideally a conversation with
someone who is not a YouTuber and not an AI.

---

## Part 2 — Dos

**Do rebuild by typing.** Cloning his repo teaches you where his files are. Typing his
code teaches you what it does. The friction is the feature.

**Do keep one idea per session.** A four-hour stream contains maybe forty things. Carry
one into your repo. The other thirty-nine go in the notes and you let them go. Breadth
here is the enemy — you already have 81 bots in the field and the bottleneck isn't ideas.

**Do write notes from memory first.** Then correct against the transcript in a different
colour, so to speak. The corrections *are* the map of what you didn't understand.

**Do timebox it.** Two hours of active rebuild beats eight hours of watching, every time,
and it's not close.

**Do keep his code and your code in separate trees.** `~/moondev_bots` for reference,
your repo for what you actually believe. When they mix you lose track of what's been
through your own validation and what merely looks like it has.

**Do record the negative results.** "Tried it, it degraded out-of-sample, dropped it" is
a genuine result and it's the kind you'll otherwise forget and re-test in four months.

**Do read his repos, not just watch the streams.** The GitHub is the durable artifact —
the Hyperliquid data layer, the trading-battle harness, the RBI agent, the
`backtesting.py` scaffolding. A stream is a performance of the code; the repo is the code.

**Do assume the stream is the beginning of your work, not the end of it.**

---

## Part 3 — Don'ts

**Don't trade real money on a strategy you saw on a livestream.** This is the one that
matters. Not small, not "just to feel it", not with money you can afford to lose. A
demoed strategy has an in-sample result and no out-of-sample result, which means it has
no result. If you take one line from this whole folder, take this one.

**Don't treat a live demo as evidence.** He found the strategy and *then* showed it
working, on the data he found it in. That's the definition of in-sample. It's not
dishonest — it's what a livestream structurally can be — but it means the demo carries
approximately zero information about future performance.

**Don't confuse "the bot ran" with "the bot works."** A bot that executes cleanly and
loses money steadily is a working program and a broken strategy. Your success metric is
out-of-sample performance, never uptime.

**Don't let AI-written backtest code through unread.** The RBI agent generating
`backtesting.py` code from a video is a real accelerant, and lookahead bias is the
failure mode it will hand you: indicators computed on the full series before the split,
a signal that peeks at the bar it trades on, a fill at a price not available at decision
time, survivorship in the symbol list. These produce beautiful equity curves. Check the
split, check the shift, check the fill price, every single time.

**Don't skip the backtest because the idea is obviously good.** Obviously-good is where
overfitting lives. Your repo has an overfitting chart already; look at it when tempted.

**Don't commit secrets.** No `.env`, no keys in notebooks, no API keys in a pasted
traceback or a screenshot in your notes. Rotate anything you even suspect you've exposed.
Read-only keys where a read-only key will do.

**Don't run someone else's script against a funded account.** Not his, not a viewer's, not
one an AI wrote for you. Read it fully first, and run it against paper.

**Don't chase every new repo and agent.** He ships constantly. Following all of it is a
way to feel busy and learn nothing. Depth on one thing beats a survey of twelve.

**Don't measure progress in hours watched.** It's the easiest number to move and the
least connected to whether you can do anything. The dashboard tracks rebuilds and
surviving ideas instead, on purpose.

**Don't buy the upsell to skip the work.** Any paid tier, signal group, or bot bundle
still has to clear your own out-of-sample test before you believe it. Nothing purchased
is exempt from the filter.

**Don't do this alone with only AI for feedback.** Both a livestream and an AI assistant
will happily agree with you about a bad strategy. Your walk-forward module won't. Trust
that one.
