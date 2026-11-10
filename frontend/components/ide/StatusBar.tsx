"use client";

import React from "react";
import {
  GitBranch,
  Database,
  Cpu,
  Terminal,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Radio,
} from "lucide-react";
import { SystemHealth } from "@/types";

interface StatusBarProps {
  branchName: string;
  activeLanguage?: string;
  cursorPos?: { line: number; column: number };
  health: SystemHealth | null;
  onOpenTerminal: () => void;
  onOpenDiagnostics: () => void;
}

export function StatusBar({
  branchName,
  activeLanguage = "Plain Text",
  cursorPos = { line: 1, column: 1 },
  health,
  onOpenTerminal,
  onOpenDiagnostics,
}: StatusBarProps) {
  const dbStatus = health?.database?.status || "checking";
  const ollamaStatus = health?.inference_engine?.status || "offline";
  const localAgentStatus = health?.local_agent?.status || "offline";

  return (
    <footer className="h-6 bg-slate-950 border-t border-slate-800/80 px-2 flex items-center justify-between text-[11px] text-slate-400 select-none font-mono z-30">
      {/* Left items: Git Branch + Health indicator */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 hover:text-white cursor-pointer transition-colors">
          <GitBranch className="w-3 h-3 text-indigo-400" />
          <span>{branchName || "main"}</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* Database Status */}
        <div className="flex items-center gap-1" title={`MongoDB Atlas: ${dbStatus} (${health?.database?.database})`}>
          <Database className={`w-3 h-3 ${dbStatus === "connected" ? "text-emerald-400" : "text-amber-400"}`} />
          <span>{dbStatus === "connected" ? "Atlas Live" : "Local Mock"}</span>
          {health?.database?.latency_ms && (
            <span className="text-[10px] text-slate-500">({Math.round(health.database.latency_ms)}ms)</span>
          )}
        </div>

        <span className="text-slate-700">|</span>

        {/* Ollama Status */}
        <div className="flex items-center gap-1" title={`Local Ollama Engine: ${ollamaStatus}`}>
          <Cpu className={`w-3 h-3 ${ollamaStatus === "online" ? "text-emerald-400" : "text-rose-400"}`} />
          <span>{ollamaStatus === "online" ? "Ollama (qwen2.5 1.5b)" : "Ollama Offline"}</span>
        </div>

        <span className="text-slate-700">|</span>

        {/* Local Agent Port 8001 */}
        <div
          onClick={onOpenTerminal}
          className="flex items-center gap-1 hover:text-white cursor-pointer transition-colors"
          title="DODO Local Agent (Port 8001)"
        >
          <Terminal className={`w-3 h-3 ${localAgentStatus === "online" ? "text-emerald-400" : "text-slate-500"}`} />
          <span>Agent 8001</span>
        </div>
      </div>

      {/* Right items: Encoding, Language, Cursor Position, Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1">
          <span>Ln {cursorPos.line}, Col {cursorPos.column}</span>
        </div>

        <span className="text-slate-700">|</span>

        <span>UTF-8</span>

        <span className="text-slate-700">|</span>

        <span className="text-slate-300 font-semibold">{activeLanguage}</span>

        <span className="text-slate-700">|</span>

        {/* Diagnostics Trigger Pill */}
        <button
          onClick={onOpenDiagnostics}
          className="flex items-center gap-1 hover:text-white transition-colors"
          title="System Diagnostics"
        >
          <Activity className="w-3 h-3 text-emerald-400" />
          <span className="text-emerald-400 font-semibold">Ready</span>
        </button>
      </div>
    </footer>
  );
}

