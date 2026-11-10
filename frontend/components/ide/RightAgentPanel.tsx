"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Bot,
  Play,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  XCircle,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Activity,
  Layers,
  Lock,
  FileCheck,
  Terminal,
  Send,
  Square,
  ChevronDown,
  ChevronRight,
  Eye,
  FileCode,
  X,
} from "lucide-react";
import { AgentTask, TaskStep, Message } from "@/types";

interface RightAgentPanelProps {
  tasks: AgentTask[];
  activeTask: AgentTask | null;
  onSelectTask: (task: AgentTask) => void;
  onCreateTask: (prompt: string) => void;
  onCancelTask: (taskId: string) => void;
  onApproveStep?: (taskId: string, stepId: number, approved: boolean) => void;
  isExecutingTask: boolean;
  messages: Message[];
  onSendMessage: (content: string, model: string) => void;
  isStreamingChat: boolean;
  onStopStreamingChat: () => void;
  selectedModel: string;
  onSelectModel: (m: string) => void;
  onClose: () => void;
}

export function RightAgentPanel({
  tasks,
  activeTask,
  onSelectTask,
  onCreateTask,
  onCancelTask,
  onApproveStep,
  isExecutingTask,
  messages,
  onSendMessage,
  isStreamingChat,
  onStopStreamingChat,
  selectedModel,
  onSelectModel,
  onClose,
}: RightAgentPanelProps) {
  const [mode, setMode] = useState<"developer" | "chat">("developer");
  const [prompt, setPrompt] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [showEventTimeline, setShowEventTimeline] = useState(false);

  const handleDevSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isExecutingTask) return;
    onCreateTask(prompt.trim());
    setPrompt("");
  };

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreamingChat) return;
    onSendMessage(chatInput.trim(), selectedModel);
    setChatInput("");
  };

  const plan = activeTask?.plan;
  const steps: TaskStep[] = plan?.steps || [];
  const completedCount = steps.filter((s) => s.status === "completed").length;
  const progressPct = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;
  const pendingApproval = activeTask?.pending_approval;

  return (
    <aside className="w-96 md:w-[420px] bg-slate-950 border-l border-slate-800 flex flex-col h-full select-none z-20 text-xs overflow-hidden">
      {/* Top Header: Mode Switcher + Close */}
      <div className="h-10 bg-slate-900 border-b border-slate-800 px-3 flex items-center justify-between">
        <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded border border-slate-800">
          <button
            onClick={() => setMode("developer")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition-colors text-[11px] ${
              mode === "developer"
                ? "bg-amber-500/20 text-amber-300 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Autonomous Dev</span>
          </button>
          <button
            onClick={() => setMode("chat")}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded transition-colors text-[11px] ${
              mode === "chat"
                ? "bg-indigo-600/30 text-indigo-300 font-semibold"
                : "text-slate-400 hover:text-white"
            }`}
          >
            <Bot className="w-3.5 h-3.5 text-indigo-400" />
            <span>AI Assistant</span>
          </button>
        </div>

        <button
          onClick={onClose}
          title="Close AI Agent panel (Ctrl+Shift+A)"
          className="p-1 text-slate-400 hover:text-white hover:bg-slate-800 rounded transition-colors"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Mode A: Autonomous Developer View */}
      {mode === "developer" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Active Task Summary / Lifecycle Header */}
          <div className="p-3 bg-slate-900/60 border-b border-slate-800/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-bold flex items-center gap-1">
                <Sparkles className="w-3 h-3" />
                <span>Antigravity Workflow Engine</span>
              </span>

              {activeTask && isExecutingTask && (
                <button
                  onClick={() => onCancelTask(activeTask.id)}
                  className="px-2 py-0.5 bg-rose-500/20 text-rose-300 border border-rose-500/30 rounded text-[10px] hover:bg-rose-500 hover:text-white transition-colors"
                >
                  Cancel Run
                </button>
              )}
            </div>

            {/* Workflow Pipeline Pills */}
            <div className="flex items-center justify-between text-[9px] font-mono text-slate-500 overflow-x-auto py-0.5">
              <span className={activeTask?.status === "planning" ? "text-amber-400 font-bold" : "text-slate-400"}>PLAN</span>
              <span>→</span>
              <span className={activeTask?.status === "awaiting_approval" ? "text-rose-400 font-bold animate-pulse" : "text-slate-400"}>APPROVE</span>
              <span>→</span>
              <span className={activeTask?.status === "executing" ? "text-indigo-400 font-bold animate-pulse" : "text-slate-400"}>EXECUTE</span>
              <span>→</span>
              <span className={activeTask?.status === "verified" ? "text-emerald-400 font-bold" : "text-slate-400"}>VERIFY</span>
              <span>→</span>
              <span className={activeTask?.status === "completed" ? "text-emerald-400 font-bold" : "text-slate-400"}>DELIVER</span>
            </div>

            {/* Progress Bar */}
            {steps.length > 0 && (
              <div className="space-y-1">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Progress ({completedCount}/{steps.length} steps)</span>
                  <span className="font-mono text-amber-400">{progressPct}%</span>
                </div>
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-emerald-500 rounded-full transition-all duration-300"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Body Content */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {/* Pending Approval Gatekeeper Card */}
            {pendingApproval && (
              <div className="p-3 bg-amber-500/10 border border-amber-500/40 rounded-lg space-y-2.5 animate-in fade-in">
                <div className="flex items-center gap-2 text-amber-400 font-bold text-xs">
                  <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
                  <span>Approval Required (Gatekeeper Security)</span>
                </div>
                <div className="text-[11px] text-slate-200 font-medium">
                  {pendingApproval.description}
                </div>
                <div className="flex items-center gap-2 text-[10px] font-mono text-slate-400">
                  <span className="px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">
                    Tool: {pendingApproval.tool_name}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase">
                    Risk: {pendingApproval.risk_level}
                  </span>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={() => onApproveStep?.(pendingApproval.task_id, pendingApproval.step_id, true)}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-1 px-3 rounded text-xs transition-colors shadow-sm flex items-center justify-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve & Continue</span>
                  </button>
                  <button
                    onClick={() => onApproveStep?.(pendingApproval.task_id, pendingApproval.step_id, false)}
                    className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </div>
            )}

            {/* Plan Display */}
            {plan ? (
              <div className="space-y-3">
                {/* Objective Card */}
                <div className="p-2.5 bg-slate-900 border border-slate-800 rounded space-y-1">
                  <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">
                    Plan Objective
                  </span>
                  <p className="text-white text-[12px] font-medium leading-relaxed">
                    {plan.objective}
                  </p>
                  {plan.tech_stack && plan.tech_stack.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {plan.tech_stack.map((t) => (
                        <span key={t} className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Steps List */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider px-1">
                    Execution Steps
                  </span>
                  <div className="space-y-1.5">
                    {steps.map((step) => {
                      const isStepDone = step.status === "completed";
                      const isStepRunning = step.status === "in_progress";
                      const isStepFailed = step.status === "failed";
                      const isStepWaiting = step.status === "awaiting_approval";

                      return (
                        <div
                          key={step.step_id}
                          className={`p-2.5 rounded border text-xs transition-all ${
                            isStepRunning
                              ? "bg-indigo-950/40 border-indigo-500/50"
                              : isStepWaiting
                              ? "bg-amber-950/30 border-amber-500/40"
                              : isStepDone
                              ? "bg-slate-900/60 border-slate-800/80 text-slate-300"
                              : isStepFailed
                              ? "bg-rose-950/30 border-rose-500/50"
                              : "bg-slate-950 border-slate-800/60 text-slate-400"
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-start gap-2">
                              <span className="font-mono text-[10px] text-slate-500 mt-0.5">
                                #{step.step_id}
                              </span>
                              <div>
                                <h4 className="font-medium text-white text-[11px] leading-snug">
                                  {step.title}
                                </h4>
                                <p className="text-slate-400 text-[10px] mt-0.5 leading-normal">
                                  {step.description}
                                </p>
                              </div>
                            </div>

                            {/* Status Icon */}
                            <div className="flex-shrink-0 mt-0.5">
                              {isStepRunning && <RefreshCw className="w-3.5 h-3.5 text-indigo-400 animate-spin" />}
                              {isStepDone && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                              {isStepWaiting && <Lock className="w-3.5 h-3.5 text-amber-400 animate-pulse" />}
                              {isStepFailed && <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                              {step.status === "pending" && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                            </div>
                          </div>

                          {/* Result Snippet */}
                          {step.result && (
                            <div className="mt-2 pt-1.5 border-t border-slate-800/60 text-[10px] font-mono text-emerald-300 bg-slate-950/60 p-1.5 rounded truncate">
                              ✓ {step.result}
                            </div>
                          )}

                          {step.error && (
                            <div className="mt-2 pt-1.5 border-t border-slate-800/60 text-[10px] font-mono text-rose-300 bg-rose-950/40 p-1.5 rounded">
                              ✗ {step.error}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Final Completion Report */}
                {activeTask?.result_summary && (
                  <div className="p-3 bg-emerald-950/20 border border-emerald-500/40 rounded-lg space-y-2">
                    <div className="flex items-center gap-1.5 text-emerald-400 font-bold text-xs">
                      <FileCheck className="w-4 h-4" />
                      <span>DODO Autonomous Completion Report</span>
                    </div>
                    <pre className="text-[10px] font-mono text-slate-200 whitespace-pre-wrap leading-relaxed bg-slate-950/80 p-2 rounded border border-emerald-500/20 max-h-48 overflow-y-auto">
                      {activeTask.result_summary}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-2">
                <Sparkles className="w-8 h-8 text-slate-600" />
                <p className="text-xs font-medium text-slate-400">No active autonomous task</p>
                <p className="text-[11px] text-slate-500 max-w-xs">
                  Describe what you want DODO to build below. DODO will inspect your project, formulate a plan, apply diffs, and test automatically.
                </p>
              </div>
            )}
          </div>

          {/* Dev Prompt Input Box */}
          <form onSubmit={handleDevSubmit} className="p-2.5 bg-slate-900 border-t border-slate-800 space-y-2">
            <div className="relative">
              <textarea
                rows={3}
                placeholder="Describe software task (e.g. 'Create task manager app with React and FastAPI', 'Fix bug in main.py')..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                  if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                    handleDevSubmit(e);
                  }
                }}
                disabled={isExecutingTask}
                className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/50 resize-none font-sans disabled:opacity-50"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-500 font-mono">
                Ctrl+Enter to send
              </span>
              <button
                type="submit"
                disabled={!prompt.trim() || isExecutingTask}
                className="bg-amber-500 hover:bg-amber-400 disabled:opacity-40 text-slate-950 font-bold px-3.5 py-1.5 rounded flex items-center gap-1.5 text-xs transition-colors shadow-sm"
              >
                {isExecutingTask ? (
                  <>
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    <span>Executing...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-current" />
                    <span>Start Run</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Mode B: Conversational AI Assistant View */}
      {mode === "chat" && (
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {messages.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 text-slate-500 space-y-2">
                <Bot className="w-8 h-8 text-slate-600" />
                <p className="text-xs font-medium text-slate-400">Ask DODO Anything</p>
                <p className="text-[11px] text-slate-500 max-w-xs">
                  Ask code explanation questions, request refactorings, or debug logic directly using local Qwen 2.5 Coder.
                </p>
              </div>
            ) : (
              messages.map((msg, idx) => {
                const isUser = msg.role === "user";
                return (
                  <div
                    key={idx}
                    className={`flex flex-col space-y-1 ${isUser ? "items-end" : "items-start"}`}
                  >
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-500 px-1">
                      <span>{isUser ? "You" : "DODO AI"}</span>
                      {msg.model_used && (
                        <span className="font-mono text-indigo-400">({msg.model_used})</span>
                      )}
                    </div>
                    <div
                      className={`p-2.5 rounded-lg max-w-[95%] text-xs leading-relaxed whitespace-pre-wrap break-words ${
                        isUser
                          ? "bg-amber-500/10 text-amber-200 border border-amber-500/30"
                          : "bg-slate-900 text-slate-200 border border-slate-800 font-mono"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Chat Input Box */}
          <form onSubmit={handleChatSubmit} className="p-2.5 bg-slate-900 border-t border-slate-800 flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask a technical question..."
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={isStreamingChat}
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
            />
            {isStreamingChat ? (
              <button
                type="button"
                onClick={onStopStreamingChat}
                className="p-1.5 bg-rose-600/30 text-rose-300 rounded border border-rose-500/40 hover:bg-rose-600 hover:text-white"
              >
                <Square className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!chatInput.trim()}
                className="p-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded transition-colors"
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            )}
          </form>
        </div>
      )}
    </aside>
  );
}
