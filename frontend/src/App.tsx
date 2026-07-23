import React, { useState, useRef, useEffect, useCallback } from 'react'
import RiskGauge from './components/RiskGauge'
import TypingIndicator from './components/TypingIndicator'
import SuggestionChips from './components/SuggestionChips'
import ReportTabs from './components/ReportTabs'
import type {
  AnalysisMode,
  TabView,
  ChatMessage,
  ChangeImpactResponse,
  AssistantResponse,
  ChangeType,
} from './types'
import {
  assistantRespond,
  analyzeChangeImpact,
  getChangeTypes,
  getComponents,
  checkHealth,
} from './services/api'

// Icons as inline SVGs
const IconSend = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
  </svg>
)

const IconBot = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="10" rx="2" /><circle cx="12" cy="5" r="2" />
    <path d="M12 7v4" /><line x1="8" y1="16" x2="8" y2="16" /><line x1="16" y1="16" x2="16" y2="16" />
  </svg>
)

const IconUser = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
)

const IconZap = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
)

interface FormData {
  changeTitle: string
  changeDescription: string
  changeType: string
  affectedServices: string
  priority: string
}

const defaultFormData: FormData = {
  changeTitle: '',
  changeDescription: '',
  changeType: 'enhancement',
  affectedServices: '',
  priority: 'medium',
}

const initialSuggestions = [
  'Analyze the impact of upgrading the payment gateway database',
  'What happens if we change the checkout service API?',
  'Show me past incidents with the payment service',
  'Tell me about the system architecture',
]

