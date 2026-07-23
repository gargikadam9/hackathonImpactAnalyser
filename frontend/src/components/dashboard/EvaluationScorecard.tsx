import React from 'react'
import type { EvaluationScorecardProps, EvaluationVerdictLabel } from './types'

/**
 * MODULE 8 — Automated Evaluation Metric & Ground-Truth Scoring Pipeline.
 *
 * Renders the independent, post-hoc `EvaluationReport` produced by
 * `ImpactAnalyserEvaluator` (ai-service/app/evaluation/evaluator.py) so a
 * developer can see, at a glance, whether THIS SPECIFIC prediction is
 * actually trustworthy before acting on it — not just the risk score
 * itself, but a second opinion that graded the grader.
 */

const VERDICT_META: Record<EvaluationVerdictLabel, { label: string; color: string; icon: string }> = {
  TRUSTED: { label: 'Trusted', color: '#34d399', icon: '✅' },
  REVIEW_RECOMMENDED: { label: 'Review Recommended', color: '#f59e0b', icon: '⚠️' },
  LOW_CONFIDENCE_FLAGGED: { label: 'Low Confidence — Flagged', color: '#ef4444', icon: '🚩' },
}

const MetricGauge: React.FC<{ label: string; value: number; suffix?: string; tone: string }> = ({
  label,
  value,
  suffix = '%',
  tone,
}) => (
  <div className="es-metric">
    <div className="es-metric-header">
      <span className="es-metric-label">{label}</span>
      <span className="es-metric-value" style={{ color: tone }}>
        {value.toFixed(0)}
        {suffix}
      </span>
    </div>
    <div className="es-metric-track">
      <div className="es-metric-fill" style={{ width: `${Math.min(Math.max(value, 0), 100)}%`, background: tone }} />
    </div>
  </div>
)

function toneForScore(value: number): string {
  if (value >= 80) return '#34d399'
  if (value >= 50) return '#f59e0b'
  return '#ef4444'
}

