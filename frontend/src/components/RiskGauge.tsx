import React from 'react'

interface RiskGaugeProps {
  score: number
  level: string
  confidence: number
}

const RiskGauge: React.FC<RiskGaugeProps> = ({ score, level, confidence }) => {
  const percentage = Math.min(Math.max(score * 100, 0), 100)
  const circumference = 2 * Math.PI * 54
  const offset = circumference - (percentage / 100) * circumference

  const getColor = () => {
    switch (level) {
      case 'critical': return '#ef4444'
      case 'high': return '#f59e0b'
      case 'medium': return '#3b82f6'
      case 'low': return '#10b981'
      default: return '#6366f1'
    }
  }

  const getLevelLabel = () => {
    switch (level) {
      case 'critical': return 'Critical Risk'
      case 'high': return 'High Risk'
      case 'medium': return 'Medium Risk'
      case 'low': return 'Low Risk'
      default: return 'Unknown'
    }
  }

  const color = getColor()

  return (
    <div className="risk-gauge">
      <svg width="140" height="140" viewBox="0 0 120 120">
        {/* Background circle */}
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="#334155"
          strokeWidth="8"
        />
        {/* Progress arc */}
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform="rotate(-90 60 60)"
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        {/* Center text */}
        <text
          x="60"
          y="55"
          textAnchor="middle"
          fill={color}
          fontSize="24"
          fontWeight="bold"
        >
          {percentage.toFixed(0)}%
        </text>
        <text
          x="60"
          y="72"
          textAnchor="middle"
          fill="#94a3b8"
          fontSize="10"
        >
          RISK
        </text>
      </svg>
      <div className="risk-gauge-info">
        <span className="risk-level" style={{ color }}>
          {getLevelLabel()}
        </span>
        <span className="risk-confidence">
          Confidence: {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      <style>{`
        .risk-gauge {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
        }
        .risk-gauge-info {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .risk-level {
          font-size: 1rem;
          font-weight: 600;
        }
        .risk-confidence {
          font-size: 0.8rem;
          color: #94a3b8;
        }
      `}</style>
    </div>
  )
}

export default RiskGauge

