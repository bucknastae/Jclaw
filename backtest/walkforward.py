"""Walk-forward analysis — stage 3 of the validation pipeline.

Stage 2 (``holdout_scan``) cuts history once and asks "did this survive the tail?".
Walk-forward asks the harder question: choose parameters on one period, trade the
*next untouched* period, roll forward, and repeat. A strategy that only worked
because one particular cut point flattered it fails here.

This module owns the window arithmetic, the selection rule and the scoring, and
knows nothing about how a backtest runs. You supply that as one adapter callable.

Wiring it up
------------
Write one function with this signature::

    def evaluate(data, params, *, score_start, score_end) -> Mapping[str, float]:
        ...

* ``data``      whatever you passed to :func:`walk_forward` — a DataFrame, a path,
                a loaded bar list. It is handed back untouched.
* ``params``    one dict from your grid.
* ``score_*``   the half-open scoring window ``[score_start, score_end)``.

The adapter must let the strategy **warm up on all history before**
``score_start`` and then report metrics for the scoring window alone — exactly
what ``run_suite --holdout`` already does. Getting this wrong is the classic
walk-forward bug: a 200-bar moving average scored from a cold start produces
garbage for the first 200 bars of every fold.

Return whatever metric keys your engine already emits. The names used across
this project are ``total_return_pct``, ``cagr_pct``, ``max_drawdown_pct``,
``sharpe``, ``sortino``, ``num_trades``, ``win_rate_pct``, ``profit_factor``
and ``exposure_pct``; only the key named by ``select_by`` and ``num_trades``
are required.

Against the existing runner that is roughly::

    from backtest.split import slice_range          # already in the repo

    def evaluate(df, params, *, score_start, score_end):
        return run_strategy(df, bot=BOT, params=params,
                            score_from=score_start, score_to=score_end)

    report = walk_forward(df, list(df.index), grid, evaluate,
                          train="24M", test="6M", min_trades=20)
    print(report.to_markdown())

Reading the output
------------------
``efficiency`` is walk-forward efficiency: mean out-of-sample return divided by
mean in-sample return. Below ~0.5 the in-sample number is mostly fitting noise.
``hit_rate`` is the share of folds that finished positive out-of-sample — with
few folds it is a weak signal, so the report prints the fold count beside it.
``param_churn`` is how often the selected parameters changed between folds; a
churn near 1.0 means the "best" settings are unstable and the strategy has no
single configuration worth trading.

Paper and historical only.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Callable, Iterable, Mapping, Sequence

__all__ = [
    "Window",
    "Fold",
    "WalkForwardReport",
    "make_windows",
    "walk_forward",
    "parse_span",
    "InsufficientHistory",
]


class InsufficientHistory(Exception):
    """Raised when the index is too short for even one train+test window."""


# --------------------------------------------------------------------------- #
# span arithmetic
# --------------------------------------------------------------------------- #

def parse_span(span: str | int) -> tuple[str, int]:
    """Normalise a span to ``(unit, amount)`` where unit is 'months' or 'bars'.

    >>> parse_span("18M")
    ('months', 18)
    >>> parse_span(500)
    ('bars', 500)
    """
    if isinstance(span, bool):  # bool is an int subclass; catch it before int
        raise TypeError(f"span must be a str or int, got {span!r}")
    if isinstance(span, int):
        if span <= 0:
            raise ValueError(f"bar span must be positive, got {span}")
        return ("bars", span)
    text = str(span).strip().upper()
    if not text:
        raise ValueError("span must not be empty")
    if text.endswith("M"):
        body = text[:-1]
        if not body.isdigit() or int(body) <= 0:
            raise ValueError(f"bad month span {span!r} — expected e.g. '18M'")
        return ("months", int(body))
    if text.endswith("Y"):
        body = text[:-1]
        if not body.isdigit() or int(body) <= 0:
            raise ValueError(f"bad year span {span!r} — expected e.g. '2Y'")
        return ("months", int(body) * 12)
    if text.isdigit() and int(text) > 0:
        return ("bars", int(text))
    raise ValueError(f"unrecognised span {span!r} — use '18M', '2Y' or a bar count")


def _add_months(stamp: Any, months: int) -> Any:
    """Add whole months to a date/datetime, clamping to the end of short months."""
    year = stamp.year + (stamp.month - 1 + months) // 12
    month = (stamp.month - 1 + months) % 12 + 1
    # 31 Jan + 1 month lands on 28/29 Feb, not on an invalid date.
    day = min(stamp.day, _days_in_month(year, month))
    return stamp.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 2:
        leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        return 29 if leap else 28
    return 30 if month in (4, 6, 9, 11) else 31


def _is_temporal(value: Any) -> bool:
    return isinstance(value, (date, datetime)) or (
        hasattr(value, "year") and hasattr(value, "month") and hasattr(value, "day")
    )


# --------------------------------------------------------------------------- #
# windows
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Window:
    """One train/test split. Both ranges are half-open: ``[start, end)``."""

    index: int
    train_start: Any
    train_end: Any
    test_start: Any
    test_end: Any

    @property
    def label(self) -> str:
        return f"fold {self.index + 1}"


def make_windows(
    timestamps: Sequence[Any],
    *,
    train: str | int,
    test: str | int,
    step: str | int | None = None,
    mode: str = "rolling",
) -> list[Window]:
    """Build the train/test windows that walk across ``timestamps``.

    ``timestamps`` must be sorted ascending. ``mode`` is ``"rolling"`` (fixed-length
    train window that slides) or ``"anchored"`` (train window always starts at the
    beginning and grows). ``step`` defaults to the test length, which gives
    non-overlapping test windows — the usual choice, because overlapping test
    windows reuse the same bars and inflate the fold count without adding evidence.
    """
    if mode not in ("rolling", "anchored"):
        raise ValueError(f"mode must be 'rolling' or 'anchored', got {mode!r}")
    stamps = list(timestamps)
    if len(stamps) < 2:
        raise InsufficientHistory(f"need at least 2 timestamps, got {len(stamps)}")
    if any(b < a for a, b in zip(stamps, stamps[1:])):
        raise ValueError("timestamps must be sorted ascending")

    train_unit, train_n = parse_span(train)
    test_unit, test_n = parse_span(test)
    step_unit, step_n = parse_span(step) if step is not None else (test_unit, test_n)

    temporal = _is_temporal(stamps[0])
    if not temporal and "months" in (train_unit, test_unit, step_unit):
        raise ValueError(
            "month spans need date-like timestamps; pass bar counts instead"
        )

    windows: list[Window] = []
    origin = stamps[0]
    last = stamps[-1]
    cursor = origin
    i = 0

    while True:
        if temporal:
            train_start = origin if mode == "anchored" else cursor
            train_end = (
                _add_months(cursor, train_n)
                if train_unit == "months"
                else _bar_offset(stamps, cursor, train_n)
            )
            test_end = (
                _add_months(train_end, test_n)
                if test_unit == "months"
                else _bar_offset(stamps, train_end, test_n)
            )
            if train_end is None or test_end is None or test_end > last:
                break
            windows.append(Window(i, train_start, train_end, train_end, test_end))
            cursor = (
                _add_months(cursor, step_n)
                if step_unit == "months"
                else _bar_offset(stamps, cursor, step_n)
            )
            if cursor is None:
                break
        else:
            train_start_i = 0 if mode == "anchored" else i * step_n
            train_end_i = train_start_i + train_n if mode == "rolling" else train_n + i * step_n
            test_end_i = train_end_i + test_n
            if test_end_i > len(stamps):
                break
            windows.append(
                Window(
                    i,
                    stamps[train_start_i],
                    stamps[train_end_i],
                    stamps[train_end_i],
                    stamps[test_end_i - 1],
                )
            )
        i += 1
        if i > 10_000:  # pathological step; refuse to spin
            raise ValueError("step too small — over 10,000 windows generated")

    if not windows:
        raise InsufficientHistory(
            f"history spans {origin} to {last}, which is not enough for a "
            f"{train} train window plus a {test} test window"
        )
    return windows


def _bar_offset(stamps: Sequence[Any], start: Any, n: int) -> Any | None:
    """The timestamp ``n`` bars after ``start``, or None if that runs off the end."""
    lo, hi = 0, len(stamps)
    while lo < hi:  # bisect_left without importing for a one-liner
        mid = (lo + hi) // 2
        if stamps[mid] < start:
            lo = mid + 1
        else:
            hi = mid
    target = lo + n
    return stamps[target] if target < len(stamps) else None


# --------------------------------------------------------------------------- #
# folds and report
# --------------------------------------------------------------------------- #

@dataclass
class Fold:
    window: Window
    params: Mapping[str, Any]
    train: Mapping[str, float]
    test: Mapping[str, float]
    considered: int = 0
    rejected_for_trades: int = 0

    @property
    def train_return(self) -> float:
        return float(self.train.get("total_return_pct", 0.0))

    @property
    def test_return(self) -> float:
        return float(self.test.get("total_return_pct", 0.0))


@dataclass
class WalkForwardReport:
    folds: list[Fold] = field(default_factory=list)
    select_by: str = "sortino"
    min_trades: int = 0
    mode: str = "rolling"

    # -- aggregates -------------------------------------------------------- #
    @property
    def n_folds(self) -> int:
        return len(self.folds)

    @property
    def mean_train_return(self) -> float:
        return statistics.fmean(f.train_return for f in self.folds) if self.folds else 0.0

    @property
    def mean_test_return(self) -> float:
        return statistics.fmean(f.test_return for f in self.folds) if self.folds else 0.0

    @property
    def median_test_return(self) -> float:
        return statistics.median(f.test_return for f in self.folds) if self.folds else 0.0

    @property
    def efficiency(self) -> float | None:
        """Out-of-sample return over in-sample return. None when in-sample is <= 0.

        Undefined rather than zero when the in-sample leg lost money: a ratio
        against a negative denominator flips sign and reads as a good score.
        """
        ins = self.mean_train_return
        if ins <= 0:
            return None
        return self.mean_test_return / ins

    @property
    def hit_rate(self) -> float:
        if not self.folds:
            return 0.0
        return sum(1 for f in self.folds if f.test_return > 0) / len(self.folds)

    @property
    def worst_drawdown(self) -> float:
        vals = [float(f.test.get("max_drawdown_pct", 0.0)) for f in self.folds]
        return min(vals) if vals else 0.0

    @property
    def total_test_trades(self) -> int:
        return sum(int(f.test.get("num_trades", 0)) for f in self.folds)

    @property
    def param_churn(self) -> float:
        """Share of fold boundaries where the selected parameters changed."""
        if len(self.folds) < 2:
            return 0.0
        changes = sum(
            1
            for a, b in zip(self.folds, self.folds[1:])
            if dict(a.params) != dict(b.params)
        )
        return changes / (len(self.folds) - 1)

    def passed(
        self,
        *,
        min_hit_rate: float = 0.6,
        min_efficiency: float = 0.5,
        max_drawdown: float = -60.0,
        min_total_trades: int = 20,
    ) -> tuple[bool, list[str]]:
        """Apply a fixed bar. Returns ``(ok, reasons_it_failed)``."""
        reasons: list[str] = []
        if self.n_folds == 0:
            return False, ["no folds were run"]
        if self.hit_rate < min_hit_rate:
            reasons.append(
                f"only {self.hit_rate:.0%} of {self.n_folds} folds finished positive "
                f"(needs {min_hit_rate:.0%})"
            )
        eff = self.efficiency
        if eff is None:
            reasons.append("in-sample legs lost money, so efficiency is undefined")
        elif eff < min_efficiency:
            reasons.append(f"walk-forward efficiency {eff:.2f} (needs {min_efficiency:.2f})")
        if self.worst_drawdown < max_drawdown:
            reasons.append(
                f"worst out-of-sample drawdown {self.worst_drawdown:.1f}% "
                f"(limit {max_drawdown:.1f}%)"
            )
        if self.total_test_trades < min_total_trades:
            reasons.append(
                f"only {self.total_test_trades} out-of-sample trades "
                f"(needs {min_total_trades}) — not enough to judge"
            )
        return (not reasons), reasons

    # -- output ------------------------------------------------------------ #
    def to_markdown(self, name: str = "strategy") -> str:
        ok, reasons = self.passed()
        eff = self.efficiency
        lines = [
            f"# Walk-forward — {name}",
            "",
            f"- mode: **{self.mode}**, selected on **{self.select_by}**, "
            f"min trades in-sample **{self.min_trades}**",
            f"- folds: **{self.n_folds}**",
            f"- mean return: in-sample **{self.mean_train_return:+.1f}%**, "
            f"out-of-sample **{self.mean_test_return:+.1f}%** "
            f"(median {self.median_test_return:+.1f}%)",
            f"- walk-forward efficiency: **{'n/a' if eff is None else f'{eff:.2f}'}**",
            f"- folds finishing positive: **{self.hit_rate:.0%}**",
            f"- worst out-of-sample drawdown: **{self.worst_drawdown:.1f}%**",
            f"- out-of-sample trades: **{self.total_test_trades}**",
            f"- parameter churn: **{self.param_churn:.0%}**",
            "",
            f"**Verdict: {'PASS' if ok else 'FAIL'}**",
        ]
        for r in reasons:
            lines.append(f"- {r}")
        lines += [
            "",
            "| fold | test window | params | IS ret | OOS ret | OOS DD | trades |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
        for f in self.folds:
            params = ", ".join(f"{k}={v}" for k, v in sorted(f.params.items())) or "—"
            lines.append(
                f"| {f.window.index + 1} "
                f"| {f.window.test_start} → {f.window.test_end} "
                f"| {params} "
                f"| {f.train_return:+.1f}% "
                f"| {f.test_return:+.1f}% "
                f"| {float(f.test.get('max_drawdown_pct', 0.0)):.1f}% "
                f"| {int(f.test.get('num_trades', 0))} |"
            )
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #

Evaluator = Callable[..., Mapping[str, float]]


def walk_forward(
    data: Any,
    timestamps: Sequence[Any],
    param_grid: Iterable[Mapping[str, Any]],
    evaluate: Evaluator,
    *,
    train: str | int = "24M",
    test: str | int = "6M",
    step: str | int | None = None,
    mode: str = "rolling",
    select_by: str = "sortino",
    min_trades: int = 0,
    on_fold: Callable[[Fold], None] | None = None,
) -> WalkForwardReport:
    """Run the walk-forward and return the report.

    For each window the grid is scored on the train range, the best configuration
    by ``select_by`` (subject to ``min_trades``) is chosen, and *that* configuration
    alone is then scored on the test range. The test range is never consulted
    during selection — that is the whole point of the exercise.

    Raises :class:`InsufficientHistory` when the data cannot fit one window, and
    :class:`ValueError` when the grid is empty or ``select_by`` is missing from the
    metrics the adapter returns.
    """
    grid = [dict(p) for p in param_grid]
    if not grid:
        raise ValueError("param_grid is empty — pass at least one configuration")

    windows = make_windows(timestamps, train=train, test=test, step=step, mode=mode)
    report = WalkForwardReport(select_by=select_by, min_trades=min_trades, mode=mode)

    for window in windows:
        scored: list[tuple[float, Mapping[str, Any], Mapping[str, float]]] = []
        rejected = 0
        for params in grid:
            metrics = evaluate(
                data, params, score_start=window.train_start, score_end=window.train_end
            )
            if select_by not in metrics:
                raise ValueError(
                    f"adapter returned no {select_by!r} key; got {sorted(metrics)}"
                )
            if int(metrics.get("num_trades", 0)) < min_trades:
                rejected += 1
                continue
            scored.append((float(metrics[select_by]), params, metrics))

        if not scored:
            # Every configuration was too quiet in-sample. That is a result, not an
            # error: record the fold as skipped rather than silently dropping it.
            continue

        # max() keeps the first of equal scores, so a stable grid gives a stable pick.
        best_score, best_params, best_train = max(scored, key=lambda row: row[0])
        test_metrics = evaluate(
            data, best_params, score_start=window.test_start, score_end=window.test_end
        )
        fold = Fold(
            window=window,
            params=best_params,
            train=best_train,
            test=test_metrics,
            considered=len(grid),
            rejected_for_trades=rejected,
        )
        report.folds.append(fold)
        if on_fold is not None:
            on_fold(fold)

    return report
