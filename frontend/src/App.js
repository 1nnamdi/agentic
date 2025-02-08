import { useState } from 'react'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState([
    { role: 'assistant', content: 'Hello! To start using this app, you need to enter a url to get started.' }
  ]);


  const [url, setUrl] = useState('')

  const API_BASE_URL = process.env.REACT_APP_API_BASE || 'http://16.171.200.180';

  const handleQA = async (e) => {
    e.preventDefault();
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

  const handleCrawl = async (e) => {
    e.preventDefault();
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

  return (
    <div className="chat-container">
      <form onSubmit={handleCrawl} className="url-form">
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter URL to crawl..."
          className="url-input"
        />
        <button type="submit" className="crawl-button">
          Crawl
        </button>
      </form>
      
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
      
      <form onSubmit={handleQA} className="input-form">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Type your message here..."
          className="chat-input"
        />
        <button type="submit" className="send-button">
          Send
        </button>
      </form>
    </div>
  )
}

export default App
