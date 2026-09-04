# backtest/

## `walkforward.py` — stage 3 of the validation pipeline

Stage 2 (`holdout_scan`) cuts history once. Walk-forward chooses parameters on one
period, trades the **next untouched** period, rolls forward, and repeats — so a
strategy that only worked because one cut point flattered it fails here.

The module owns the window arithmetic, the selection rule and the scoring. It knows
nothing about how a backtest runs; you supply that as one adapter:

```python
def evaluate(data, params, *, score_start, score_end) -> Mapping[str, float]:
    """Warm up on all history before score_start, report metrics for [score_start, score_end)."""
```

That warm-up requirement is the one thing to get right — it is the same contract
`run_suite --holdout` already honours. A 200-bar moving average scored from a cold
start produces garbage for the first 200 bars of every fold.

```python
from backtest.walkforward import walk_forward

report = walk_forward(df, list(df.index), grid, evaluate,
                      train="24M", test="6M", mode="rolling", min_trades=20)
print(report.to_markdown("roc_bot"))
ok, reasons = report.passed()
```

### What the report tells you

| Field | Read it as |
| --- | --- |
| `efficiency` | Out-of-sample return over in-sample return. Below ~0.5 the in-sample number is mostly fitting noise. `None` when the in-sample leg lost money, because a ratio over a negative denominator flips sign and reads as a good score. |
| `hit_rate` | Share of folds that finished positive. Weak with few folds, so the fold count prints beside it. |
| `param_churn` | How often the selected parameters changed between folds. Near 1.0 means there is no single configuration worth trading. |
| `worst_drawdown` | The deepest out-of-sample drawdown across all folds, not the last one. |

`passed()` applies a fixed bar — hit rate, efficiency, drawdown and a total
out-of-sample trade count — and returns the reasons it failed. Point the gauntlet at
that rather than eyeballing the table.

Both window modes are supported: `rolling` (fixed-length train window that slides)
and `anchored` (train window grows from a fixed origin). Spans take calendar months
(`"18M"`, `"2Y"`) or bar counts (`500`).

No third-party dependencies; `python3 -m pytest tests/test_walkforward.py` covers the
window arithmetic, the selection rule, and the guarantee that the test window never
leaks into selection.
