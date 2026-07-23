import React from 'react'

interface SuggestionChipsProps {
  suggestions: string[]
  onSelect: (suggestion: string) => void
}

const SuggestionChips: React.FC<SuggestionChipsProps> = ({ suggestions, onSelect }) => {
  if (!suggestions || suggestions.length === 0) return null

  return (
    <div className="suggestion-chips">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          className="chip"
          onClick={() => onSelect(suggestion)}
        >
          {suggestion}
        </button>
      ))}

      <style>{`
        .suggestion-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin: 8px 0;
        }
        .chip {
          display: inline-flex;
          align-items: center;
          padding: 6px 14px;
          background: rgba(99, 102, 241, 0.1);
          border: 1px solid rgba(99, 102, 241, 0.3);
          border-radius: 20px;
          color: #818cf8;
          font-size: 0.8rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: inherit;
        }
        .chip:hover {
          background: rgba(99, 102, 241, 0.2);
          border-color: #6366f1;
          transform: translateY(-1px);
        }
        .chip:active {
          transform: translateY(0);
        }
      `}</style>
    </div>
  )
}

export default SuggestionChips

