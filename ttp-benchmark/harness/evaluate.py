"""Scoring for TTP extraction.

Ground truth and predictions are both *sets* of ATT&CK technique ids per
report. We score two ways:

  strict  -> exact id match (T1059.001 must equal T1059.001)
  parent  -> technique-level: both sides collapsed to their parent technique
             (T1059.001 -> T1059), so a right technique / wrong sub-technique
             still counts. Reported alongside strict so you can see how much of
             the gap is sub-technique precision vs. missing the technique.

Micro = pool TP/FP/FN across all reports (weights big reports more).
Macro = mean of per-report F1 (weights every report equally).
"""

from __future__ import annotations

from dataclasses import dataclass


def parent(tid: str) -> str:
    return tid.split(".")[0]


@dataclass
class Score:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def _score_one(gold: set[str], pred: set[str]) -> Score:
    return Score(tp=len(gold & pred), fp=len(pred - gold), fn=len(gold - pred))


@dataclass
class ModelReport:
    model_key: str
    micro_strict: Score
    micro_parent: Score
    macro_f1_strict: float
    macro_f1_parent: float
    n_reports: int
    n_errors: int
    avg_latency_s: float
    total_input_tokens: int
    total_output_tokens: int
    est_cost_usd: float | None


def evaluate_model(
    model_key: str,
    per_report: list[dict],
    price_in: float | None,
    price_out: float | None,
) -> ModelReport:
    """per_report: list of {gold: set[str], pred: set[str], latency, in_tok, out_tok, error}"""
    micro_s, micro_p = Score(), Score()
    f1s_s, f1s_p = [], []
    n_err = sum(1 for r in per_report if r.get("error"))
    lat = in_tok = out_tok = 0

    for r in per_report:
        gold = {g for g in r["gold"] if g}
        pred = {p for p in r["pred"] if p}
        s = _score_one(gold, pred)
        p = _score_one({parent(g) for g in gold}, {parent(x) for x in pred})
        micro_s.tp += s.tp; micro_s.fp += s.fp; micro_s.fn += s.fn
        micro_p.tp += p.tp; micro_p.fp += p.fp; micro_p.fn += p.fn
        f1s_s.append(s.f1)
        f1s_p.append(p.f1)
        lat += r.get("latency", 0.0)
        in_tok += r.get("in_tok", 0)
        out_tok += r.get("out_tok", 0)

    n = len(per_report)
    cost = None
    if price_in is not None and price_out is not None:
        cost = in_tok / 1e6 * price_in + out_tok / 1e6 * price_out

    return ModelReport(
        model_key=model_key,
        micro_strict=micro_s,
        micro_parent=micro_p,
        macro_f1_strict=sum(f1s_s) / n if n else 0.0,
        macro_f1_parent=sum(f1s_p) / n if n else 0.0,
        n_reports=n,
        n_errors=n_err,
        avg_latency_s=lat / n if n else 0.0,
        total_input_tokens=in_tok,
        total_output_tokens=out_tok,
        est_cost_usd=cost,
    )
