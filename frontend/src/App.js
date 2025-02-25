import { useState } from 'react'
import { FaSearch, FaCode, FaPaintBrush, FaFileAlt, FaLink, FaPhone } from 'react-icons/fa'
import './App.css'

function App() {
  
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState([
    { role: 'assistant', content: 'Hello! To start using this app, you need to enter a url to get started.' }
  ]);
  const [url, setUrl] = useState('')
  const [activeMode, setActiveMode] = useState('chat')

  const API_BASE_URL = process.env.REACT_APP_API_BASE; //|| 'http://16.171.200.180';


  const handleSubmit = (e) => {
    e.preventDefault()
    if (!question.trim()) return

    if (activeMode === 'web-search') {
      handleWebSearch(url)
    } else { 
      handleQA(question)
    }
    setQuestion('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const handleWebSearch = (searchUrl) => {
    if (!searchUrl.startsWith('http://') && !searchUrl.startsWith('https://')) {
      searchUrl = `https://${searchUrl}`
    }
    handleCrawl(searchUrl)
  }

  const handleCrawl = async () => {
    console.log(url)
    //e.preventDefault();
    if (!url.trim()) return;

    try {
      const response = await fetch(`${API_BASE_URL}:8000/crawl`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        throw new Error('Failed to crawl the URL');
      }

      const data = await response.json();
      const newMessages = [
        ...answer,
        { role: 'user', content: `Crawling URL: ${url}` },
        { role: 'assistant', content: data.message }
      ];
      setAnswer(newMessages);
    } catch (error) {
      const newMessages = [
        ...answer,
        { role: 'user', content: `Crawling URL: ${url}` },
        { role: 'assistant', content: `Error: ${error.message}` }
      ];
      setAnswer(newMessages);
    }

    setUrl('');
  };

  const handleQA = async (e) => {
   
    //e.preventDefault();
    if (!question.trim()) return;

    try {
      
        const response = await fetch(`${API_BASE_URL}:8000/ask?question=${encodeURIComponent(question)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get an answer');
      }

      const data = await response.json();
      const newMessages = [
        ...answer,
        { role: 'user', content: question },
        { role: 'assistant', content: data.answer }
      ];
      setAnswer(newMessages);
    } catch (error) {
      const newMessages = [
        ...answer,
        { role: 'user', content: question },
        { role: 'assistant', content: `Error: ${error.message}` }
      ];
      setAnswer(newMessages);
    }

    setQuestion('');
  };


  const handleCall = () => {
    const newMessages = [
      ...answer,
      { role: 'system', content: 'Initiating voice call...' }
    ]
    setAnswer(newMessages)
  }

  const tools = [
    { id: 'canvas', icon: FaFileAlt, label: 'Canvas' },
    { id: 'web-search', icon: FaSearch, label: 'Web search' },
    { id: 'image', icon: FaPaintBrush, label: 'Image generation' },
    { id: 'code', icon: FaCode, label: 'Code Interpreter' }
  ]

  return (
    <div className="chat-container">
     
      
      <div className="chat-messages">
        {answer.map((message, index) => (
          <div
            key={index}
            className={`message ${message.role === 'user' ? 'user-message' : 'assistant-message'}`}
          >
            <div className="message-content">
              {message.content}
            </div>
          </div>
        ))}
      </div>
      
      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <textarea
              value={question}
              onChange={(e) => {
                if (activeMode === 'web-search') {
                  setUrl(e.target.value)
                } else {
                  setQuestion(e.target.value)
                }
              }}
              onKeyDown={handleKeyDown}
              placeholder={activeMode === 'web-search' ? 'Enter a URL to search...' : 'Ask a question...'}
              className="chat-input"
              rows={3}
            />
            <button type="submit" className="send-button">
              {activeMode === 'web-search' ? 'Search' : 'Send'}
            </button>
            <button 
              type="button" 
              onClick={handleCall}
              className="call-button"
              title="Start voice call"
            >
              <FaPhone />
            </button>
          </div>
        </form>
        
        <div className="tools-container">
          {tools.map((tool) => {
            const Icon = tool.icon
            return (
              <button
                key={tool.id}
                type="button"
                className={`tool-button ${activeMode === tool.id ? 'active' : ''}`}
                onClick={() => setActiveMode(activeMode === tool.id ? 'chat':tool.id)}
                title={tool.label}
              >
                <Icon />
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default App
