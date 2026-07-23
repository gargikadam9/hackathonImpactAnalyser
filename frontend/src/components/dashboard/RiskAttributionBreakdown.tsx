import React, { useState } from 'react'
import type { RiskAttributionBreakdownProps, RiskDriverView } from './types'

/**
 * MODULE 7 — Explainable AI (XAI) & Attribution Pipeline.
 *
 * Renders the strict `ExplainabilityReport` produced by
 * `build_attribution_matrix` (ai-service/app/agents/react/explainability.py)
 * as a visual "Risk Line-Item Breakdown": every driver that contributed to
 * the numeric risk score gets its own row, with the exact code snippet (or
 * structural signal) that caused it, a percentage-weighted bar, and a
 * hoverable tooltip with the full justification text. This is the
 * dashboard-facing deliverable for "the dashboard must not just show a raw
 * Risk Score: 85/100 — it must explain exactly why".
 */

const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  blast_radius: { label: 'Blast Radius', color: '#f59e0b', icon: '💥' },
  criticality: { label: 'Service Criticality', color: '#ef4444', icon: '🔺' },
  historical_precedent: { label: 'Historical Precedent', color: '#a78bfa', icon: '🕰️' },
  change_type_baseline: { label: 'Change Type Baseline', color: '#60a5fa', icon: '📐' },
}

function categoryMeta(category: string) {
  return CATEGORY_META[category] ?? { label: category, color: '#94a3b8', icon: '❔' }
}

function isStructuralPlaceholder(snippet: string): boolean {
  return snippet.trim().startsWith('(')
}

const RiskDriverRow: React.FC<{ driver: RiskDriverView; rank: number }> = ({ driver, rank }) => {
  const [isHovered, setIsHovered] = useState(false)
  const meta = categoryMeta(driver.category)
  const structural = isStructuralPlaceholder(driver.codeSnippet)

  return (
    <div
      className="rab-row"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsHovered(true)}
      onBlur={() => setIsHovered(false)}
      tabIndex={0}
      role="group"
      aria-label={`Risk driver ${rank}: ${driver.justification}`}
    >
      <div className="rab-row-header">
        <span className="rab-rank">#{rank}</span>
        <span className="rab-category-badge" style={{ borderColor: meta.color, color: meta.color }}>
          {meta.icon} {meta.label}
        </span>
        {driver.filePath && <span className="rab-file-path">{driver.filePath}</span>}
        <span className="rab-weight-value" style={{ color: meta.color }}>
          {driver.severityWeight.toFixed(1)}%
        </span>
      </div>

      <div className="rab-weight-track">
        <div className="rab-weight-fill" style={{ width: `${Math.min(driver.severityWeight, 100)}%`, background: meta.color }} />
      </div>

      <pre className={`rab-snippet ${structural ? 'rab-snippet-structural' : 'rab-snippet-code'}`}>
        <code>{driver.codeSnippet}</code>
      </pre>

      {isHovered && (
        <div className="rab-tooltip" role="tooltip">
          {driver.justification}
        </div>
      )}
      {!isHovered && <p className="rab-justification-inline">{driver.justification}</p>}

      <style>{`
        .rab-row {
          position: relative;
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding: 14px 16px;
          background: rgba(30, 41, 59, 0.6);
          border: 1px solid #334155;
          border-radius: 10px;
          outline: none;
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .rab-row:hover, .rab-row:focus {
          border-color: ${meta.color}55;
          box-shadow: 0 0 0 1px ${meta.color}33;
        }
        .rab-row-header {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }
        .rab-rank {
          font-size: 0.75rem;
          font-weight: 700;
          color: #64748b;
        }
        .rab-category-badge {
          font-size: 0.72rem;
          font-weight: 700;
          padding: 2px 9px;
          border: 1px solid;
          border-radius: 999px;
          white-space: nowrap;
        }
        .rab-file-path {
          font-size: 0.72rem;
          color: #64748b;
          font-family: 'JetBrains Mono', 'Courier New', monospace;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          max-width: 260px;
        }
        .rab-weight-value {
          margin-left: auto;
          font-size: 0.95rem;
          font-weight: 800;
        }
        .rab-weight-track {
          width: 100%;
          height: 5px;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.15);
          overflow: hidden;
        }
        .rab-weight-fill {
          height: 100%;
          border-radius: 999px;
          transition: width 0.6s ease;
        }
        .rab-snippet {
          margin: 0;
          padding: 8px 10px;
          border-radius: 6px;
          font-size: 0.78rem;
          line-height: 1.5;
          overflow-x: auto;
          white-space: pre-wrap;
          word-break: break-word;
        }
        .rab-snippet-code {
          background: rgba(239, 68, 68, 0.08);
          border: 1px solid rgba(239, 68, 68, 0.35);
          color: #fca5a5;
        }
        .rab-snippet-structural {
          background: rgba(148, 163, 184, 0.08);
          border: 1px dashed rgba(148, 163, 184, 0.35);
          color: #94a3b8;
          font-style: italic;
        }
        .rab-justification-inline {
          margin: 0;
          font-size: 0.82rem;
          color: #cbd5e1;
          line-height: 1.5;
        }
        .rab-tooltip {
          position: absolute;
          left: 16px;
          right: 16px;
          bottom: -8px;
          transform: translateY(100%);
          z-index: 20;
          background: #0f172a;
          border: 1px solid ${meta.color}66;
          color: #e2e8f0;
          font-size: 0.8rem;
          line-height: 1.5;
          padding: 10px 12px;
          border-radius: 8px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.45);
        }
      `}</style>
    </div>
  )
}

