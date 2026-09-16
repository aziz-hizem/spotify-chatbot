import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { SendHorizonal } from 'lucide-react';
import { FaSpotify } from "react-icons/fa";
import spotifyBg from './assets/backgrounds/spotify_bg.png';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'system', content: 'Hello! I can help you interact with your Spotify account. Try: "Add these songs to my chill playlist: Levitating, Blinding Lights"' }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const res = await axios.post(`${API_URL}/chat`, { message: input });
      const botMessage = { role: 'assistant', content: res.data.response };
      setMessages(prev => [...prev, botMessage]);
    } catch (err) {
      console.error('Chat request failed:', err);
      const errorMessage = { role: 'assistant', content: '⚠️ Failed to contact backend.' };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyPress = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (

    <div
      className="min-h-screen flex flex-col relative font-sans text-white"
      style={{
        backgroundImage: `url(${spotifyBg})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/80 pointer-events-none z-0" />

      <header className="flex items-center gap-3 px-6 py-4 border-b border-[#1DB954]/20 relative z-10">
        <FaSpotify className="text-[#1DB954]" size={28} />
        <h1 className="text-xl font-semibold">Spotify Chatbot</h1>
      </header>

      {/* Centered chat area */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10">
        <div className="flex-1 w-full max-w-xl flex flex-col mx-auto">
          <main className="flex-1 overflow-y-auto p-4 items-center space-y-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`w-full flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`px-4 py-3 rounded-2xl shadow-sm whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-[#1DB954]/80 text-black inline-block max-w-[80%]'
                      : 'bg-white/10 text-white max-w-xl'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </main>

          <form
            onSubmit={e => { e.preventDefault(); sendMessage(); }}
            className="px-0 py-4 border-t border-[#1DB954]/20" // removed bg-black/80
          >
            <div className="flex items-center gap-3">
              <textarea
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                rows={1}
                placeholder="Ask me to add songs, get info..."
                className="flex-1 resize-none rounded-xl bg-zinc-900 text-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[#1DB954] placeholder:text-zinc-400"
              />
              <button
                type="submit"
                className="p-2 rounded-full bg-[#1DB954] hover:bg-[#1ed760] transition-colors text-black"
              >
                <SendHorizonal size={20} />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
