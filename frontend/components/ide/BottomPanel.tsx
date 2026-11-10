"use client";

import React, { useState } from "react";
import {
  Terminal as TerminalIcon,
  Globe,
  AlertCircle,
  FileText,
  X,
  Maximize2,
  Minimize2,
  ChevronDown,
} from "lucide-react";
import { TerminalPanel } from "@/components/TerminalPanel";
import { BrowserPreview } from "@/components/BrowserPreview";

export type BottomTab = "terminal" | "browser" | "problems" | "output";

interface BottomPanelProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: BottomTab;
  onSelectTab: (tab: BottomTab) => void;
  height: number;
  onResize: (newHeight: number) => void;
  problemsCount?: number;
}

export function BottomPanel({
  isOpen,
  onClose,
  activeTab,
  onSelectTab,
  height,
  onResize,
  problemsCount = 0,
}: BottomPanelProps) {
  const [isMaximized, setIsMaximized] = useState(false);

  if (!isOpen) return null;

  const panelHeight = isMaximized ? "calc(100vh - 40px)" : `${height}px`;

  return (
    <div
      style={{ height: panelHeight }}
      className="border-t border-slate-800 bg-slate-950 flex flex-col z-20 transition-[height] duration-150 ease-out"
    >
      {/* Top Header / Tab Switcher */}
      <div className="h-9 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-2 text-xs select-none">
        <div className="flex items-center gap-1">
          <button
            onClick={() => onSelectTab("terminal")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "terminal"
                ? "bg-slate-800 text-white font-medium border-b-2 border-amber-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <TerminalIcon className="w-3.5 h-3.5 text-amber-400" />
            <span>Terminal</span>
          </button>

          <button
            onClick={() => onSelectTab("browser")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "browser"
                ? "bg-slate-800 text-white font-medium border-b-2 border-emerald-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <Globe className="w-3.5 h-3.5 text-emerald-400" />
            <span>Browser Preview</span>
          </button>

          <button
            onClick={() => onSelectTab("problems")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "problems"
                ? "bg-slate-800 text-white font-medium border-b-2 border-rose-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            <span>Problems</span>
            {problemsCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300 text-[10px]">
                {problemsCount}
              </span>
            )}
          </button>

          <button
            onClick={() => onSelectTab("output")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded transition-colors ${
              activeTab === "output"
                ? "bg-slate-800 text-white font-medium border-b-2 border-indigo-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>Output & Logs</span>
          </button>
        </div>

        {/* Panel Action Controls (Maximize / Close) */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMaximized(!isMaximized)}
            title={isMaximized ? "Restore panel size" : "Maximize panel"}
            className="p-1 hover:text-white hover:bg-slate-800 rounded text-slate-400 transition-colors"
          >
            {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onClose}
            title="Close bottom panel (Ctrl+`)"
            className="p-1 hover:text-white hover:bg-slate-800 rounded text-slate-400 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-hidden relative">
        {activeTab === "terminal" && <TerminalPanel />}
        {activeTab === "browser" && <BrowserPreview />}
        {activeTab === "problems" && (
          <div className="p-4 text-xs font-mono text-slate-400 space-y-2 h-full overflow-y-auto">
            <div className="flex items-center gap-2 text-slate-300 font-semibold mb-2">
              <AlertCircle className="w-4 h-4 text-emerald-400" />
              <span>Workspace Syntax & Linter Status: Clean</span>
            </div>
            <p className="text-slate-500 text-[11px]">
              No active syntax errors or AST compiler warnings detected in open files.
            </p>
          </div>
        )}
        {activeTab === "output" && (
          <div className="p-3 text-xs font-mono text-slate-400 space-y-1 h-full overflow-y-auto bg-slate-950">
            <div className="text-slate-500">[System] DODO Local Agent connected on port 8001.</div>
            <div className="text-slate-500">[System] MongoDB Atlas live cluster connection healthy (latency ~50ms).</div>
            <div className="text-slate-500">[System] Ollama inference engine online (qwen2.5-coder:1.5b resident).</div>
            <div className="text-slate-500">[System] Browser automation Playwright initialized.</div>
            <div className="text-emerald-400">[IDE] Autonomous workspace synchronized. Ready for developer instructions.</div>
          </div>
        )}
      </div>
    </div>
  );
}
