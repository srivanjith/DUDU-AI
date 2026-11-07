"use client";

import React from "react";
import { MessageSquare, Plus, Terminal, Code2, Cpu, Settings, Trash2, Globe, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { Conversation, SystemHealth } from "@/types";

interface SidebarProps {
  conversations: Conversation[];
  activeConvId: string | null;
  onSelectConv: (id: string) => void;
  onNewChat: () => void;
  onDeleteConv: (id: string, e: React.MouseEvent) => void;
  activeTab: "chat" | "developer" | "editor" | "terminal" | "browser" | "models" | "settings";
  onSelectTab: (tab: any) => void;
  health: SystemHealth | null;
}

export function Sidebar({
  conversations,
  activeConvId,
  onSelectConv,
  onNewChat,
  onDeleteConv,
  activeTab,
  onSelectTab,
  health,
}: SidebarProps) {
  const isDbHealthy = health?.database?.status === "connected" || health?.database?.status === "healthy_fallback";
  const isAiOnline = health?.inference_engine?.status === "online";

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center font-black text-xl text-white shadow-lg shadow-indigo-500/20">
            🦅
          </div>
          <div>
            <h1 className="font-extrabold text-base tracking-wider text-white">DODO</h1>
            <p className="text-[10px] text-slate-400 font-medium">Your AI. Your Machine. Your Rules.</p>
          </div>
        </div>
      </div>

      {/* Navigation Modes */}
      <div className="px-3 py-3 border-b border-slate-800 space-y-1">
        <button
          onClick={() => onSelectTab("chat")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === "chat"
              ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <MessageSquare className="w-4 h-4 text-indigo-400" />
          <span>Mode A: AI Assistant</span>
        </button>

        <button
          onClick={() => onSelectTab("developer")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === "developer"
              ? "bg-violet-600/20 text-violet-400 border border-violet-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Sparkles className="w-4 h-4 text-violet-400" />
          <span>Mode B: Autonomous Dev</span>
        </button>

        <button
          onClick={() => onSelectTab("editor")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === "editor"
              ? "bg-emerald-600/20 text-emerald-400 border border-emerald-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Code2 className="w-4 h-4 text-emerald-400" />
          <span>Workspace Editor</span>
        </button>

        <button
          onClick={() => onSelectTab("terminal")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === "terminal"
              ? "bg-amber-600/20 text-amber-400 border border-amber-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Terminal className="w-4 h-4 text-amber-400" />
          <span>Mode C: Terminal & Processes</span>
        </button>

        <button
          onClick={() => onSelectTab("browser")}
          className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            activeTab === "browser"
              ? "bg-sky-600/20 text-sky-400 border border-sky-500/30 font-semibold"
              : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
          }`}
        >
          <Globe className="w-4 h-4 text-sky-400" />
          <span>Browser Verification</span>
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all active:scale-[0.98]"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* Conversations List */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-1">
        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-2 py-1">
          Recent Conversations
        </div>
        {conversations.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-500 italic">No conversations yet</div>
        ) : (
          conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => {
                onSelectConv(c.id);
                onSelectTab("chat");
              }}
              className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                activeConvId === c.id
                  ? "bg-slate-800 text-white font-medium border border-slate-700/60"
                  : "text-slate-400 hover:bg-slate-800/40 hover:text-slate-200"
              }`}
            >
              <div className="flex items-center gap-2 truncate">
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 opacity-70" />
                <span className="truncate">{c.title}</span>
              </div>
              <button
                onClick={(e) => onDeleteConv(c.id, e)}
                className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 transition-opacity"
                title="Delete Conversation"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))
        )}
      </div>

      {/* System Status Indicators */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40 space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isDbHealthy ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-rose-500"}`} />
            MongoDB
          </span>
          <span className="text-slate-500 text-[10px]">{health?.database?.status || "connecting"}</span>
        </div>

        <div className="flex items-center justify-between text-[11px]">
          <span className="text-slate-400 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isAiOnline ? "bg-emerald-400" : "bg-amber-400"}`} />
            Inference
          </span>
          <span className="text-slate-500 text-[10px]">{isAiOnline ? "Ollama Active" : "Local Engine"}</span>
        </div>

        {/* Footer controls */}
        <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-slate-400">
          <button
            onClick={() => onSelectTab("models")}
            className="flex items-center gap-1.5 text-xs hover:text-white transition-colors"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Models</span>
          </button>

          <button
            onClick={() => onSelectTab("settings")}
            className="flex items-center gap-1.5 text-xs hover:text-white transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </aside>
  );
}

