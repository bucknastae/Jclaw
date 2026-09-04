"""Tests for backtest.walkforward.

The adapter under test is deterministic and synthetic, so every assertion here is
about the walk-forward machinery — window arithmetic, the selection rule, and the
guarantee that the test window never leaks into selection.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backtest.walkforward import (  # noqa: E402
    InsufficientHistory,
    WalkForwardReport,
    Window,
    make_windows,
    parse_span,
    walk_forward,
)


def daily(start: date, n: int) -> list[date]:
    from datetime import timedelta

    return [start + timedelta(days=i) for i in range(n)]


# --------------------------------------------------------------------------- #
# spans
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "raw,expected",
    [("18M", ("months", 18)), ("2Y", ("months", 24)), ("6m", ("months", 6)),
     (500, ("bars", 500)), ("500", ("bars", 500))],
)
def test_parse_span(raw, expected):
    assert parse_span(raw) == expected


@pytest.mark.parametrize("bad", ["", "M", "0M", "-3M", "banana", 0, -5, True])
def test_parse_span_rejects_nonsense(bad):
    with pytest.raises((ValueError, TypeError)):
        parse_span(bad)


# --------------------------------------------------------------------------- #
# windows
# --------------------------------------------------------------------------- #

def test_rolling_windows_do_not_overlap_in_test():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    ws = make_windows(stamps, train="12M", test="6M")
    assert len(ws) >= 3
    for a, b in zip(ws, ws[1:]):
        assert a.test_end <= b.test_start, "test windows must not overlap"
    for w in ws:
        assert w.train_end == w.test_start, "test must start where train ends"
        assert w.train_start < w.train_end < w.test_end


def test_anchored_windows_grow_from_a_fixed_origin():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    ws = make_windows(stamps, train="12M", test="6M", mode="anchored")
    assert len({w.train_start for w in ws}) == 1
    assert ws[0].train_start == stamps[0]
    lengths = [(w.train_end - w.train_start).days for w in ws]
    assert lengths == sorted(lengths) and lengths[-1] > lengths[0]


def test_bar_count_windows():
    stamps = list(range(1000))
    ws = make_windows(stamps, train=200, test=50)
    assert ws[0].train_start == 0 and ws[0].train_end == 200
    assert ws[1].train_start == 50 and ws[1].train_end == 250
    assert all(w.test_end > w.test_start for w in ws)


def test_month_spans_need_dates():
    with pytest.raises(ValueError, match="month spans"):
        make_windows(list(range(500)), train="12M", test="3M")


def test_short_history_is_an_explicit_error():
    with pytest.raises(InsufficientHistory):
        make_windows(daily(date(2020, 1, 1), 40), train="12M", test="6M")


def test_unsorted_timestamps_rejected():
    with pytest.raises(ValueError, match="sorted"):
        make_windows([date(2020, 3, 1), date(2020, 1, 1)], train=1, test=1)


def test_month_arithmetic_clamps_short_months():
    ws = make_windows(daily(date(2020, 1, 31), 400), train="1M", test="1M")
    assert ws[0].train_end == date(2020, 2, 29), "leap-year February, clamped from the 31st"


# --------------------------------------------------------------------------- #
# the run
# --------------------------------------------------------------------------- #

def make_adapter(calls, *, train_score, test_score):
    """Adapter whose in-sample and out-of-sample scores are set independently."""

    def evaluate(data, params, *, score_start, score_end):
        calls.append((dict(params), score_start, score_end))
        is_train = (score_start, score_end) in data["train_ranges"]
        table = train_score if is_train else test_score
        value = table(params)
        return {
            "sortino": value,
            "total_return_pct": value * 10,
            "max_drawdown_pct": -abs(value) * 5,
            "num_trades": params.get("trades", 30),
        }

    return evaluate


def build(stamps, train="12M", test="6M", mode="rolling"):
    ws = make_windows(stamps, train=train, test=test, mode=mode)
    return ws, {"train_ranges": {(w.train_start, w.train_end) for w in ws}}


def test_selection_uses_only_the_train_window():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    ws, data = build(stamps)
    calls: list = []
    # 'a' wins in-sample; 'b' would win out-of-sample. The walk-forward must pick 'a'.
    adapter = make_adapter(
        calls,
        train_score=lambda p: 2.0 if p["k"] == "a" else 0.5,
        test_score=lambda p: 0.1 if p["k"] == "a" else 9.9,
    )
    report = walk_forward(
        data, stamps, [{"k": "a"}, {"k": "b"}], adapter, train="12M", test="6M"
    )
    assert report.n_folds == len(ws)
    assert all(f.params["k"] == "a" for f in report.folds)
    assert all(f.test["sortino"] == 0.1 for f in report.folds)


def test_test_window_is_evaluated_once_per_fold_for_the_winner_only():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    ws, data = build(stamps)
    calls: list = []
    grid = [{"k": "a"}, {"k": "b"}, {"k": "c"}]
    adapter = make_adapter(calls, train_score=lambda p: 1.0, test_score=lambda p: 1.0)
    walk_forward(data, stamps, grid, adapter, train="12M", test="6M")
    test_ranges = {(w.test_start, w.test_end) for w in ws}
    test_calls = [c for c in calls if (c[1], c[2]) in test_ranges]
    assert len(test_calls) == len(ws), "one out-of-sample evaluation per fold"


def test_min_trades_filters_the_grid_in_sample():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    _, data = build(stamps)
    calls: list = []
    adapter = make_adapter(
        calls,
        train_score=lambda p: 9.0 if p["k"] == "quiet" else 1.0,
        test_score=lambda p: 1.0,
    )
    grid = [{"k": "quiet", "trades": 2}, {"k": "busy", "trades": 40}]
    report = walk_forward(
        data, stamps, grid, adapter, train="12M", test="6M", min_trades=20
    )
    assert all(f.params["k"] == "busy" for f in report.folds)
    assert all(f.rejected_for_trades == 1 for f in report.folds)


def test_fold_is_skipped_when_nothing_clears_min_trades():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    _, data = build(stamps)
    adapter = make_adapter([], train_score=lambda p: 1.0, test_score=lambda p: 1.0)
    report = walk_forward(
        data, stamps, [{"k": "a", "trades": 1}], adapter,
        train="12M", test="6M", min_trades=20,
    )
    assert report.n_folds == 0
    ok, reasons = report.passed()
    assert not ok and "no folds" in reasons[0]


def test_empty_grid_rejected():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    _, data = build(stamps)
    with pytest.raises(ValueError, match="empty"):
        walk_forward(data, stamps, [], lambda *a, **k: {}, train="12M", test="6M")


def test_missing_select_key_is_a_clear_error():
    stamps = daily(date(2020, 1, 1), 365 * 4)
    _, data = build(stamps)
    with pytest.raises(ValueError, match="sortino"):
        walk_forward(
            data, stamps, [{"k": "a"}],
            lambda d, p, *, score_start, score_end: {"num_trades": 5},
            train="12M", test="6M",
        )


# --------------------------------------------------------------------------- #
# report arithmetic
# --------------------------------------------------------------------------- #

def fold(train_ret, test_ret, dd=-10.0, trades=10, params=None):
    from backtest.walkforward import Fold

    w = Window(0, date(2020, 1, 1), date(2021, 1, 1), date(2021, 1, 1), date(2021, 7, 1))
    return Fold(
        window=w,
        params=params or {"k": "a"},
        train={"total_return_pct": train_ret},
        test={"total_return_pct": test_ret, "max_drawdown_pct": dd, "num_trades": trades},
    )


def test_efficiency_is_undefined_when_in_sample_lost_money():
    r = WalkForwardReport(folds=[fold(-40.0, -20.0)])
    assert r.efficiency is None, "a negative denominator would flip the sign"
    ok, reasons = r.passed()
    assert not ok and any("undefined" in x for x in reasons)


def test_efficiency_and_hit_rate():
    r = WalkForwardReport(folds=[fold(100.0, 50.0), fold(100.0, -10.0)])
    assert r.efficiency == pytest.approx(0.2)
    assert r.hit_rate == pytest.approx(0.5)
    assert r.mean_test_return == pytest.approx(20.0)
    assert r.median_test_return == pytest.approx(20.0)


def test_param_churn():
    stable = WalkForwardReport(folds=[fold(1, 1, params={"a": 1}) for _ in range(3)])
    assert stable.param_churn == 0.0
    churny = WalkForwardReport(
        folds=[fold(1, 1, params={"a": i}) for i in range(3)]
    )
    assert churny.param_churn == pytest.approx(1.0)


def test_worst_drawdown_is_the_deepest_not_the_last():
    r = WalkForwardReport(folds=[fold(1, 1, dd=-12.0), fold(1, 1, dd=-64.0), fold(1, 1, dd=-3.0)])
    assert r.worst_drawdown == pytest.approx(-64.0)
    ok, reasons = r.passed(max_drawdown=-60.0)
    assert not ok and any("drawdown" in x for x in reasons)


def test_passed_is_true_for_a_good_run():
    folds = [fold(100.0, 70.0, dd=-18.0, trades=12) for _ in range(4)]
    r = WalkForwardReport(folds=folds)
    ok, reasons = r.passed()
    assert ok, reasons


def test_markdown_renders_verdict_and_every_fold():
    r = WalkForwardReport(folds=[fold(100.0, 50.0), fold(100.0, -10.0)])
    md = r.to_markdown("roc_bot")
    assert "roc_bot" in md and ("PASS" in md or "FAIL" in md)
    assert md.count("\n| 1 ") + md.count("\n| 2 ") == 2
