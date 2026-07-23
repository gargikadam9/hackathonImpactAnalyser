import React from 'react'
import type { TabView, ChangeImpactResponse, SimilarIncident, AgentTrace } from '../types'

interface ReportTabsProps {
  report: ChangeImpactResponse
  activeTab: TabView
  onTabChange: (tab: TabView) => void
}

const tabs: { key: TabView; label: string }[] = [
  { key: 'overview', label: 'Overview' },
  { key: 'understanding', label: 'Understanding' },
  { key: 'evidence', label: 'Evidence' },
  { key: 'incidents', label: 'Incidents' },
  { key: 'mitigation', label: 'Mitigation' },
  { key: 'trace', label: 'Trace' },
]

const ReportTabs: React.FC<ReportTabsProps> = ({ report, activeTab, onTabChange }) => {
  return (
    <div className="report-tabs">
      <div className="tabs-nav">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-content animate-fadeIn">
        {activeTab === 'overview' && <OverviewTab report={report} />}
        {activeTab === 'understanding' && <UnderstandingTab report={report} />}
        {activeTab === 'evidence' && <EvidenceTab report={report} />}
        {activeTab === 'incidents' && <IncidentsTab incidents={report.similarIncidents} />}
        {activeTab === 'mitigation' && <MitigationTab report={report} />}
        {activeTab === 'trace' && <TraceTab traces={report.agentTraces} />}
      </div>

      <style>{`
        .report-tabs {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .tabs-nav {
          display: flex;
          gap: 4px;
          background: #1e293b;
          border-radius: 10px;
          padding: 4px;
          border: 1px solid #334155;
          overflow-x: auto;
        }
        .tab-btn {
          padding: 8px 16px;
          border: none;
          background: transparent;
          color: #94a3b8;
          font-size: 0.85rem;
          font-weight: 500;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.2s ease;
          white-space: nowrap;
          font-family: inherit;
        }
        .tab-btn:hover {
          color: #f1f5f9;
          background: rgba(99, 102, 241, 0.1);
        }
        .tab-btn.active {
          background: #6366f1;
          color: white;
        }
        .tab-content {
          min-height: 200px;
        }
      `}</style>
    </div>
  )
}

