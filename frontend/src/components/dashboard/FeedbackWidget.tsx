import React, { useState } from 'react'
import type { FeedbackWidgetProps } from './types'

/**
 * MODULE 8 — Feedback capture (human-in-the-loop).
 *
 * Thumbs up/down + manual risk-score override widget that calls
 * `POST /api/v1/feedback/capture` (see services/api.ts::submitFeedback).
 * This is the closing half of the evaluation loop: `EvaluationScorecard`
 * shows the AUTOMATED audit; this widget captures the HUMAN verdict, both
 * keyed by the same `analysis_id` so they can be joined later for
 * fine-tuning the deterministic scoring formula and the vector index.
 */

type SubmitState = 'idle' | 'submitting' | 'submitted' | 'error'

const FeedbackWidget: React.FC<FeedbackWidgetProps> = ({ analysisId, currentRiskScore, onSubmit }) => {
  const [vote, setVote] = useState<'up' | 'down' | null>(null)
  const [showOverride, setShowOverride] = useState(false)
  const [overrideValue, setOverrideValue] = useState<number>(currentRiskScore)
  const [comment, setComment] = useState('')
  const [state, setState] = useState<SubmitState>('idle')

  const handleVote = async (nextVote: 'up' | 'down') => {
    setVote(nextVote)
    setState('submitting')
    try {
      await onSubmit({ vote: nextVote })
      setState('submitted')
    } catch {
      setState('error')
    }
  }

  const handleOverrideSubmit = async () => {
    setState('submitting')
    try {
      await onSubmit({ overriddenRiskScore: overrideValue, comment: comment || undefined })
      setState('submitted')
      setShowOverride(false)
    } catch {
      setState('error')
    }
  }

  return (
    <div className="feedback-widget">
      <div className="fw-row">
        <span className="fw-label">Was this risk assessment accurate?</span>
        <div className="fw-vote-buttons">
          <button
            type="button"
            className={`fw-vote-btn ${vote === 'up' ? 'fw-vote-active fw-vote-up' : ''}`}
            onClick={() => handleVote('up')}
            aria-pressed={vote === 'up'}
            aria-label="Thumbs up — this assessment was accurate"
          >
            👍
          </button>
          <button
            type="button"
            className={`fw-vote-btn ${vote === 'down' ? 'fw-vote-active fw-vote-down' : ''}`}
            onClick={() => handleVote('down')}
            aria-pressed={vote === 'down'}
            aria-label="Thumbs down — this assessment was inaccurate"
          >
            👎
          </button>
          <button type="button" className="fw-override-toggle" onClick={() => setShowOverride((v) => !v)}>
            {showOverride ? 'Cancel override' : 'Override score'}
          </button>
        </div>
      </div>

      {showOverride && (
        <div className="fw-override-panel">
          <label className="fw-override-label" htmlFor={`override-${analysisId}`}>
            Manually corrected risk score (1-100)
          </label>
          <input
            id={`override-${analysisId}`}
            type="range"
            min={1}
            max={100}
            value={overrideValue}
            onChange={(e) => setOverrideValue(Number(e.target.value))}
          />
          <span className="fw-override-current">{overrideValue}/100</span>
          <textarea
            className="fw-comment"
            placeholder="Optional: why is the correct score different? (fed back into the scoring formula's tuning data)"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
          />
          <button type="button" className="fw-submit-btn" onClick={handleOverrideSubmit} disabled={state === 'submitting'}>
            {state === 'submitting' ? 'Submitting…' : 'Submit override'}
          </button>
        </div>
      )}

      {state === 'submitted' && <p className="fw-status fw-status-ok">✓ Feedback captured — thank you.</p>}
      {state === 'error' && <p className="fw-status fw-status-error">Failed to submit feedback. Please try again.</p>}

      <style>{`
        .feedback-widget {
          display: flex;
          flex-direction: column;
          gap: 10px;
          padding: 14px 16px;
          background: rgba(51, 65, 85, 0.35);
          border: 1px solid #334155;
          border-radius: 10px;
        }
        .fw-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 12px;
          flex-wrap: wrap;
        }
        .fw-label { font-size: 0.85rem; color: #cbd5e1; font-weight: 600; }
        .fw-vote-buttons { display: flex; align-items: center; gap: 8px; }
        .fw-vote-btn {
          font-size: 1.1rem;
          padding: 6px 12px;
          background: rgba(15, 23, 42, 0.5);
          border: 1px solid #334155;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s ease;
        }
        .fw-vote-btn:hover { transform: translateY(-1px); }
        .fw-vote-active.fw-vote-up { background: rgba(52, 211, 153, 0.18); border-color: #34d399; }
        .fw-vote-active.fw-vote-down { background: rgba(239, 68, 68, 0.18); border-color: #ef4444; }
        .fw-override-toggle {
          font-size: 0.75rem;
          font-weight: 600;
          padding: 6px 12px;
          background: transparent;
          border: 1px solid #475569;
          border-radius: 8px;
          color: #93c5fd;
          cursor: pointer;
        }
        .fw-override-panel {
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding-top: 6px;
          border-top: 1px solid #334155;
        }
        .fw-override-label { font-size: 0.75rem; color: #94a3b8; }
        .fw-override-current { font-size: 0.85rem; font-weight: 700; color: #f1f5f9; }
        .fw-comment {
          width: 100%;
          resize: vertical;
          font-family: inherit;
          font-size: 0.82rem;
          padding: 8px 10px;
          background: rgba(15, 23, 42, 0.5);
          border: 1px solid #334155;
          border-radius: 8px;
          color: #e2e8f0;
        }
        .fw-submit-btn {
          align-self: flex-start;
          font-size: 0.8rem;
          font-weight: 700;
          padding: 7px 16px;
          background: #3b82f6;
          border: none;
          border-radius: 8px;
          color: white;
          cursor: pointer;
        }
        .fw-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .fw-status { margin: 0; font-size: 0.78rem; }
        .fw-status-ok { color: #6ee7b7; }
        .fw-status-error { color: #fca5a5; }
      `}</style>
    </div>
  )
}

export default FeedbackWidget
