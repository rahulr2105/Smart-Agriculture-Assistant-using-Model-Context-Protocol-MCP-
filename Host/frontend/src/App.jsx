import React, { useState, useEffect } from 'react';
import { 
  Sprout, 
  Search, 
  RefreshCw, 
  Play, 
  Copy, 
  Check, 
  Server, 
  Terminal, 
  Info, 
  AlertCircle,
  MessageSquare,
  Send,
  ChevronDown,
  ChevronUp,
  Cpu,
  Sparkles,
  Brain
} from 'lucide-react';

function App() {
  const [tools, setTools] = useState([]);
  const [serverStatus, setServerStatus] = useState({});
  const [selectedTool, setSelectedTool] = useState(null);
  const [formInputs, setFormInputs] = useState({});
  const [executing, setExecuting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [loadingTools, setLoadingTools] = useState(true);
  const [copied, setCopied] = useState(false);

  // Supervisor Chat State
  const [activeTab, setActiveTab] = useState('explorer');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [expandedSteps, setExpandedSteps] = useState({});

  const sendChatMessage = async (e, customMsg = null) => {
    if (e) e.preventDefault();
    const query = customMsg || chatInput;
    if (!query.trim()) return;

    const userMsg = { role: 'user', content: query };
    // If it's a suggestion click, update messages list with user message
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput('');
    setChatLoading(true);
    setChatError(null);

    // Prepare history to send to backend
    // Only send basic role/content pairs to avoid sending full trace data
    const history = chatMessages.map(m => ({
      role: m.role,
      content: m.content || ''
    }));

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: query,
          history: history
        })
      });

      const data = await response.json();

      if (response.ok) {
        setChatMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          steps: data.steps
        }]);
      } else {
        setChatError(data.detail || 'An error occurred talking to the supervisor.');
      }
    } catch (err) {
      setChatError(err.message || 'Failed to connect to the server.');
    } finally {
      setChatLoading(false);
    }
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatError(null);
  };

  const toggleStep = (msgIndex, stepIndex) => {
    const key = `${msgIndex}-${stepIndex}`;
    setExpandedSteps(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };


  // Fetch tools and server status
  const fetchData = async () => {
    try {
      setLoadingTools(true);
      const [toolsRes, statusRes] = await Promise.all([
        fetch('/api/tools'),
        fetch('/api/status')
      ]);

      if (toolsRes.ok) {
        const toolsData = await toolsRes.json();
        setTools(toolsData);
      } else {
        console.error("Failed to fetch tools");
      }

      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setServerStatus(statusData.servers || {});
      }
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoadingTools(false);
    }
  };

  // Poll server status every 6 seconds
  useEffect(() => {
    fetchData();
    const interval = setInterval(async () => {
      try {
        const statusRes = await fetch('/api/status');
        if (statusRes.ok) {
          const statusData = await statusRes.json();
          setServerStatus(statusData.servers || {});
        }
      } catch (err) {
        console.error("Error polling server status:", err);
      }
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  // Set default form values when a tool is selected
  useEffect(() => {
    if (selectedTool) {
      const defaults = {};
      const schema = selectedTool.inputSchema || {};
      const properties = schema.properties || {};
      
      Object.keys(properties).forEach(key => {
        defaults[key] = properties[key].default !== undefined ? properties[key].default : '';
      });
      
      setFormInputs(defaults);
      setResult(null);
      setError(null);
    }
  }, [selectedTool]);

  const handleInputChange = (key, value) => {
    setFormInputs(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const executeTool = async (e) => {
    e.preventDefault();
    if (!selectedTool) return;

    setExecuting(true);
    setResult(null);
    setError(null);

    try {
      const response = await fetch(`/api/tools/${selectedTool.name}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formInputs)
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data.result);
      } else {
        setError(data.detail || "An error occurred during execution.");
      }
    } catch (err) {
      setError(err.message || "Failed to connect to the server.");
    } finally {
      setExecuting(false);
    }
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Filter tools based on search term and category
  const filteredTools = tools.filter(tool => {
    const matchesSearch = tool.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          tool.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || tool.server === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const categories = ['all', ...Object.keys(serverStatus)];

  // Helper to clean tool name for presentation
  const formatToolName = (rawName) => {
    // e.g. crop_recommend_crop_tool -> Recommend Crop
    let name = rawName;
    for (const key of Object.keys(serverStatus)) {
      if (name.startsWith(`${key}_`)) {
        name = name.substring(key.length + 1);
        break;
      }
    }
    return name
      .replace(/_tool$/, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, c => c.toUpperCase());
  };

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="brand-section">
          <Sprout className="brand-icon" size={32} />
          <div className="brand-title">
            <h1>MCP Host Portal</h1>
            <p>Model Context Protocol Dashboard</p>
          </div>
        </div>

        <div className="header-tabs">
          <button 
            className={`header-tab ${activeTab === 'explorer' ? 'active' : ''}`}
            onClick={() => setActiveTab('explorer')}
          >
            Tools Explorer
          </button>
          <button 
            className={`header-tab ${activeTab === 'supervisor' ? 'active' : ''}`}
            onClick={() => setActiveTab('supervisor')}
          >
            Supervisor Agent
          </button>
        </div>

        <div className="status-monitor">
          <span className="status-label">Server Nodes:</span>
          <div className="status-badges">
            {Object.entries(serverStatus).map(([name, status]) => (
              <div key={name} className={`status-badge ${status}`}>
                <div className="status-dot"></div>
                <span style={{ textTransform: 'capitalize' }}>{name}</span>
              </div>
            ))}
            {Object.keys(serverStatus).length === 0 && (
              <span className="status-badge offline">
                <div className="status-dot"></div>
                No Servers Detected
              </span>
            )}
          </div>
          <button className="btn-icon" onClick={fetchData} title="Refresh Dashboard">
            <RefreshCw size={14} />
          </button>
        </div>
      </header>

      {/* Main Content depending on active tab */}
      {activeTab === 'explorer' ? (
        <main className="dashboard-grid">
          {/* Left Sidebar - Tools Explorer */}
          <section className="sidebar">
            <div className="sidebar-header">
              <div className="search-container">
                <Search className="search-icon" size={16} />
                <input 
                  type="text" 
                  placeholder="Search tools..." 
                  className="search-input"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="category-filters">
                {categories.map(cat => (
                  <button
                    key={cat}
                    className={`category-tab ${selectedCategory === cat ? 'active' : ''}`}
                    onClick={() => setSelectedCategory(cat)}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            <div className="tool-list">
              {loadingTools ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '2rem' }}>
                  <div className="loading-spinner"></div>
                </div>
              ) : filteredTools.length > 0 ? (
                filteredTools.map(tool => (
                  <div 
                    key={tool.name}
                    className={`tool-card ${selectedTool?.name === tool.name ? 'active' : ''}`}
                    onClick={() => setSelectedTool(tool)}
                  >
                    <div className="tool-card-header">
                      <span className="tool-card-title">{formatToolName(tool.name)}</span>
                      <span className={`server-tag ${tool.server}`}>{tool.server}</span>
                    </div>
                    <p className="tool-card-desc">{tool.description}</p>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem', fontSize: '0.875rem' }}>
                  No tools match your criteria.
                </div>
              )}
            </div>
          </section>

          {/* Right Detail & Execution Panel */}
          <section className="detail-panel">
            {selectedTool ? (
              <div className="execution-center">
                {/* Header Details */}
                <div className="tool-detail-header">
                  <div className="tool-detail-meta">
                    <span className={`server-tag ${selectedTool.server}`}>{selectedTool.server}</span>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {selectedTool.name}
                    </span>
                  </div>
                  <h2 className="tool-detail-title">{formatToolName(selectedTool.name)}</h2>
                  <p className="tool-detail-desc">{selectedTool.description}</p>
                </div>

                {/* Workspaces: Form & Results Split */}
                <div className="workspace-split">
                  {/* Form Input Section */}
                  <div className="form-section">
                    <h3 className="form-title">Parameters</h3>
                    <form onSubmit={executeTool} className="parameter-form">
                      {selectedTool.inputSchema?.properties && Object.keys(selectedTool.inputSchema.properties).length > 0 ? (
                        Object.entries(selectedTool.inputSchema.properties).map(([key, prop]) => {
                          const isRequired = selectedTool.inputSchema.required?.includes(key);
                          return (
                            <div className="form-group" key={key}>
                              <label className="form-label">
                                {prop.title || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                                {isRequired && <span className="required-star">*</span>}
                              </label>
                              {prop.type === 'integer' || prop.type === 'number' ? (
                                <input
                                  type="number"
                                  className="form-input"
                                  placeholder={prop.description || `Enter ${key}`}
                                  required={isRequired}
                                  value={formInputs[key] || ''}
                                  onChange={(e) => handleInputChange(key, e.target.value)}
                                />
                              ) : (
                                <input
                                  type="text"
                                  className="form-input"
                                  placeholder={prop.description || `Enter ${key}`}
                                  required={isRequired}
                                  value={formInputs[key] || ''}
                                  onChange={(e) => handleInputChange(key, e.target.value)}
                                />
                              )}
                              {prop.description && <span className="form-help">{prop.description}</span>}
                            </div>
                          );
                        })
                      ) : (
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '1rem 0' }}>
                          This tool does not require any parameters.
                        </div>
                      )}

                      <button 
                        type="submit" 
                        className="btn-execute"
                        disabled={executing}
                      >
                        {executing ? (
                          <>
                            <div className="loading-spinner" style={{ width: '16px', height: '16px' }}></div>
                            <span>Running Tool...</span>
                          </>
                        ) : (
                          <>
                            <Play size={16} fill="currentColor" />
                            <span>Run Tool</span>
                          </>
                        )}
                      </button>
                    </form>
                  </div>

                  {/* Results Section */}
                  <div className="result-section">
                    <div className="result-header">
                      <h3 className="result-title">Output Console</h3>
                      {result && (
                        <button 
                          className="btn-icon" 
                          onClick={copyToClipboard}
                          title="Copy to clipboard"
                        >
                          {copied ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                        </button>
                      )}
                    </div>

                    <div className="result-display-wrapper">
                      {executing && (
                        <div className="result-empty">
                          <div className="loading-spinner" style={{ width: '32px', height: '32px', marginBottom: '1rem' }}></div>
                          <p style={{ color: 'var(--text-secondary)' }}>Executing request on MCP server...</p>
                        </div>
                      )}

                      {!executing && result && (
                        <div className="result-content">
                          {result}
                        </div>
                      )}

                      {!executing && error && (
                        <div className="result-content error">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                            <AlertCircle size={16} />
                            <span style={{ fontWeight: '600' }}>Execution Failed</span>
                          </div>
                          {error}
                        </div>
                      )}

                      {!executing && !result && !error && (
                        <div className="result-empty">
                          <Terminal className="placeholder-icon" size={40} />
                          <p>Fill out the parameters and click <strong>Run Tool</strong> to see outputs.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="placeholder-container">
                <Sprout className="placeholder-icon" size={64} />
                <h3>Welcome to MCP Host Dashboard</h3>
                <p>Select an active tool from the explorer on the left to review its schema parameters and run queries.</p>
              </div>
            )}
          </section>
        </main>
      ) : (
        <div className="chat-container">
          <div className="chat-workspace">
            {/* Left Chat Window */}
            <div className="chat-main">
              <div className="chat-messages">
                {chatMessages.length === 0 ? (
                  <div className="chat-empty">
                    <Brain className="chat-empty-icon" size={64} />
                    <h3>Supervisor Chat Agent</h3>
                    <p>
                      Ask questions across multiple MCP domains. The supervisor agent uses <strong>gpt-4o-mini</strong> to choose the correct model servers (crop, disease, weather, market) to answer your question.
                    </p>
                    <div className="chat-suggestions">
                      <button className="suggestion-card" onClick={() => sendChatMessage(null, "What crop should I plant if temperature is 28°C and humidity is 75%?")}>
                        <span>Suggest Crop</span>
                        "What crop should I plant if temperature is 28°C and humidity is 75%?"
                      </button>
                      <button className="suggestion-card" onClick={() => sendChatMessage(null, "What is the current market price of wheat and how is the weather?")}>
                        <span>Market & Weather</span>
                        "What is the current market price of wheat and how is the weather?"
                      </button>
                      <button className="suggestion-card" onClick={() => sendChatMessage(null, "How do I identify and treat leaf blast disease on my rice crop?")}>
                        <span>Disease Diagnosis</span>
                        "How do I identify and treat leaf blast disease on my rice crop?"
                      </button>
                      <button className="suggestion-card" onClick={() => sendChatMessage(null, "Check the weather for crop planning recommendations.")}>
                        <span>General Planning</span>
                        "Check the weather for crop planning recommendations."
                      </button>
                    </div>
                  </div>
                ) : (
                  chatMessages.map((msg, index) => (
                    <div key={index} className={`chat-bubble ${msg.role}`}>
                      <div className="message-meta">
                        {msg.role === 'user' ? (
                          <>You</>
                        ) : (
                          <>
                            <Brain size={12} style={{ color: 'var(--primary)' }} />
                            <span>Supervisor</span>
                          </>
                        )}
                      </div>
                      
                      {/* If the message has reasoning trace steps, render them before the final text */}
                      {msg.role === 'assistant' && msg.steps && msg.steps.length > 0 && (
                        <div className="reasoning-trace">
                          {msg.steps.map((step, stepIdx) => {
                            const stepKey = `${index}-${stepIdx}`;
                            const isExpanded = !!expandedSteps[stepKey];
                            return (
                              <div key={stepIdx} className="trace-step">
                                <div className="trace-header" onClick={() => toggleStep(index, stepIdx)}>
                                  <div className="trace-title">
                                    <Cpu size={14} style={{ color: 'var(--accent)' }} />
                                    <span>Model Selected: {step.name.split('_')[0].toUpperCase()}</span>
                                    <span className="trace-badge">{formatToolName(step.name)}</span>
                                  </div>
                                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                </div>
                                
                                {isExpanded && (
                                  <div className="trace-body">
                                    <div className="trace-args">
                                      <span className="trace-label">Input Arguments</span>
                                      <pre className="trace-code">{JSON.stringify(step.args, null, 2)}</pre>
                                    </div>
                                    <div className="trace-result">
                                      <span className="trace-label">Response Output</span>
                                      <pre className="trace-code">{step.result}</pre>
                                    </div>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}

                      {msg.content && (
                        <div className="message-content">
                          {msg.content}
                        </div>
                      )}
                    </div>
                  ))
                )}

                {chatLoading && (
                  <div className="chat-bubble assistant">
                    <div className="message-meta">
                      <Brain size={12} style={{ color: 'var(--primary)' }} />
                      <span>Supervisor is thinking...</span>
                    </div>
                    <div className="message-content" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="typing-indicator">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                      </div>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Consulting MCP nodes...</span>
                    </div>
                  </div>
                )}

                {chatError && (
                  <div className="chat-bubble assistant">
                    <div className="message-meta" style={{ color: 'var(--error)' }}>
                      <AlertCircle size={12} />
                      <span>Error</span>
                    </div>
                    <div className="message-content error" style={{ background: 'var(--error-bg)', border: '1px solid var(--error)', color: 'var(--error)', borderTopLeftRadius: '0.25rem' }}>
                      {chatError}
                    </div>
                  </div>
                )}
              </div>

              {/* Chat Input Container */}
              <div className="chat-input-container">
                <form onSubmit={sendChatMessage} className="chat-form">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask the Supervisor Agent a question..."
                    className="chat-input"
                    disabled={chatLoading}
                  />
                  <button type="submit" className="chat-send-btn" disabled={chatLoading || !chatInput.trim()}>
                    <Send size={16} />
                    <span>Send</span>
                  </button>
                </form>
              </div>
            </div>

            {/* Right Chat Sidebar - Configuration / Status */}
            <div className="chat-sidebar">

              <div className="sidebar-card">
                <div className="sidebar-card-title">
                  <Server size={16} style={{ color: 'var(--primary)' }} />
                  <span>Supervisor Info</span>
                </div>
                <p>The supervisor agent dynamically routes questions to domain tools. It acts as an LLM orchestrator across these domains:</p>
                <ul style={{ fontSize: '0.8rem', paddingLeft: '1.25rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                  <li><strong style={{ color: 'var(--text-primary)' }}>Crop Node:</strong> Planning & recommendation</li>
                  <li><strong style={{ color: 'var(--text-primary)' }}>Disease Node:</strong> Diagnosing crop sickness</li>
                  <li><strong style={{ color: 'var(--text-primary)' }}>Weather Node:</strong> Temperature & rain details</li>
                  <li><strong style={{ color: 'var(--text-primary)' }}>Market Node:</strong> Buying/selling prices</li>
                </ul>
              </div>

              {chatMessages.length > 0 && (
                <button
                  className="category-tab"
                  style={{ width: '100%', padding: '0.75rem', justifyContent: 'center', marginTop: 'auto' }}
                  onClick={clearChat}
                >
                  Clear Chat History
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