const App: React.FC = () => {
  // State
  const [mode, setMode] = useState<AnalysisMode>('chat')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: "Hello! I'm the **AI Change Impact Analyzer**. I can help you analyze the impact of proposed system changes, look up past incidents, or answer questions about the architecture.\n\nTry asking me something or use the **Form** mode for detailed analysis.",
    },
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [report, setReport] = useState<ChangeImpactResponse | null>(null)
  const [activeTab, setActiveTab] = useState<TabView>('overview')
  const [changeTypes, setChangeTypes] = useState<ChangeType[]>([])
  const [formData, setFormData] = useState<FormData>(defaultFormData)
  const [suggestions, setSuggestions] = useState(initialSuggestions)
  const [healthStatus, setHealthStatus] = useState<string>('')

  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Load change types on mount
  useEffect(() => {
    loadChangeTypes()
    checkApiHealth()
  }, [])

  const checkApiHealth = async () => {
    try {
      await checkHealth()
      setHealthStatus('connected')
    } catch {
      setHealthStatus('disconnected')
    }
  }

  const loadChangeTypes = async () => {
    try {
      const types = await getChangeTypes()
      setChangeTypes(types)
    } catch {
      // Will use defaults
    }
  }

  // Send chat message
  const handleSendMessage = useCallback(async () => {
    const text = inputValue.trim()
    if (!text || isLoading) return

    setInputValue('')
    setSuggestions([])

    // Add user message
    const userMessage: ChatMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])

    // Show typing indicator
    setIsLoading(true)

    try {
      // First, try the assistant route to classify
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const assistantResponse: AssistantResponse = await assistantRespond(text, history)

      if (assistantResponse.classification === 'change-analysis') {
        // It's a change analysis request
        const result = await analyzeChangeImpact({
          change_title: text.substring(0, 100),
          change_description: text,
          change_type: 'enhancement',
          affected_services: [],
          priority: 'medium',
        })

        setReport(result)
        setActiveTab('overview')
        setMode('chat')

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `✅ **Analysis Complete!**\n\nRisk Score: **${(result.riskScore * 100).toFixed(0)}%** (${result.riskLevel.toUpperCase()})\n\n${result.executiveSummary.substring(0, 300)}...\n\n*Use the report tabs below to explore the full analysis.*`,
          },
        ])
      } else {
        // General conversation
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: assistantResponse.reply,
          },
        ])

        // Update suggestions
        if (assistantResponse.suggested_actions) {
          setSuggestions(assistantResponse.suggested_actions)
        }
      }
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Error:** ${error.message || 'Failed to get response. Please try again.'}`,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [inputValue, isLoading, messages])

  // Submit form-based analysis
  const handleFormSubmit = useCallback(async () => {
    if (!formData.changeTitle.trim() || isLoading) return

    setIsLoading(true)

    try {
      const services = formData.affectedServices
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)

      const result = await analyzeChangeImpact({
        change_title: formData.changeTitle,
        change_description: formData.changeDescription,
        change_type: formData.changeType,
        affected_services: services,
        priority: formData.priority,
      })

      setReport(result)
      setActiveTab('overview')

      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: `**Form Analysis:** ${formData.changeTitle}`,
        },
        {
          role: 'assistant',
          content: `✅ **Analysis Complete!**\n\nRisk Score: **${(result.riskScore * 100).toFixed(0)}%** (${result.riskLevel.toUpperCase()})\n\n${result.executiveSummary.substring(0, 300)}...`,
        },
      ])

      setFormData(defaultFormData)
    } catch (error: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `❌ **Error:** ${error.message || 'Analysis failed.'}`,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }, [formData, isLoading])

  // Handle suggestion click
  const handleSuggestionSelect = useCallback((suggestion: string) => {
    setInputValue(suggestion)
  }, [])

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="app">
      {/* Hero / Banner */}
      <header className="hero">
        <div className="hero-bg" />
        <div className="hero-content container">
          <div className="hero-badge">
            <IconZap />
            <span>AI-Powered Change Analysis</span>
          </div>
          <h1 className="hero-title">
            <span className="text-gradient">Change Impact</span> Analyzer
          </h1>
          <p className="hero-subtitle">
            Multi-agent AI system for assessing risk, impact, and mitigation strategies
            for system changes across 19+ microservices.
          </p>
          <div className="hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">7</span>
              <span className="hero-stat-label">AI Agents</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">19</span>
              <span className="hero-stat-label">Services</span>
            </div>
            <div className="hero-stat">
              <span className="hero-stat-value">6</span>
              <span className="hero-stat-label">Data Sources</span>
            </div>
            <div className="hero-stat">
              <span className={`hero-stat-dot ${healthStatus === 'connected' ? 'connected' : 'disconnected'}`} />
              <span className="hero-stat-label">{healthStatus === 'connected' ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
          {/* Mode Toggle */}
          <div className="mode-toggle">
            <button
              className={`mode-btn ${mode === 'chat' ? 'active' : ''}`}
              onClick={() => setMode('chat')}
            >
              <IconBot />
              Chat Mode
            </button>
            <button
              className={`mode-btn ${mode === 'form' ? 'active' : ''}`}
              onClick={() => setMode('form')}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="9" y1="21" x2="9" y2="9" />
              </svg>
              Form Mode
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main container">
        {/* Chat Area */}
        {mode === 'chat' && (
          <div className="chat-section">
            <div className="chat-messages">
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'assistant' ? <IconBot /> : <IconUser />}
                  </div>
                  <div className="message-bubble">
                    <div className="message-content">
                      {msg.content.split('\n').map((line, j) => (
                        <React.Fragment key={j}>
                          {j > 0 && <br />}
                          {line}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-avatar"><IconBot /></div>
                  <TypingIndicator text="Analyzing" />
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Suggestions */}
            {suggestions.length > 0 && !isLoading && (
              <div className="suggestions-area">
                <SuggestionChips suggestions={suggestions} onSelect={handleSuggestionSelect} />
              </div>
            )}

            {/* Input */}
            <div className="chat-input-area">
              <textarea
                ref={inputRef}
                className="chat-input"
                placeholder="Describe a change or ask a question..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                disabled={isLoading}
              />
              <button
                className="btn btn-primary send-btn"
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
              >
                <IconSend />
              </button>
            </div>
          </div>
        )}

        {/* Form Mode */}
        {mode === 'form' && (
          <div className="form-section">
            <div className="card">
              <h2 className="form-title">Change Impact Analysis</h2>
              <p className="form-desc">
                Fill in the details of your proposed change and we'll analyze the risks,
                impacted services, and recommended mitigation strategies.
              </p>

              <div className="form-grid">
                <div className="form-group full-width">
                  <label>Change Title *</label>
                  <input
                    type="text"
                    placeholder="e.g., Payment Gateway Database Pool Upgrade"
                    value={formData.changeTitle}
                    onChange={(e) => setFormData({ ...formData, changeTitle: e.target.value })}
                  />
                </div>

                <div className="form-group full-width">
                  <label>Change Description</label>
                  <textarea
                    placeholder="Describe the proposed change in detail..."
                    value={formData.changeDescription}
                    onChange={(e) => setFormData({ ...formData, changeDescription: e.target.value })}
                    rows={4}
                  />
                </div>

                <div className="form-group">
                  <label>Change Type</label>
                  <select
                    value={formData.changeType}
                    onChange={(e) => setFormData({ ...formData, changeType: e.target.value })}
                  >
                    <option value="enhancement">Enhancement</option>
                    <option value="infrastructure">Infrastructure</option>
                    <option value="bugfix">Bug Fix</option>
                    <option value="security">Security</option>
                    <option value="rollback">Rollback</option>
                    <option value="data">Data Update</option>
                    <option value="policy">Policy Change</option>
                    <option value="research">Research</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Priority</label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div className="form-group full-width">
                  <label>Affected Services (comma-separated)</label>
                  <input
                    type="text"
                    placeholder="e.g., payment-gateway, order-service"
                    value={formData.affectedServices}
                    onChange={(e) => setFormData({ ...formData, affectedServices: e.target.value })}
                  />
                </div>
              </div>

              <button
                className="btn btn-primary form-submit"
                onClick={handleFormSubmit}
                disabled={isLoading || !formData.changeTitle.trim()}
              >
                {isLoading ? (
                  <>
                    <span className="animate-pulse">Analyzing...</span>
                  </>
                ) : (
                  <>
                    <IconZap />
                    Analyze Change Impact
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Report Section */}
        {report && (
          <div className="report-section animate-fadeIn">
            <div className="report-header">
              <h2>Analysis Report</h2>
              <span className="report-id">ID: {report.analysisId}</span>
              <span className="report-mode-badge">
                {report.mockMode ? '🔧 Mock Mode' : '🤖 AI Analysis'}
              </span>
            </div>

            <div className="report-layout">
              <div className="report-sidebar">
                <RiskGauge
                  score={report.riskScore}
                  level={report.riskLevel}
                  confidence={report.confidence}
                />
                <div className="report-quick-stats">
                  <div className="quick-stat">
                    <span className="quick-stat-label">Services</span>
                    <span className="quick-stat-value">{report.impactedServices.length}</span>
                  </div>
                  <div className="quick-stat">
                    <span className="quick-stat-label">Risks</span>
                    <span className="quick-stat-value">{report.potentialRisks.length}</span>
                  </div>
                  <div className="quick-stat">
                    <span className="quick-stat-label">Tests</span>
                    <span className="quick-stat-value">{report.recommendedTests.length}</span>
                  </div>
                  <div className="quick-stat">
                    <span className="quick-stat-label">Time</span>
                    <span className="quick-stat-value">{(report.processingTimeMs / 1000).toFixed(1)}s</span>
                  </div>
                </div>
              </div>

              <div className="report-main">
                <ReportTabs
                  report={report}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container footer-content">
          <p>AI Change Impact Analyzer v1.0.0</p>
          <p className="footer-mode">
            Running in <strong>{report?.mockMode ? 'Mock' : 'Live'}</strong> mode
            {' · '}
            <a href="https://github.com/org/change-impact-analyzer" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </p>
        </div>
      </footer>

      {/* Global App Styles */}
      <style>{`
        .app {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
        }

        /* Hero Banner */
        .hero {
          position: relative;
          overflow: hidden;
          padding: 60px 0 40px;
          text-align: center;
        }
        .hero-bg {
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(6, 182, 212, 0.1) 50%, transparent 100%);
          animation: gradientShift 8s ease infinite;
          background-size: 200% 200%;
        }
        .hero-content {
          position: relative;
          z-index: 1;
        }
        .hero-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 16px;
          background: rgba(99, 102, 241, 0.15);
          border: 1px solid rgba(99, 102, 241, 0.3);
          border-radius: 20px;
          color: #818cf8;
          font-size: 0.85rem;
          margin-bottom: 20px;
        }
        .hero-title {
          font-size: 3rem;
          font-weight: 800;
          margin-bottom: 12px;
          line-height: 1.2;
        }
        @media (max-width: 640px) {
          .hero-title { font-size: 2rem; }
        }
        .hero-subtitle {
          color: #94a3b8;
          font-size: 1.1rem;
          max-width: 600px;
          margin: 0 auto 30px;
          line-height: 1.7;
        }
        .hero-stats {
          display: flex;
          justify-content: center;
          gap: 30px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }
        .hero-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .hero-stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #f1f5f9;
        }
        .hero-stat-label {
          font-size: 0.8rem;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .hero-stat-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
        }
        .hero-stat-dot.connected { background: #10b981; box-shadow: 0 0 8px rgba(16,185,129,0.5); }
        .hero-stat-dot.disconnected { background: #ef4444; box-shadow: 0 0 8px rgba(239,68,68,0.5); }

        /* Mode Toggle */
        .mode-toggle {
          display: inline-flex;
          gap: 4px;
          background: #1e293b;
          border-radius: 10px;
          padding: 4px;
          border: 1px solid #334155;
        }
        .mode-btn {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 8px 18px;
          border: none;
          background: transparent;
          color: #94a3b8;
          font-size: 0.85rem;
          font-weight: 500;
          cursor: pointer;
          border-radius: 8px;
          transition: all 0.2s ease;
          font-family: inherit;
        }
        .mode-btn.active {
          background: #6366f1;
          color: white;
        }
        .mode-btn:hover:not(.active) {
          color: #f1f5f9;
          background: rgba(99, 102, 241, 0.1);
        }

        /* Main */
        .main {
          flex: 1;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        /* Chat */
        .chat-section {
          display: flex;
          flex-direction: column;
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 16px;
          overflow: hidden;
          max-width: 800px;
          margin: 0 auto;
          width: 100%;
        }
        .chat-messages {
          flex: 1;
          padding: 20px;
          overflow-y: auto;
          max-height: 500px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .message {
          display: flex;
          gap: 12px;
          animation: fadeIn 0.3s ease;
        }
        .message.user {
          flex-direction: row-reverse;
        }
        .message-avatar {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: #334155;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .message.user .message-avatar {
          background: rgba(99, 102, 241, 0.2);
          color: #818cf8;
        }
        .message-bubble {
          max-width: 75%;
          padding: 12px 16px;
          background: #334155;
          border-radius: 12px;
          border: 1px solid #475569;
        }
        .message.user .message-bubble {
          background: rgba(99, 102, 241, 0.15);
          border-color: rgba(99, 102, 241, 0.3);
        }
        .message-content {
          font-size: 0.9rem;
          line-height: 1.6;
          color: #cbd5e1;
          white-space: pre-wrap;
        }
        .message-content strong {
          color: #f1f5f9;
        }

        .suggestions-area {
          padding: 0 20px 12px;
        }

        .chat-input-area {
          display: flex;
          gap: 8px;
          padding: 12px 20px;
          border-top: 1px solid #334155;
          background: #0f172a;
        }
        .chat-input {
          flex: 1;
          background: #334155;
          border: 1px solid #475569;
          border-radius: 8px;
          padding: 10px 14px;
          color: #f1f5f9;
          font-size: 0.9rem;
          resize: none;
          min-height: 40px;
          max-height: 120px;
          font-family: inherit;
        }
        .chat-input:focus {
          outline: none;
          border-color: #6366f1;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .chat-input::placeholder {
          color: #64748b;
        }
        .send-btn {
          padding: 10px 16px;
          border-radius: 8px;
        }

        /* Form */
        .form-section {
          max-width: 600px;
          margin: 0 auto;
          width: 100%;
        }
        .form-title {
          font-size: 1.3rem;
          margin-bottom: 8px;
        }
        .form-desc {
          color: #94a3b8;
          font-size: 0.9rem;
          margin-bottom: 20px;
        }
        .form-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .form-group.full-width {
          grid-column: 1 / -1;
        }
        .form-group label {
          font-size: 0.85rem;
          color: #94a3b8;
          font-weight: 500;
        }
        .form-submit {
          margin-top: 20px;
          width: 100%;
          padding: 12px;
          font-size: 1rem;
        }

        /* Report */
        .report-section {
          max-width: 1200px;
          margin: 0 auto;
          width: 100%;
        }
        .report-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;
          flex-wrap: wrap;
        }
        .report-header h2 {
          font-size: 1.4rem;
        }
        .report-id {
          font-size: 0.8rem;
          color: #64748b;
          font-family: monospace;
        }
        .report-mode-badge {
          padding: 4px 10px;
          background: rgba(245, 158, 11, 0.15);
          border: 1px solid rgba(245, 158, 11, 0.3);
          border-radius: 6px;
          color: #fcd34d;
          font-size: 0.8rem;
        }
        .report-layout {
          display: grid;
          grid-template-columns: 200px 1fr;
          gap: 20px;
        }
        @media (max-width: 768px) {
          .report-layout {
            grid-template-columns: 1fr;
          }
        }
        .report-sidebar {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .report-quick-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 8px;
        }
        .quick-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 10px;
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 8px;
        }
        .quick-stat-label {
          font-size: 0.7rem;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }
        .quick-stat-value {
          font-size: 1.1rem;
          font-weight: 700;
          color: #f1f5f9;
        }
        .report-main {
          min-width: 0;
        }

        /* Footer */
        .footer {
          padding: 20px 0;
          border-top: 1px solid #334155;
          margin-top: 40px;
        }
        .footer-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.85rem;
          color: #64748b;
        }
        .footer-mode a {
          color: #818cf8;
          text-decoration: none;
        }
        .footer-mode a:hover {
          text-decoration: underline;
        }
        @media (max-width: 640px) {
          .footer-content { flex-direction: column; gap: 8px; text-align: center; }
        }
      `}</style>
    </div>
  )
}

export default App

