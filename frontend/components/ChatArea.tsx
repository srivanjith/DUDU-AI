"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Square, Copy, Check, Sparkles, User, Bot, CornerDownLeft, RotateCcw, AlertCircle, Cpu, CheckCircle2 } from "lucide-react";
import { Message } from "@/types";

interface ChatAreaProps {
  messages: Message[];
  onSendMessage: (content: string, model: string) => void;
  isStreaming: boolean;
  onStopStreaming: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  availableModels: string[];
  ollamaStatus?: {
    status: string;
    version?: string;
    model_count: number;
    latency_ms?: number;
  };
}

export function ChatArea({
  messages,
  onSendMessage,
  isStreaming,
  onStopStreaming,
  selectedModel,
  onSelectModel,
  availableModels,
  ollamaStatus,
}: ChatAreaProps) {
  const [input, setInput] = useState("");
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<string | null>(null);
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

  const handleRetry = () => {
    // Find last user prompt
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        onSendMessage(messages[i].content, selectedModel);
        break;
      }
    }
  };

  const copyToClipboard = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const copyCode = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCodeIndex(id);
    setTimeout(() => setCopiedCodeIndex(null), 2000);
  };

  const isOnline = ollamaStatus?.status === "online";
  const modelCount = ollamaStatus?.model_count ?? availableModels.length;

  // Simple Markdown renderer for code blocks
  const renderMessageContent = (content: string, msgIdx: number) => {
    const parts = content.split(/(```[\s\S]*?```)/g);

    return parts.map((part, pIdx) => {
      if (part.startsWith("```") && part.endsWith("```")) {
        const lines = part.slice(3, -3).trim().split("\n");
        const lang = lines[0].trim();
        const code = lines.slice(1).join("\n");
        const codeId = `${msgIdx}-${pIdx}`;

        return (
          <div key={pIdx} className="my-2.5 rounded-xl border border-slate-800 bg-slate-950 overflow-hidden font-mono text-xs">
            <div className="flex items-center justify-between px-3.5 py-1.5 bg-slate-900 border-b border-slate-800 text-[11px] text-slate-400">
              <span className="font-semibold text-slate-300">{lang || "code"}</span>
              <button
                onClick={() => copyCode(code, codeId)}
                className="flex items-center gap-1 hover:text-white transition-colors"
                title="Copy code"
              >
                {copiedCodeIndex === codeId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedCodeIndex === codeId ? "Copied" : "Copy"}</span>
              </button>
            </div>
            <pre className="p-3.5 overflow-x-auto text-slate-200 leading-relaxed">
              <code>{code}</code>
            </pre>
          </div>
        );
      }

      return (
        <span key={pIdx} className="whitespace-pre-wrap leading-relaxed">
          {part}
        </span>
      );
    });
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100">
      {/* Top Header / Model Selector Bar */}
      <div className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Mode A — AI Assistant</span>
          <span className="text-slate-600">•</span>
          
          {/* Status Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-slate-800/80 border border-slate-700/60">
            <span className={`w-2 h-2 rounded-full ${isOnline ? (modelCount > 0 ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-amber-400") : "bg-rose-500"}`} />
            <span className="text-slate-300">
              {isOnline ? (modelCount > 0 ? `Ollama Online (${modelCount} models)` : "Ollama Online (0 models)") : "Ollama Offline"}
            </span>
          </div>
        </div>

        {/* Model Selector Dropdown */}
        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-400 font-medium flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            Model:
          </label>
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 font-medium cursor-pointer"
          >
            <option value="auto">Auto Router (Hardware Aware)</option>
            <optgroup label="Local Models (Ollama)">
              <option value="qwen2.5-coder:1.5b">Qwen2.5-Coder 1.5B (Local • Ollama)</option>
              {availableModels.filter(m => m !== "qwen2.5-coder:1.5b" && !m.includes("nemotron")).map((m) => (
                <option key={m} value={m}>
                  {m} (Installed)
                </option>
              ))}
            </optgroup>
            <optgroup label="Cloud Models (OpenRouter)">
              <option value="nvidia/nemotron-3-ultra-550b-a55b:free">
                NVIDIA Nemotron 3 Ultra (Cloud • OpenRouter)
              </option>
              <option value="nvidia/nemotron-super-vl">
                NVIDIA Nemotron Super VL (Vision • OpenRouter)
              </option>
            </optgroup>
          </select>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-16">
            <div className="w-14 h-14 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-3xl mb-4 shadow-lg shadow-indigo-600/10">
              🦅
            </div>
            <h2 className="text-xl font-bold text-white mb-2">Welcome to DODO AI Assistant</h2>
            <p className="text-xs text-slate-400 mb-6 leading-relaxed">
              Your independent, local-first conversational AI and engineering intelligence engine. Powered by local open-weight models on your machine with full privacy and zero cloud dependencies.
            </p>
            <div className="grid grid-cols-2 gap-2.5 w-full text-left">
              <button
                onClick={() => onSendMessage("Explain how DODO secures workspace files and isolates execution", selectedModel)}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 hover:border-indigo-500/50 hover:bg-slate-800/60 transition-all"
              >
                🔒 Workspace security & path jailing
              </button>
              <button
                onClick={() => onSendMessage("Explain how the DODO local model router optimizes inference for 4GB VRAM", selectedModel)}
                className="p-3 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 hover:border-indigo-500/50 hover:bg-slate-800/60 transition-all"
              >
                ⚡ Model routing for 4GB VRAM RTX 3050
              </button>
            </div>
          </div>
        ) : (
          messages.map((m, idx) => {
            const isUser = m.role === "user";
            const isError = m.content.startsWith("⚠️") || m.content.includes("Error:") || m.content.includes("error_code");

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
                      : isError
                      ? "bg-rose-950/40 border border-rose-800/60 text-rose-200 rounded-tl-none"
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

                  {/* Body Text / Markdown code formatting */}
                  <div className="font-sans text-[13px]">
                    {renderMessageContent(m.content, idx)}
                  </div>

                  {/* Action Buttons: Copy & Retry */}
                  {!isUser && (
                    <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {idx === messages.length - 1 && !isStreaming && (
                        <button
                          onClick={handleRetry}
                          className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors"
                          title="Retry response"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                      )}
                      <button
                        onClick={() => copyToClipboard(m.content, idx)}
                        className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white transition-colors"
                        title="Copy response"
                      >
                        {copiedIndex === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                    </div>
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
            placeholder="Ask a technical question, plan architecture, or inspect code..."
            disabled={isStreaming}
            className="flex-1 bg-slate-800/80 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all disabled:opacity-50"
          />

          {isStreaming ? (
            <button
              type="button"
              onClick={onStopStreaming}
              className="px-4 py-3 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-sm font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-rose-600/20 active:scale-95"
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
