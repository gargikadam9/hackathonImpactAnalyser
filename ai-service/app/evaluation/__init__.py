"""
MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring Pipeline.

This package is a fully independent "Auditor Agent" layer that runs AFTER
the primary v2 ReAct pipeline (app/agents/react/*) has produced its
RiskAnalysisReport. It never participates in generating a prediction — it
only grades one, the way a model-risk / QA reviewer would.
"""

from app.evaluation.evaluator import ImpactAnalyserEvaluator, default_evaluator
from app.evaluation.schemas import EvaluationReport, EvaluationVerdict, FeedbackEntry

__all__ = [
    "ImpactAnalyserEvaluator",
    "default_evaluator",
    "EvaluationReport",
    "EvaluationVerdict",
    "FeedbackEntry",
]
