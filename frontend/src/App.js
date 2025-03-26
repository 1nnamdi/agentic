import { useState, useRef, useEffect } from 'react'
import { FaSearch, FaCode, FaPaintBrush, FaFileAlt, FaLink, FaPhone, FaArrowDown, FaMicrophone, FaStop } from 'react-icons/fa'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState([
    { role: 'assistant', content: 'Hello! To start using this app, you need to enter a url to get started.' }
  ]);
  const [url, setUrl] = useState('')
  const [activeMode, setActiveMode] = useState('chat')
  
  // Voice chat state
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [isPlaying, setIsPlaying] = useState(false)
  const mediaRecorderRef = useRef(null)
  const websocketRef = useRef(null)
  const audioChunksRef = useRef([])
  const audioContextRef = useRef(null)

  const API_BASE_URL = process.env.REACT_APP_API_BASE;

  const [showScrollButton, setShowScrollButton] = useState(false)
  const messagesEndRef = useRef(null)
  const chatMessagesRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleScroll = () => {
    if (!chatMessagesRef.current) return
    
    const { scrollTop, scrollHeight, clientHeight } = chatMessagesRef.current
    const isScrolledUp = scrollHeight - scrollTop - clientHeight > 100
    setShowScrollButton(isScrolledUp)
  }

  useEffect(() => {
    const chatMessages = chatMessagesRef.current
    if (chatMessages) {
      chatMessages.addEventListener('scroll', handleScroll)
      return () => chatMessages.removeEventListener('scroll', handleScroll)
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [answer])
  
  // Clean up WebSocket and audio resources when component unmounts
  useEffect(() => {
    return () => {
      // Close WebSocket connection
      if (websocketRef.current) {
        websocketRef.current.close()
      }
      
      // Stop recording if active
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
      
      // Close audio context
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  const handleSubmit = (e) => {
    e.preventDefault()
    //if (!question.trim() || !url.trim()) return

    if (activeMode === 'web-search') {
      handleWebSearch(url);
      setUrl('');
    } else {
      handleQA(question)
      setQuestion('');
    }
   
    
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

  // Initialize WebSocket connection
  const initializeWebSocket = () => {
    // Close any existing connection
    if (websocketRef.current) {
      websocketRef.current.close()
    }

    // Create new WebSocket connection
    const wsUrl = `ws://${API_BASE_URL.replace('http://', '')}:8000/voice-chat`
    websocketRef.current = new WebSocket(wsUrl)

    // Set up event handlers
    websocketRef.current.onopen = () => {
      console.log('WebSocket connection established')
    }

    websocketRef.current.onmessage = async (event) => {
      try {
        // Handle text messages (JSON)
        if (typeof event.data === 'string') {
          const data = JSON.parse(event.data)
          
          if (data.status === 'ready') {
            // Server is ready to receive audio
            if (audioChunksRef.current.length > 0) {
              const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
              websocketRef.current.send(await audioBlob.arrayBuffer())
              setIsProcessing(true)
            }
          } 
          else if (data.type === 'transcription') {
            // Update transcript and add user message
            setTranscript(data.text)
            const newMessages = [
              ...answer,
              { role: 'user', content: data.text }
            ]
            setAnswer(newMessages)
            setIsProcessing(true)
          } 
          else if (data.type === 'response') {
            // Add assistant response message
            const newMessages = [
              ...answer,
              { role: 'user', content: transcript },
              { role: 'assistant', content: data.text }
            ]
            setAnswer(newMessages)
          }
        } 
        // Handle binary messages (audio)
        else if (event.data instanceof Blob) {
          setIsPlaying(true)
          
          // Play audio response
          if (!audioContextRef.current) {
            audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
          }
          
          const arrayBuffer = await event.data.arrayBuffer()
          const audioBuffer = await audioContextRef.current.decodeAudioData(arrayBuffer)
          
          const source = audioContextRef.current.createBufferSource()
          source.buffer = audioBuffer
          source.connect(audioContextRef.current.destination)
          
          source.onended = () => {
            setIsPlaying(false)
            setIsProcessing(false)
            
            // Tell server we're done playing audio
            websocketRef.current.send(JSON.stringify({ status: 'complete' }))
          }
          
          source.start(0)
        }
      } catch (error) {
        console.error('Error processing message:', error)
        setIsProcessing(false)
      }
    }

    websocketRef.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsRecording(false)
      setIsProcessing(false)
    }

    websocketRef.current.onclose = () => {
      console.log('WebSocket connection closed')
      setIsRecording(false)
      setIsProcessing(false)
    }
  }

  // Start recording audio
  const startRecording = async () => {
    try {
      // Initialize WebSocket
      initializeWebSocket()
      
      // Reset state
      audioChunksRef.current = []
      setTranscript('')
      setIsRecording(true)
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      
      // Create and configure MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream)
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      mediaRecorderRef.current.onstop = () => {
        // Stop all tracks in the stream
        stream.getTracks().forEach(track => track.stop())
        
        // If WebSocket is ready, send the audio data
        if (websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          const newMessage = { role: 'system', content: 'Processing audio...' }
          setAnswer(prev => [...prev, newMessage])
        }
      }
      
      // Start recording
      mediaRecorderRef.current.start(100) // Collect data in 100ms chunks
    } catch (error) {
      console.error('Error starting recording:', error)
      setIsRecording(false)
    }
  }

  // Stop recording audio
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop()
      setIsRecording(false)
    }
  }

  const handleCall = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }
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

  const tools = [
    { id: 'document', icon: FaFileAlt, label: 'Document chat' },
    { id: 'web-search', icon: FaSearch, label: 'Web search' },
    { id: 'image', icon: FaPaintBrush, label: 'Image generation' },
    { id: 'code', icon: FaCode, label: 'Code Interpreter' }
  ]

  return (
    <div className="chat-container">
      {/* {activeMode === 'web-search' && (
        setUrl(e.target.value)
      )} */}
      
      <div className="chat-messages" ref={chatMessagesRef}>
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
        <div ref={messagesEndRef} />
        {showScrollButton && (
          <button onClick={scrollToBottom} className="scroll-bottom-button">
            <FaArrowDown />
          </button>
        )}
      </div>
      
      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <textarea
              type="url"
              value={activeMode === 'web-search' ? url : question}
              onChange={(e) => {
                if (activeMode === 'web-search') {
                  setUrl(e.target.value);
                } else {
                  setQuestion(e.target.value);          
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
              className={`call-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
              title={isRecording ? "Stop recording" : "Start voice recording"}
              disabled={isProcessing || isPlaying}
            >
              {isRecording ? <FaStop /> : <FaMicrophone />}
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