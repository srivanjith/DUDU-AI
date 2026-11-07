"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Square, Copy, Check, Sparkles, User, Bot, CornerDownLeft } from "lucide-react";
import { Message } from "@/types";

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (content: string, model: string) => void;
  isStreaming: boolean;
  onStopStreaming: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  availableModels: string[];
}

export function ChatArea({
  messages,
  onSendMessage,
  isStreaming,
  onStopStreaming,
  selectedModel,
  onSelectModel,
  availableModels,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    onSendMessage(input.trim(), selectedModel);
    setInput("");
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100">
      {/* Top Bar / Model Selector */}
      <div className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Mode A — AI Assistant</span>
          <span className="text-slate-600">•</span>
          <span className="text-xs text-indigo-400 font-medium">Conversational & Code Planning</span>
        </div>

        {/* Model Selector Dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium">Model:</label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-medium cursor-pointer"
          >
            <option value="auto">Auto Router (Hardware Aware)</option>
            <option value="qwen2.5-coder:7b">Qwen 2.5 Coder 7B</option>
            <option value="qwen2.5:7b">Qwen 2.5 7B</option>
            <option value="deepseek-r1:8b">DeepSeek R1 8B</option>
            <option value="llama3.2:1b">Llama 3.2 1B (Fast)</option>
            {availableModels.map((m) => (
              <option key={m} value={m}>
                {m} (Installed)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-16">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-3xl mb-4">
              🦅
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Welcome to DODO</h2>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Your independent, local-first autonomous development assistant. Ask questions, plan software architectures, or explore code completely on your machine.
            </p>
            <div className="grid grid-cols-2 gap-2 w-full text-left">
              <button
                onClick={() => onSendMessage("Explain how the DODO local model router optimizes inference for 4GB VRAM", selectedModel)}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 hover:border-indigo-500/50 hover:bg-slate-800/60 transition-all"
              >
                💡 Explain model router with 4GB VRAM
              </button>
              <button
                onClick={() => onSendMessage("Create an architecture blueprint for a real-time collaborative code editor", selectedModel)}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 hover:border-indigo-500/50 hover:bg-slate-800/60 transition-all"
              >
                🛠️ Architecture blueprint for collaborative editor
              </button>
            </div>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isUser = m.role === "user";
            return (
              <div
                key={idx}
                className={`flex gap-3.5 max-w-4xl mx-auto ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-sm flex-shrink-0">
                    🦅
                  </div>
                )}

                <div
                  className={`group relative rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[85%] ${
                    isUser
                      ? "bg-indigo-600 text-white rounded-tr-none shadow-md shadow-indigo-600/10"
                      : "bg-slate-900 border border-slate-800/80 text-slate-200 rounded-tl-none"
                  }`}
                >
                  {/* Model tag if assistant */}
                  {!isUser && m.model_used && (
                    <div className="text-[10px] text-indigo-400 font-medium mb-1.5 flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      <span>{m.model_used}</span>
                    </div>
                  )}

                  {/* Body Text / Code formatting */}
                  <div className="whitespace-pre-wrap font-sans text-[13px]">{m.content}</div>

                  {/* Copy Button */}
                  {!isUser && (
                    <button
                      onClick={() => copyToClipboard(m.content, idx)}
                      className="absolute top-2 right-2 p-1 rounded bg-slate-800 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Copy response"
                    >
                      {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 text-xs flex-shrink-0">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Composer Bottom Form */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 backdrop-blur-md">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your question, code request, or development plan..."
            disabled={isStreaming}
            className="flex-1 bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all disabled:opacity-50"
          />

          {isStreaming ? (
            <button
              type="button"
              onClick={onStopStreaming}
              className="px-4 py-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-sm font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-rose-600/20"
            >
              <Square className="w-4 h-4 fill-white" />
              <span>Stop</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!input.trim()}
              className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-xl text-sm font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-indigo-600/20 active:scale-95"
            >
              <span>Send</span>
              <CornerDownLeft className="w-4 h-4" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