// Overview Tab
const OverviewTab: React.FC<{ report: ChangeImpactResponse }> = ({ report }) => (
  <div className="tab-panel">
    <div className="overview-grid">
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Impact Summary</h3>
        </div>
        <div className="stat-list">
          <div className="stat">
            <span className="stat-label">Risk Score</span>
            <span className={`stat-value badge-${report.riskLevel}`}>
              {(report.riskScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Confidence</span>
            <span className="stat-value">{(report.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="stat">
            <span className="stat-label">Services Impacted</span>
            <span className="stat-value">{report.impactedServices.length}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Processing Time</span>
            <span className="stat-value">{(report.processingTimeMs / 1000).toFixed(1)}s</span>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Teams to Notify</h3>
        </div>
        <div className="team-list">
          {report.teamsToNotify.map((team, i) => (
            <span key={i} className="team-badge">{team}</span>
          ))}
        </div>
        <div style={{ marginTop: 16 }}>
          <h3 className="card-title" style={{ marginBottom: 8 }}>Mode</h3>
          <span className={`badge ${report.mockMode ? 'badge-medium' : 'badge-success'}`}>
            {report.mockMode ? 'Mock Mode' : 'Live Analysis'}
          </span>
        </div>
      </div>
    </div>

    <div className="card" style={{ marginTop: 16 }}>
      <div className="card-header">
        <h3 className="card-title">Executive Summary</h3>
      </div>
      <div className="exec-summary" dangerouslySetInnerHTML={{ __html: report.executiveSummary }} />
    </div>

    <style>{`
      .overview-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
      }
      @media (max-width: 640px) {
        .overview-grid { grid-template-columns: 1fr; }
      }
      .stat-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      .stat {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #334155;
      }
      .stat:last-child { border-bottom: none; }
      .stat-label { color: #94a3b8; font-size: 0.875rem; }
      .stat-value { font-weight: 600; font-size: 0.875rem; }
      .team-list {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .team-badge {
        padding: 4px 10px;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 6px;
        color: #818cf8;
        font-size: 0.8rem;
      }
      .exec-summary {
        font-size: 0.9rem;
        line-height: 1.7;
        color: #cbd5e1;
      }
      .exec-summary strong {
        color: #f1f5f9;
      }
    `}</style>
  </div>
)

// Understanding Tab
const UnderstandingTab: React.FC<{ report: ChangeImpactResponse }> = ({ report }) => (
  <div className="tab-panel">
    <div className="card">
      <h3 className="card-title" style={{ marginBottom: 12 }}>Interpreted Intent</h3>
      <p style={{ color: '#cbd5e1', lineHeight: 1.7 }}>{report.interpretedIntent}</p>
    </div>
    <div className="card" style={{ marginTop: 16 }}>
      <h3 className="card-title" style={{ marginBottom: 12 }}>Impacted Services</h3>
      <div className="service-chips">
        {report.impactedServices.map((svc, i) => (
          <span key={i} className="service-chip">{svc}</span>
        ))}
      </div>
    </div>
    <div className="card" style={{ marginTop: 16 }}>
      <h3 className="card-title" style={{ marginBottom: 12 }}>Data Sources Used</h3>
      <div className="service-chips">
        {report.dataSourcesUsed.map((src, i) => (
          <span key={i} className="service-chip src-chip">{src}</span>
        ))}
      </div>
    </div>

    <style>{`
      .service-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
      }
      .service-chip {
        padding: 6px 14px;
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.3);
        border-radius: 6px;
        color: #22d3ee;
        font-size: 0.85rem;
      }
      .src-chip {
        background: rgba(16, 185, 129, 0.1);
        border-color: rgba(16, 185, 129, 0.3);
        color: #34d399;
      }
    `}</style>
  </div>
)

// Evidence Tab
const EvidenceTab: React.FC<{ report: ChangeImpactResponse }> = ({ report }) => (
  <div className="tab-panel">
    {report.retrievedEvidence.length === 0 ? (
      <div className="card">
        <p style={{ color: '#94a3b8', textAlign: 'center', padding: 20 }}>
          No evidence retrieved in mock mode. Run with a live AI provider for detailed evidence.
        </p>
      </div>
    ) : (
      <div className="evidence-list">
        {report.retrievedEvidence.slice(0, 10).map((ev, i) => (
          <div key={i} className="evidence-item card">
            <div className="evidence-meta">
              <span className={`badge badge-${(ev as any).type || 'info'}`}>
                {(ev as any).type}
              </span>
              <span style={{ color: '#64748b', fontSize: '0.8rem' }}>
                Source: {(ev as any).source}
              </span>
            </div>
            <p className="evidence-content">
              {typeof (ev as any).content === 'string'
                ? (ev as any).content.substring(0, 300)
                : JSON.stringify((ev as any).content)}
            </p>
            {(ev as any).relevance !== undefined && (
              <div className="evidence-relevance">
                Relevance: {((ev as any).relevance * 100).toFixed(0)}%
              </div>
            )}
          </div>
        ))}
      </div>
    )}

    <style>{`
      .evidence-list { display: flex; flex-direction: column; gap: 12px; }
      .evidence-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .evidence-content {
        color: #cbd5e1;
        font-size: 0.85rem;
        line-height: 1.6;
      }
      .evidence-relevance {
        margin-top: 8px;
        font-size: 0.8rem;
        color: #64748b;
      }
    `}</style>
  </div>
)

// Incidents Tab
const IncidentsTab: React.FC<{ incidents: SimilarIncident[] }> = ({ incidents }) => (
  <div className="tab-panel">
    {incidents.length === 0 ? (
      <div className="card">
        <p style={{ color: '#94a3b8', textAlign: 'center', padding: 20 }}>
          No similar incidents found.
        </p>
      </div>
    ) : (
      <div className="incidents-list">
        {incidents.map((inc, i) => (
          <div key={i} className="incident-item card">
            <div className="incident-header">
              <span className={`badge badge-${inc.severity}`}>{inc.severity}</span>
              <span style={{ color: '#64748b', fontSize: '0.8rem' }}>{inc.id}</span>
            </div>
            <h4 style={{ margin: '8px 0', fontSize: '0.95rem' }}>{inc.title}</h4>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>
              Service: {inc.service}
            </p>
            {inc.resolution && (
              <p style={{ color: '#cbd5e1', fontSize: '0.85rem', marginTop: 4 }}>
                Resolution: {inc.resolution.substring(0, 150)}
              </p>
            )}
            {inc.similarity_score !== undefined && (
              <div style={{ marginTop: 8, fontSize: '0.8rem', color: '#64748b' }}>
                Match: {(inc.similarity_score * 100).toFixed(0)}%
              </div>
            )}
          </div>
        ))}
      </div>
    )}

    <style>{`
      .incidents-list { display: flex; flex-direction: column; gap: 12px; }
      .incident-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
    `}</style>
  </div>
)

// Mitigation Tab
const MitigationTab: React.FC<{ report: ChangeImpactResponse }> = ({ report }) => (
  <div className="tab-panel">
    <div className="card">
      <h3 className="card-title" style={{ marginBottom: 12 }}>Potential Risks</h3>
      <div className="list-items">
        {report.potentialRisks.map((risk, i) => (
          <div key={i} className="list-item">
            <span className="list-icon">⚠️</span>
            <span>{risk}</span>
          </div>
        ))}
      </div>
    </div>

    <div className="card" style={{ marginTop: 16 }}>
      <h3 className="card-title" style={{ marginBottom: 12 }}>Mitigation Plan</h3>
      <div className="list-items">
        {report.mitigationPlan.map((step, i) => (
          <div key={i} className="list-item">
            <span className="list-icon">{i + 1}.</span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </div>

    <div className="card" style={{ marginTop: 16 }}>
      <h3 className="card-title" style={{ marginBottom: 12 }}>Recommended Tests</h3>
      <div className="list-items">
        {report.recommendedTests.map((test, i) => (
          <div key={i} className="list-item">
            <span className="list-icon">🧪</span>
            <span>{test}</span>
          </div>
        ))}
      </div>
    </div>

    <style>{`
      .list-items { display: flex; flex-direction: column; gap: 8px; }
      .list-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 12px;
        background: rgba(51, 65, 85, 0.3);
        border-radius: 8px;
        font-size: 0.875rem;
        color: #cbd5e1;
      }
      .list-icon {
        flex-shrink: 0;
        font-weight: 600;
        min-width: 24px;
      }
    `}</style>
  </div>
)

// Trace Tab
const TraceTab: React.FC<{ traces: AgentTrace[] }> = ({ traces }) => (
  <div className="tab-panel">
    <div className="trace-timeline">
      {traces.map((trace, i) => (
        <div key={i} className={`trace-item ${trace.status}`}>
          <div className="trace-marker">
            <div className="trace-dot" />
            <div className="trace-line" />
          </div>
          <div className="trace-content card">
            <div className="trace-header">
              <span className="trace-agent">{trace.agent}</span>
              <div className="trace-meta">
                <span className={`badge badge-${trace.status === 'completed' ? 'success' : trace.status === 'failed' ? 'critical' : 'medium'}`}>
                  {trace.status}
                </span>
                <span className="trace-time">{(trace.processingTimeMs).toFixed(0)}ms</span>
              </div>
            </div>
            {trace.output && (
              <p className="trace-output">{trace.output.substring(0, 200)}</p>
            )}
            {trace.error && (
              <p className="trace-error">Error: {trace.error}</p>
            )}
          </div>
        </div>
      ))}
    </div>

    <style>{`
      .trace-timeline { display: flex; flex-direction: column; gap: 0; }
      .trace-item {
        display: flex;
        gap: 16px;
      }
      .trace-marker {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 24px;
        flex-shrink: 0;
      }
      .trace-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: #6366f1;
        border: 2px solid #1e293b;
        z-index: 1;
      }
      .trace-item.completed .trace-dot { background: #10b981; }
      .trace-item.failed .trace-dot { background: #ef4444; }
      .trace-line {
        width: 2px;
        flex-grow: 1;
        background: #334155;
        margin: 4px 0;
      }
      .trace-item:last-child .trace-line { display: none; }
      .trace-content {
        flex-grow: 1;
        margin-bottom: 8px;
        padding: 12px 16px;
      }
      .trace-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .trace-agent {
        font-weight: 600;
        text-transform: capitalize;
        font-size: 0.9rem;
      }
      .trace-meta {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .trace-time {
        font-size: 0.75rem;
        color: #64748b;
      }
      .trace-output {
        font-size: 0.8rem;
        color: #94a3b8;
        line-height: 1.5;
      }
      .trace-error {
        font-size: 0.8rem;
        color: #fca5a5;
        margin-top: 4px;
      }
    `}</style>
  </div>
)

export default ReportTabs