const RiskAttributionBreakdown: React.FC<RiskAttributionBreakdownProps> = ({
  riskScore,
  drivers,
  historicalCorrelationFactor,
  totalAttributedWeight,
}) => {
  const sortedDrivers = [...drivers].sort((a, b) => b.severityWeight - a.severityWeight)

  return (
    <div className="risk-attribution-breakdown">
      <div className="rab-header">
        <div>
          <h3 className="rab-title">Risk Line-Item Breakdown</h3>
          <p className="rab-subtitle">
            Why the AI assigned <strong>{riskScore}/100</strong> — every driver below is a real,
            traceable percentage of that score.
          </p>
        </div>
        <div className="rab-total-chip" title="Sum of all driver weights below">
          {totalAttributedWeight.toFixed(1)}% attributed
        </div>
      </div>

      <div className="rab-rows">
        {sortedDrivers.length === 0 ? (
          <div className="rab-empty">No structural risk drivers were computed for this analysis.</div>
        ) : (
          sortedDrivers.map((driver, index) => (
            <RiskDriverRow key={driver.id} driver={driver} rank={index + 1} />
          ))
        )}
      </div>

      <div className="rab-historical-correlation">
        <span className="rab-historical-label">📊 Historical Correlation Factor</span>
        <p className="rab-historical-text">{historicalCorrelationFactor}</p>
      </div>

      <style>{`
        .risk-attribution-breakdown {
          display: flex;
          flex-direction: column;
          gap: 16px;
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 12px;
          padding: 20px;
        }
        .rab-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 12px;
          flex-wrap: wrap;
        }
        .rab-title {
          margin: 0 0 4px 0;
          font-size: 1rem;
          color: #f1f5f9;
        }
        .rab-subtitle {
          margin: 0;
          font-size: 0.82rem;
          color: #94a3b8;
        }
        .rab-subtitle strong {
          color: #f87171;
        }
        .rab-total-chip {
          flex-shrink: 0;
          font-size: 0.75rem;
          font-weight: 700;
          padding: 4px 12px;
          border-radius: 999px;
          background: rgba(99, 102, 241, 0.15);
          border: 1px solid rgba(99, 102, 241, 0.4);
          color: #a5b4fc;
        }
        .rab-rows {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        .rab-empty {
          text-align: center;
          color: #94a3b8;
          padding: 20px;
        }
        .rab-historical-correlation {
          padding: 12px 14px;
          background: rgba(167, 139, 250, 0.08);
          border: 1px solid rgba(167, 139, 250, 0.3);
          border-radius: 10px;
        }
        .rab-historical-label {
          display: block;
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #a78bfa;
          margin-bottom: 6px;
        }
        .rab-historical-text {
          margin: 0;
          font-size: 0.85rem;
          line-height: 1.6;
          color: #cbd5e1;
        }
      `}</style>
    </div>
  )
}

export default RiskAttributionBreakdown