const EvaluationScorecard: React.FC<EvaluationScorecardProps> = ({
  verdict,
  faithfulnessScore,
  unsupportedClaims,
  contextPrecision,
  contextRecall,
  contextF1,
  aiPredictedScore,
  deterministicBaselineScore,
  percentageDeviation,
  highVarianceWarning,
  evaluatorVersion,
}) => {
  const verdictMeta = VERDICT_META[verdict] ?? VERDICT_META.REVIEW_RECOMMENDED
  const faithfulnessPct = faithfulnessScore * 100
  const precisionPct = contextPrecision * 100
  const recallPct = contextRecall * 100
  const f1Pct = contextF1 * 100

  return (
    <div className="evaluation-scorecard">
      <div className="es-header">
        <div>
          <h3 className="es-title">Evaluation &amp; Ground-Truth Audit</h3>
          <p className="es-subtitle">Independent auditor verdict — computed after, and separate from, the prediction above.</p>
        </div>
        <div className="es-verdict-badge" style={{ borderColor: verdictMeta.color, color: verdictMeta.color }}>
          {verdictMeta.icon} {verdictMeta.label}
        </div>
      </div>

      <div className="es-grid">
        <div className="es-panel">
          <h4 className="es-panel-title">Faithfulness (Hallucination Check)</h4>
          <MetricGauge label="Faithfulness Score" value={faithfulnessPct} tone={toneForScore(faithfulnessPct)} />
          {unsupportedClaims.length > 0 ? (
            <div className="es-unsupported">
              <span className="es-unsupported-label">⚠ {unsupportedClaims.length} unsupported claim(s):</span>
              <ul>
                {unsupportedClaims.slice(0, 3).map((claim, i) => (
                  <li key={i}>{claim}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="es-ok-text">✓ Every claim traces back to retrieved evidence — no hallucination detected.</p>
          )}
        </div>

        <div className="es-panel">
          <h4 className="es-panel-title">RAG Context Precision &amp; Recall</h4>
          <MetricGauge label="Precision@k" value={precisionPct} tone={toneForScore(precisionPct)} />
          <MetricGauge label="Recall@k" value={recallPct} tone={toneForScore(recallPct)} />
          <MetricGauge label="F1 Score" value={f1Pct} tone={toneForScore(f1Pct)} />
        </div>

        <div className="es-panel">
          <h4 className="es-panel-title">Deterministic Ground-Truth Delta</h4>
          <div className="es-delta-row">
            <div className="es-delta-cell">
              <span className="es-delta-label">AI Predicted</span>
              <span className="es-delta-value">{aiPredictedScore}</span>
            </div>
            <span className="es-delta-vs">vs</span>
            <div className="es-delta-cell">
              <span className="es-delta-label">Rule-Engine Baseline</span>
              <span className="es-delta-value">{deterministicBaselineScore}</span>
            </div>
          </div>
          <p className={`es-deviation ${highVarianceWarning ? 'es-deviation-warning' : ''}`}>
            {highVarianceWarning ? '🚨' : '✓'} {percentageDeviation.toFixed(1)}% deviation
            {highVarianceWarning ? ' — exceeds 20% threshold, manual review recommended' : ' — within tolerance'}
          </p>
        </div>
      </div>

      <div className="es-footer">Evaluator: {evaluatorVersion}</div>

      <style>{`
        .evaluation-scorecard {
          display: flex;
          flex-direction: column;
          gap: 16px;
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
        }
        .es-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          flex-wrap: wrap;
        }
        .es-title { margin: 0 0 4px 0; font-size: 1rem; color: #f1f5f9; }
        .es-subtitle { margin: 0; font-size: 0.8rem; color: #94a3b8; }
        .es-verdict-badge {
          flex-shrink: 0;
          font-size: 0.8rem;
          font-weight: 800;
          padding: 6px 14px;
          border-radius: 999px;
          border: 1px solid;
          white-space: nowrap;
        }
        .es-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 14px;
        }
        @media (max-width: 900px) {
          .es-grid { grid-template-columns: 1fr; }
        }
        .es-panel {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 14px;
          background: rgba(51, 65, 85, 0.35);
          border-radius: 10px;
        }
        .es-panel-title {
          margin: 0;
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #94a3b8;
        }
        .es-metric { display: flex; flex-direction: column; gap: 4px; }
        .es-metric-header { display: flex; justify-content: space-between; align-items: baseline; }
        .es-metric-label { font-size: 0.75rem; color: #cbd5e1; }
        .es-metric-value { font-size: 0.9rem; font-weight: 800; }
        .es-metric-track {
          width: 100%;
          height: 5px;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.15);
          overflow: hidden;
        }
        .es-metric-fill { height: 100%; border-radius: 999px; transition: width 0.6s ease; }
        .es-unsupported {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 8px;
          padding: 8px 10px;
        }
        .es-unsupported-label { font-size: 0.75rem; font-weight: 700; color: #f87171; }
        .es-unsupported ul { margin: 6px 0 0 0; padding-left: 18px; }
        .es-unsupported li { font-size: 0.76rem; color: #fca5a5; line-height: 1.5; }
        .es-ok-text { margin: 0; font-size: 0.78rem; color: #6ee7b7; }
        .es-delta-row {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .es-delta-cell {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
          text-align: center;
          padding: 8px;
          background: rgba(15, 23, 42, 0.5);
          border-radius: 8px;
        }
        .es-delta-label { font-size: 0.68rem; color: #94a3b8; text-transform: uppercase; }
        .es-delta-value { font-size: 1.2rem; font-weight: 800; color: #f1f5f9; }
        .es-delta-vs { font-size: 0.72rem; color: #64748b; font-weight: 700; }
        .es-deviation { margin: 0; font-size: 0.8rem; color: #6ee7b7; }
        .es-deviation-warning { color: #fca5a5; font-weight: 700; }
        .es-footer {
          font-size: 0.7rem;
          color: #64748b;
          text-align: right;
          font-family: 'JetBrains Mono', monospace;
        }
      `}</style>
    </div>
  )
}

export default EvaluationScorecard
