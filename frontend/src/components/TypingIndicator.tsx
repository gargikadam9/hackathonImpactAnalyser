import React from 'react'

interface TypingIndicatorProps {
  text?: string
}

const TypingIndicator: React.FC<TypingIndicatorProps> = ({ text = 'Analyzing' }) => {
  return (
    <div className="typing-indicator">
      <div className="typing-dots">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
      <span className="typing-text">{text}...</span>

      <style>{`
        .typing-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          background: #1e293b;
          border-radius: 12px;
          border: 1px solid #334155;
          max-width: fit-content;
        }
        .typing-dots {
          display: flex;
          gap: 4px;
        }
        .dot {
          width: 8px;
          height: 8px;
          background: #6366f1;
          border-radius: 50%;
          animation: typingBounce 1.4s ease-in-out infinite;
        }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingBounce {
          0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
          30% { transform: translateY(-6px); opacity: 1; }
        }
        .typing-text {
          font-size: 0.875rem;
          color: #94a3b8;
        }
      `}</style>
    </div>
  )
}

export default TypingIndicator

