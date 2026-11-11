"use client";

import React from "react";
import {
  Layers,
  FolderGit2,
  FolderOpen,
  FolderPlus,
  Save,
  Check,
  Bot,
  Sparkles,
  Settings,
  PanelLeft,
  PanelBottom,
  PanelRight,
  Search,
  Cpu,
  ShieldCheck,
  ChevronDown,
} from "lucide-react";

interface TopNavBarProps {
  projectName: string;
  workspacePath: string;
  isDirty: boolean;
  onSaveActiveFile: () => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  availableModels: string[];
  agentStatus: "idle" | "planning" | "executing" | "awaiting_approval" | "completed" | "error";
  showLeftSidebar: boolean;
  onToggleLeftSidebar: () => void;
  showBottomPanel: boolean;
  onToggleBottomPanel: () => void;
  showRightAgent: boolean;
  onToggleRightAgent: () => void;
  onOpenCommandPalette: () => void;
  onOpenQuickOpen: () => void;
  onOpenSettings: () => void;
  onOpenProjectModal: () => void;
  onNewProjectModal: () => void;
  ollamaStatus?: "online" | "offline";
  openRouterConfigured?: boolean;
}

export function TopNavBar({
  projectName,
  workspacePath,
  isDirty,
  onSaveActiveFile,
  selectedModel,
  onSelectModel,
  availableModels,
  agentStatus,
  showLeftSidebar,
  onToggleLeftSidebar,
  showBottomPanel,
  onToggleBottomPanel,
  showRightAgent,
  onToggleRightAgent,
  onOpenCommandPalette,
  onOpenQuickOpen,
  onOpenSettings,
  onOpenProjectModal,
  onNewProjectModal,
  ollamaStatus = "online",
  openRouterConfigured = true,
}: TopNavBarProps) {
  const getAgentStatusBadge = () => {
    switch (agentStatus) {
      case "planning":
        return {
          label: "Agent Planning...",
          color: "bg-indigo-500/20 text-indigo-400 border-indigo-500/30",
          dot: "bg-indigo-400 animate-pulse",
        };
      case "executing":
        return {
          label: "Agent Executing",
          color: "bg-amber-500/20 text-amber-400 border-amber-500/30",
          dot: "bg-amber-400 animate-ping",
        };
      case "awaiting_approval":
        return {
          label: "Approval Required",
          color: "bg-rose-500/20 text-rose-400 border-rose-500/40",
          dot: "bg-rose-400 animate-pulse",
        };
      case "completed":
        return {
          label: "Agent Completed",
          color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
          dot: "bg-emerald-400",
        };
      case "error":
        return {
          label: "Agent Error",
          color: "bg-red-500/20 text-red-400 border-red-500/30",
          dot: "bg-red-400",
        };
      default:
        return {
          label: "Agent Ready",
          color: "bg-slate-800 text-slate-400 border-slate-700",
          dot: "bg-emerald-500",
        };
    }
  };

  const badge = getAgentStatusBadge();

  return (
    <header className="h-10 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-3 text-xs select-none z-30">
      {/* Left: Brand + Project Info */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 font-bold tracking-tight text-white cursor-pointer hover:opacity-90 transition-opacity">
          <div className="w-5 h-5 rounded bg-gradient-to-tr from-amber-500 to-amber-400 flex items-center justify-center shadow-sm">
            <span className="text-[10px] text-slate-950 font-black">🦅</span>
          </div>
          <span className="text-[13px] tracking-wider font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 via-amber-200 to-white">
            DODO
          </span>
          <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-400 font-mono border border-amber-500/30 font-semibold">
            IDE
          </span>
        </div>

        <div className="h-4 w-[1px] bg-slate-800" />

        {/* Project Path Indicator */}
        <div
          onClick={onOpenProjectModal}
          title="Click to switch or open another project"
          className="flex items-center gap-1.5 text-slate-300 font-medium hover:text-white cursor-pointer px-1.5 py-0.5 rounded hover:bg-slate-800/60 transition-colors"
        >
          <FolderGit2 className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-white font-semibold truncate max-w-[130px]">{projectName || "workspace"}</span>
          <span className="text-slate-500 font-mono text-[11px] hidden lg:inline truncate max-w-[180px]" title={workspacePath}>
            [{workspacePath}]
          </span>
          <ChevronDown className="w-3 h-3 text-slate-500" />
        </div>

        {/* Action Buttons: Open Project & New Project */}
        <div className="flex items-center gap-1">
          <button
            onClick={onOpenProjectModal}
            title="Open existing project folder (Ctrl+O)"
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-slate-800 hover:bg-slate-700 hover:text-white text-slate-300 border border-slate-700 transition-colors"
          >
            <FolderOpen className="w-3 h-3 text-amber-400" />
            <span className="hidden sm:inline">Open</span>
          </button>
          <button
            onClick={onNewProjectModal}
            title="Create a new starter project"
            className="flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-emerald-950/70 hover:bg-emerald-900/90 hover:text-white text-emerald-300 border border-emerald-800/60 transition-colors"
          >
            <FolderPlus className="w-3 h-3 text-emerald-400" />
            <span className="hidden sm:inline">New</span>
          </button>
        </div>
      </div>

      {/* Center: Command Palette / Search Trigger */}
      <div className="flex-1 max-w-md mx-4 hidden sm:flex items-center">
        <button
          onClick={onOpenCommandPalette}
          className="w-full h-7 bg-slate-950/80 hover:bg-slate-950 border border-slate-800 hover:border-slate-700 rounded-md px-2.5 flex items-center justify-between text-slate-400 hover:text-slate-200 transition-colors shadow-inner"
        >
          <div className="flex items-center gap-2">
            <Search className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px]">DODO Command Palette & Files...</span>
          </div>
          <kbd className="text-[9px] font-mono px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-slate-400">
            Ctrl+Shift+P
          </kbd>
        </button>
      </div>

      {/* Right: Model Selector + Agent Status + Layout Controls */}
      <div className="flex items-center gap-2.5">
        {/* Save Status Button */}
        <button
          onClick={onSaveActiveFile}
          disabled={!isDirty}
          title={isDirty ? "Save file (Ctrl+S)" : "All files saved"}
          className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] font-medium border transition-colors ${
            isDirty
              ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30 animate-pulse"
              : "bg-slate-800/40 text-slate-400 border-slate-800 cursor-default"
          }`}
        >
          {isDirty ? (
            <>
              <Save className="w-3 h-3 text-amber-400" />
              <span>Save (Ctrl+S)</span>
            </>
          ) : (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span>Saved</span>
            </>
          )}
        </button>

        {/* Model Selector Dropdown & Connection Status */}
        <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 rounded px-2 py-0.5 text-[11px]">
          <Cpu className="w-3 h-3 text-indigo-400" />
          <select
            value={selectedModel}
            onChange={(e) => onSelectModel(e.target.value)}
            className="bg-transparent text-slate-200 focus:outline-none cursor-pointer pr-1 text-[11px]"
          >
            <option value="auto" className="bg-slate-900 text-white">Auto Router (Hardware Aware)</option>
            <optgroup label="Local Models (Ollama)" className="bg-slate-900 text-slate-400 font-semibold">
              <option value="qwen2.5-coder:1.5b" className="bg-slate-900 text-white">
                Qwen2.5-Coder 1.5B (Local • Ollama)
              </option>
              {(availableModels || []).filter(m => m !== "qwen2.5-coder:1.5b" && !m.includes("nemotron")).map((m) => (
                <option key={m} value={m} className="bg-slate-900 text-white">
                  {m} (Local Ollama)
                </option>
              ))}
            </optgroup>
            <optgroup label="Cloud Models (OpenRouter)" className="bg-slate-900 text-slate-400 font-semibold">
              <option value="nvidia/nemotron-3-ultra-550b-a55b:free" className="bg-slate-900 text-emerald-400">
                NVIDIA Nemotron 3 Ultra (Cloud • OpenRouter)
              </option>
              <option value="nvidia/nemotron-super-vl" className="bg-slate-900 text-purple-400">
                NVIDIA Nemotron Super VL (Vision • OpenRouter)
              </option>
            </optgroup>
          </select>

          {/* Model Provider Live Status Indicator */}
          {selectedModel.includes("nemotron") ? (
            <span
              className={`w-2 h-2 rounded-full ${
                openRouterConfigured ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-amber-400"
              }`}
              title={openRouterConfigured ? "OpenRouter Cloud API Connected" : "OpenRouter API Key Missing"}
            />
          ) : (
            <span
              className={`w-2 h-2 rounded-full ${
                ollamaStatus === "online"
                  ? "bg-emerald-400 shadow-sm shadow-emerald-400/50"
                  : "bg-rose-500 animate-pulse"
              }`}
              title={ollamaStatus === "online" ? "Local Ollama Daemon Online" : "Local Ollama Daemon Offline"}
            />
          )}
        </div>

        {/* Agent Status Pill */}
        <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-medium ${badge.color}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
          <span>{badge.label}</span>
        </div>

        <div className="h-4 w-[1px] bg-slate-800" />

        {/* Layout Toggle Buttons */}
        <div className="flex items-center gap-0.5 bg-slate-950 border border-slate-800 rounded p-0.5">
          <button
            onClick={onToggleLeftSidebar}
            title="Toggle Primary Sidebar (Ctrl+B)"
            className={`p-1 rounded hover:text-white transition-colors ${
              showLeftSidebar ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-900"
            }`}
          >
            <PanelLeft className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onToggleBottomPanel}
            title="Toggle Bottom Terminal/Preview Panel (Ctrl+`)"
            className={`p-1 rounded hover:text-white transition-colors ${
              showBottomPanel ? "bg-slate-800 text-white" : "text-slate-500 hover:bg-slate-900"
            }`}
          >
            <PanelBottom className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onToggleRightAgent}
            title="Toggle AI Agent Panel (Ctrl+Shift+A)"
            className={`p-1 rounded hover:text-white transition-colors ${
              showRightAgent ? "bg-slate-800 text-amber-400" : "text-slate-500 hover:bg-slate-900"
            }`}
          >
            <PanelRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Settings button */}
        <button
          onClick={onOpenSettings}
          title="IDE & Model Settings"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
        >
          <Settings className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
}

