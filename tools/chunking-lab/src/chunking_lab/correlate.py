"""The section 9 experiment: do query-free signals predict query-dependent ranking?

This is a **query over accumulated results**, not a pipeline. That was the point of
answering open question 4 before writing the result schema: intrinsic and extrinsic
metrics are computed over the same runs and stored on the same row, so asking "does
boundary fidelity track Precision Omega?" is a group-by over JSONL rather than a
separate harness that has to re-derive everything.

**This is a replication, and the framing matters.** MoC (ACL 2025) and ChunkScore
have both correlated query-free signals against downstream performance, and
Adaptive Chunking (LREC 2026) selects a chunker from intrinsic metrics alone. What
is left open is one notch narrower: all of them compute their signals **with a
model** -- perplexity, embeddings, an LLM. The ones here are arithmetic over
character offsets. Whether *those* carry information is the question.

## The confound, stated up front

Precision Omega is `|gold| / |the chunks holding gold|`. Smaller chunks shrink the
denominator **by construction**, so a strong negative correlation between median
chunk length and Precision Omega is close to a tautology, not a discovery. Any
honest version of this experiment has to say so and then control for it -- which is
what ``--control`` does, via a partial rank correlation. A signal that survives
controlling for size is telling you something size does not.
"""

from __future__ import annotations

import json
import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

#: Two-tailed critical values for Spearman's rho at alpha = 0.05. Beyond n = 20 the
#: asymptotic approximation 1.96 / sqrt(n - 1) is used. Reported rather than a
#: p-value because a lookup needs no dependency and, at the sample sizes this
#: experiment actually runs at (one point per strategy), "is it past the line" is
#: the only question the number can honestly answer.
_CRITICAL = {
    5: 1.000,
    6: 0.886,
    7: 0.786,
    8: 0.738,
    9: 0.700,
    10: 0.648,
    11: 0.618,
    12: 0.587,
    13: 0.560,
    14: 0.538,
    15: 0.521,
    16: 0.503,
    17: 0.485,
    18: 0.472,
    19: 0.460,
    20: 0.447,
}


def critical_rho(n: int) -> float | None:
    """Smallest |rho| that would be significant at p < 0.05, or None if n is too small."""
    if n < 5:
        return None
    if n in _CRITICAL:
        return _CRITICAL[n]
    return 1.96 / ((n - 1) ** 0.5)


