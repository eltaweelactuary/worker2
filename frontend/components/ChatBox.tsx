"use client"
import { useState } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'

export default function ChatBox() {
    const [messages, setMessages] = useState<{ role: 'ai' | 'user', text: string }[]>([
        { role: 'ai', text: 'Welcome, Executive. I am your Gemini Actuary. How can I assist with Law 2/2018 solvency analysis today?' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)

    const askAI = async () => {
        if (!input.trim()) return
        const userMsg = input
        setInput('')
        setMessages(prev => [...prev, { role: 'user', text: userMsg }])
        setLoading(true)

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'
            const res = await fetch(`${apiUrl}/ask-ai`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userMsg,
                    data_summary: "Live Actuarial Context: V4.0 Enterprise API",
                    persona: "Senior Actuary"
                })
            })
            const data = await res.json()
            setMessages(prev => [...prev, { role: 'ai', text: data.response }])
        } catch (err) {
            setMessages(prev => [...prev, { role: 'ai', text: 'Error connecting to the intelligence layer.' }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="glass-card flex flex-col h-[500px] overflow-hidden">
            <div className="p-4 border-b border-white/10 bg-white/5 flex items-center gap-2">
                <Bot className="text-actuary-primary" size={20} />
                <span className="font-semibold text-sm">Strategic Intelligence Agent</span>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((m, i) => (
                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-2xl text-sm ${m.role === 'user' ? 'bg-actuary-secondary text-white' : 'bg-white/5 text-slate-300'}`}>
                            {m.text}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-white/5 p-3 rounded-2xl text-slate-300">
                            <Loader2 className="animate-spin" size={16} />
                        </div>
                    </div>
                )}
            </div>

            <div className="p-4 bg-white/5 border-t border-white/10 flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && askAI()}
                    placeholder="Ask about Law 2/2018 compliance..."
                    className="flex-1 bg-black/20 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-actuary-primary"
                />
                <button onClick={askAI} className="p-2 bg-actuary-primary rounded-lg hover:opacity-80 transition-opacity">
                    <Send size={18} />
                </button>
            </div>
        </div>
    )
}
