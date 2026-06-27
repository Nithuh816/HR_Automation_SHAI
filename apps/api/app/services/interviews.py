"""Interview domain logic: round/stage mapping and scorecard aggregation."""

from __future__ import annotations

from collections.abc import Sequence

from app.models.enums import ROUND_STAGE, STAGE_ORDER, InterviewRound, Stage


def round_stage(round_: InterviewRound) -> Stage:
    return ROUND_STAGE[round_]


def next_stage_after(round_: InterviewRound) -> Stage:
    """The stage a candidate moves into after passing ``round_``."""
    idx = STAGE_ORDER.index(round_stage(round_))
    if idx + 1 >= len(STAGE_ORDER):
        return STAGE_ORDER[-1]
    return STAGE_ORDER[idx + 1]


def weighted_overall(scores: Sequence[tuple[int, int]]) -> float | None:
    """Weighted average of ``(score, weight)`` pairs, rounded to 2dp.

    Returns ``None`` when there is nothing to score.
    """
    total_weight = sum(weight for _, weight in scores)
    if total_weight == 0:
        return None
    earned = sum(score * weight for score, weight in scores)
    return round(earned / total_weight, 2)