def _ranks(values: list[float]) -> list[float]:
    """Ranks, with ties sharing their average rank.

    Tie handling is not a detail here: several strategies produce identical
    `mid_table_rate` of 0.0 on a corpus with no tables, and naive ranking would
    invent an ordering between them and report a correlation for it.
    """
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys, strict=True))
    den = (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** 0.5
    return num / den if den else 0.0


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation. Rank-based because we care about *ordering*, not scale.

    The question is "would screening on this signal put the configurations in the
    same order as measuring them?", and that is a question about ranks.
    """
    return _pearson(_ranks(xs), _ranks(ys))


def partial_spearman(xs: list[float], ys: list[float], control: list[float]) -> float:
    """Rank correlation of x and y with the effect of ``control`` removed.

    Used to ask the question that matters: once you already know the chunk size,
    does this signal tell you anything further about retrieval quality?
    """
    rxy, rxz, ryz = spearman(xs, ys), spearman(xs, control), spearman(ys, control)
    den = ((1 - rxz**2) * (1 - ryz**2)) ** 0.5
    return (rxy - rxz * ryz) / den if den else 0.0


#: The model-free intrinsic signals worth testing. Excludes cohesion and separation,
#: which need an embedder -- their absence is the whole point of the narrower
#: question this experiment asks.
SIGNALS = (
    "median_length",
    "p95_length",
    "chunks",
    "duplication",
    "boundary_fidelity",
    "orphan_rate",
    "runt_rate",
    "oversize_rate",
    "mid_table_rate",
    "split_fence_rate",
)

TARGETS = ("precision_omega", "iou", "recall", "precision")


@dataclass(frozen=True, slots=True)
class Point:
    """One (corpus, strategy) pair: its intrinsic signals and its mean extrinsic scores."""

    corpus: str
    strategy: str
    questions: int
    intrinsic: dict[str, float]
    extrinsic: dict[str, float]


@dataclass(frozen=True, slots=True)
class Correlation:
    """One signal's relationship to one target, within one corpus."""

    corpus: str
    signal: str
    target: str
    n: int
    rho: float
    partial: float | None
    #: True when the signal takes the same value for every configuration on this
    #: corpus, so there is nothing to correlate. Distinguished from rho == 0
    #: because the two mean opposite things: a constant signal is **untested
    #: here**, not shown to be uninformative. The Chroma corpora contain no
    #: Markdown tables and no code fences, so `mid_table_rate` and
    #: `split_fence_rate` are constant on all five -- reporting that as "0.00, no
    #: relationship" would be the most misleading number this tool could print.
    constant: bool = False

    @property
    def significant(self) -> bool:
        if self.constant:
            return False
        threshold = critical_rho(self.n)
        return threshold is not None and abs(self.rho) >= threshold


def load(path: Path) -> list[Point]:
    """Collapse per-question JSONL rows into one point per (corpus, strategy).

    Extrinsic scores are per question and get averaged; intrinsic values are a
    property of the chunking and are identical on every row of it, which is exactly
    the deliberate redundancy the schema was given so a row could be read alone.
    """
    grouped: dict[tuple[str, str], list[dict]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            grouped.setdefault((row["corpus"], row["strategy"]), []).append(row)

    points = []
    for (corpus, strategy), rows in sorted(grouped.items()):
        intrinsic = {
            key: float(rows[0]["intrinsic"][key])
            for key in SIGNALS
            if rows[0]["intrinsic"].get(key) is not None
        }
        extrinsic = {
            key: statistics.mean(float(r["extrinsic"][key]) for r in rows) for key in TARGETS
        }
        points.append(Point(corpus, strategy, len(rows), intrinsic, extrinsic))
    return points


def correlate(
    points: Iterable[Point], target: str = "precision_omega", control: str | None = "median_length"
) -> list[Correlation]:
    """Correlate every signal against ``target``, once per corpus.

    Per corpus rather than pooled: different corpora have different baselines, and
    pooling them would let a between-corpus difference masquerade as a
    within-corpus relationship.
    """
    by_corpus: dict[str, list[Point]] = {}
    for point in points:
        by_corpus.setdefault(point.corpus, []).append(point)

    results = []
    for corpus, group in sorted(by_corpus.items()):
        for signal in SIGNALS:
            usable = [p for p in group if signal in p.intrinsic]
            if len(usable) < 3:
                continue
            xs = [p.intrinsic[signal] for p in usable]
            ys = [p.extrinsic[target] for p in usable]
            constant = len(set(xs)) <= 1
            partial = None
            if (
                not constant
                and control
                and control != signal
                and all(control in p.intrinsic for p in usable)
            ):
                partial = partial_spearman(xs, ys, [p.intrinsic[control] for p in usable])
            results.append(
                Correlation(
                    corpus,
                    signal,
                    target,
                    len(usable),
                    0.0 if constant else spearman(xs, ys),
                    partial,
                    constant,
                )
            )
    return results


def summarise(results: list[Correlation]) -> dict[str, dict[str, float]]:
    """Mean rho and mean partial rho per signal, across corpora.

    Averaging correlations is a rough operation; it is used here only to order the
    signals for reading, never as the reported statistic. The per-corpus values are
    what the table shows, and a signal that swings sign between corpora is telling
    you something an average would hide.
    """
    by_signal: dict[str, list[Correlation]] = {}
    for result in results:
        by_signal.setdefault(result.signal, []).append(result)
    return {
        signal: {
            # Constant rows carry no information and are excluded rather than
            # averaged in as zeros, which would drag a real signal toward nothing.
            "mean_rho": statistics.mean([r.rho for r in rows if not r.constant] or [0.0]),
            "constant_everywhere": all(r.constant for r in rows),
            "mean_partial": statistics.mean([r.partial for r in rows if r.partial is not None])
            if any(r.partial is not None for r in rows)
            else 0.0,
            "corpora": len(rows),
            "min_rho": min([r.rho for r in rows if not r.constant] or [0.0]),
            "max_rho": max([r.rho for r in rows if not r.constant] or [0.0]),
        }
        for signal, rows in by_signal.items()
    }
