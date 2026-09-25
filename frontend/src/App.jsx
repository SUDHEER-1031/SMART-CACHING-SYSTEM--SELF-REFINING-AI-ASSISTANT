import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // File Upload State for RAG
  const [selectedFile, setSelectedFile] = useState(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState('')

  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // File Upload Handlers
  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0])
      setUploadStatus('')
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setIsUploading(true)
    setUploadStatus('Uploading and indexing document...')

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json().catch(() => ({}))

      if (response.ok) {
        setUploadStatus('✅ ' + (data.message || 'Document indexed successfully!'))
        setSelectedFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      } else {
        setUploadStatus('❌ ' + (data.detail || 'Upload failed.'))
      }
    } catch (error) {
      console.error("Upload Error:", error)
      setUploadStatus('❌ Error connecting to backend server.')
    } finally {
      setIsUploading(false)
    }
  }

  const handleSend = async (e) => {
    e.preventDefault()
    const query = input.trim()
    if (!query || isLoading) return

    const userMessage = { role: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(data.detail || `Server returned error (${response.status})`)
      }

      const botMessage = { 
        role: 'bot', 
        content: data.answer || 'No response generated.' 
      }
      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error("Backend Error:", error)
      setMessages(prev => [
        ...prev, 
        { 
          role: 'bot', 
          content: `⚠️ **Error:** ${error.message || 'Unable to connect to the backend server. Please verify the backend is running.'}` 
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div className="glass-panel">
        <header className="header">
          <h2>Smart Caching System</h2>
          
          <div className="upload-container">
            <input 
              id="pdf-upload"
              ref={fileInputRef}
              type="file" 
              accept=".pdf" 
              onChange={handleFileChange}
              disabled={isUploading}
            />
            <button 
              type="button"
              onClick={handleUpload} 
              disabled={!selectedFile || isUploading}
            >
              {isUploading ? 'Uploading...' : 'Upload Context (PDF)'}
            </button>
            {uploadStatus && (
              <div className="upload-status">
                {uploadStatus}
              </div>
            )}
          </div>
        </header>

        <div className="chat-box">
          {messages.length === 0 && (
            <div className="message-row bot">
              <div className="bubble bot">
                Hello! I am your self-refining AI assistant. Upload a PDF context document above for domain-specific knowledge, or simply ask me any question!
              </div>
            </div>
          )}
          
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-row ${msg.role}`}>
              <div className={`bubble ${msg.role}`}>
                {msg.role === 'bot' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message-row bot">
              <div className="bubble bot typing">Thinking...</div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSend} className="input-form">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your query..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  )
}

export default App