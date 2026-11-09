"use client";

import React, { useState } from "react";
import {
  Sparkles,
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
} from "lucide-react";
import { AgentTask, TaskStep, ExecutionEvent } from "@/types";

interface AgentPanelProps {
  tasks: AgentTask[];
  activeTask: AgentTask | null;
  onSelectTask: (task: AgentTask) => void;
  onCreateTask: (prompt: string) => void;
  onCancelTask: (taskId: string) => void;
  onApproveStep?: (taskId: string, stepId: number, approved: boolean) => void;
  isExecuting: boolean;
}

export function AgentPanel({
  tasks,
  activeTask,
  onSelectTask,
  onCreateTask,
  onCancelTask,
  onApproveStep,
  isExecuting,
}: AgentPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [showEventLog, setShowEventLog] = useState(false);

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isExecuting) return;
    onCreateTask(prompt.trim());
    setPrompt("");
  };

  const plan = activeTask?.plan;
  const steps: TaskStep[] = plan?.steps || [];
  const completedCount = steps.filter((s) => s.status === "completed").length;
  const progressPct = steps.length > 0 ? Math.round((completedCount / steps.length) * 100) : 0;
  const pendingApproval = activeTask?.pending_approval;

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Top Header */}
      <div className="h-14 border-b border-slate-800/80 px-6 flex items-center justify-between bg-slate-900/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-violet-400 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Mode B — Autonomous Developer
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-xs text-slate-400 font-mono">
            PLAN → EXECUTE → OBSERVE → EVALUATE → FIX → VERIFY → DELIVER
          </span>
        </div>

        <div className="flex items-center gap-3">
          {activeTask && (
            <button
              onClick={() => setShowEventLog(!showEventLog)}
              className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded-lg border border-slate-800 hover:bg-slate-800/60 transition-colors flex items-center gap-1.5"
            >
              <Activity className="w-3.5 h-3.5" />
              <span>{showEventLog ? "Hide Event Timeline" : "Event Timeline"}</span>
            </button>
          )}

          {activeTask && isExecuting && (
            <button
              onClick={() => onCancelTask(activeTask.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-medium hover:bg-rose-600 hover:text-white transition-colors"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Cancel Run</span>
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sub-sidebar: Task History */}
        <div className="w-72 border-r border-slate-800/80 bg-slate-900/30 flex flex-col">
          <div className="p-3 border-b border-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
            <span>Autonomous Runs</span>
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{tasks.length}</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
            {tasks.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">No autonomous runs yet.</div>
            ) : (
              tasks.map((t) => (
                <div
                  key={t.id}
                  onClick={() => onSelectTask(t)}
                  className={`p-2.5 rounded-xl cursor-pointer text-xs transition-all border ${
                    activeTask?.id === t.id
                      ? "bg-slate-800 border-violet-500/40 text-white shadow-sm"
                      : "border-transparent text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                  }`}
                >
                  <div className="font-medium truncate mb-1">{t.prompt}</div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span
                      className={`px-1.5 py-0.5 rounded capitalize ${
                        t.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : t.status === "awaiting_approval"
                          ? "bg-amber-500/15 text-amber-300 border border-amber-500/30 animate-pulse font-semibold"
                          : t.status === "executing"
                          ? "bg-violet-500/10 text-violet-400 animate-pulse"
                          : t.status === "cancelled"
                          ? "bg-slate-800 text-slate-400"
                          : "bg-amber-500/10 text-amber-400"
                      }`}
                    >
                      {t.status.replace("_", " ")}
                    </span>
                    {t.verified && (
                      <span className="text-emerald-400 flex items-center gap-0.5 text-[10px]">
                        <ShieldCheck className="w-3 h-3" />
                        Verified
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Main Detail Area */}
        <div className="flex-1 flex flex-col overflow-y-auto p-6 space-y-6">
          {/* Create Task Form */}
          <div className="bg-slate-900 border border-slate-800/80 rounded-2xl p-4 shadow-lg shadow-black/20">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2 flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-violet-400" />
              <span>Launch Autonomous Objective</span>
            </h3>
            <form onSubmit={handleStart} className="flex gap-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. Plan a task management application using React, FastAPI and MongoDB"
                disabled={isExecuting}
                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-violet-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!prompt.trim() || isExecuting}
                className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:bg-slate-800 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95 shadow-md shadow-violet-600/20"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Execute Objective</span>
              </button>
            </form>
          </div>

          {/* Interactive Approval Banner */}
          {pendingApproval && (
            <div className="bg-amber-950/40 border border-amber-500/50 rounded-2xl p-4 shadow-lg shadow-amber-500/5 animate-pulse">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <ShieldAlert className="w-4 h-4 text-amber-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-amber-300 uppercase tracking-wide">
                        Security Approval Required
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono uppercase font-bold border border-amber-500/30">
                        {pendingApproval.permission_level} Permission
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                        Risk: {pendingApproval.risk_level.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-slate-200">{pendingApproval.description}</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Target File: <span className="font-mono text-amber-200">{pendingApproval.parameters?.path || pendingApproval.tool_name}</span> (Phase 4 Controlled Filesystem Operation with automated checkpoint snapshot)
                    </p>
                    {pendingApproval.parameters?.content && (
                      <div className="mt-2 p-2 bg-slate-950 rounded-lg border border-amber-500/20 max-h-36 overflow-y-auto text-[11px] font-mono text-slate-300">
                        <div className="text-[10px] text-amber-400 font-bold uppercase mb-1">Proposed File Content Preview:</div>
                        <pre className="whitespace-pre-wrap">{pendingApproval.parameters.content.slice(0, 500)}...</pre>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    onClick={() => onApproveStep && onApproveStep(pendingApproval.task_id, pendingApproval.step_id, false)}
                    className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
                  >
                    Reject
                  </button>
                  <button
                    onClick={() => onApproveStep && onApproveStep(pendingApproval.task_id, pendingApproval.step_id, true)}
                    className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-md shadow-amber-600/30 transition-all flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Approve Step</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Active Task Execution Monitor */}
          {activeTask ? (
            <div className="space-y-6">
              {/* Task Header & Plan Overview */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-bold text-white">{activeTask.prompt}</h2>
                    <div className="text-[11px] font-mono text-slate-400 mt-0.5">
                      Target Workspace: <span className="text-emerald-400">{activeTask.workspace_path}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2.5 py-1 text-xs font-semibold rounded-full border capitalize ${
                        activeTask.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : activeTask.status === "awaiting_approval"
                          ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                          : "bg-violet-500/10 text-violet-400 border-violet-500/20"
                      }`}
                    >
                      Status: {activeTask.status.replace("_", " ")}
                    </span>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] text-slate-400">
                    <span>Progress: {completedCount} of {steps.length} steps completed</span>
                    <span className="font-mono font-semibold text-violet-400">{progressPct}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-violet-500 h-full rounded-full transition-all duration-300 ease-out"
                      style={{ width: `${progressPct}%` }}
                    />
                  </div>
                </div>

                {/* Architecture & Tech Stack Plan Badges */}
                {plan && (
                  <div className="space-y-2 pt-2 border-t border-slate-800/80">
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      {plan.tech_stack && plan.tech_stack.length > 0 && (
                        <div className="flex items-center gap-1">
                          <span className="text-slate-400 text-[11px]">Stack:</span>
                          {plan.tech_stack.map((t) => (
                            <span key={t} className="px-2 py-0.5 rounded bg-slate-800 text-indigo-300 font-mono text-[10px] border border-slate-700">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}

                      {plan.risk_level && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 uppercase font-mono">
                          Risk: {plan.risk_level}
                        </span>
                      )}

                      {plan.complexity_score && (
                        <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                          Complexity: {plan.complexity_score}/5
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
                      <span className="font-semibold text-violet-300">Strategy:</span> {plan.analysis}
                    </p>
                  </div>
                )}
              </div>

              {/* Event Timeline (Collapsible) */}
              {showEventLog && activeTask.events && activeTask.events.length > 0 && (
                <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-4 space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-violet-400" />
                    <span>Real-time Execution Telemetry ({activeTask.events.length} events)</span>
                  </h4>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto font-mono text-[11px] p-2 bg-slate-950 rounded-xl border border-slate-800/60">
                    {activeTask.events.map((evt, idx) => (
                      <div key={evt.event_id || idx} className="flex items-start gap-2 text-slate-300">
                        <span className="text-slate-500 flex-shrink-0">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </span>
                        <span className="text-violet-400 font-semibold uppercase text-[10px] px-1 bg-violet-950/50 rounded flex-shrink-0">
                          {evt.phase}
                        </span>
                        <span className="truncate">{evt.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Execution Steps List */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center justify-between">
                  <span>Structured Plan Steps ({steps.length})</span>
                  <span className="text-[10px] text-slate-500 font-normal">Controlled Phase 3 Planning Lifecycle</span>
                </h3>

                {steps.map((s) => {
                  const isDone = s.status === "completed";
                  const isRunning = s.status === "in_progress";
                  const isAwaiting = s.status === "awaiting_approval";
                  const isFailed = s.status === "failed";

                  return (
                    <div
                      key={s.step_id}
                      className={`border rounded-xl p-4 transition-all ${
                        isAwaiting
                          ? "bg-amber-950/20 border-amber-500/50 shadow-md shadow-amber-500/10"
                          : isRunning
                          ? "bg-violet-950/20 border-violet-500/50 shadow-md shadow-violet-500/10"
                          : isDone
                          ? "bg-slate-900/80 border-slate-800"
                          : isFailed
                          ? "bg-rose-950/20 border-rose-500/30"
                          : "bg-slate-900/30 border-slate-800/50 opacity-60"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2.5">
                          {isDone ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : isRunning ? (
                            <RefreshCw className="w-4 h-4 text-violet-400 animate-spin" />
                          ) : isAwaiting ? (
                            <ShieldAlert className="w-4 h-4 text-amber-400 animate-bounce" />
                          ) : isFailed ? (
                            <AlertTriangle className="w-4 h-4 text-rose-400" />
                          ) : (
                            <Clock className="w-4 h-4 text-slate-500" />
                          )}
                          <span className="text-xs font-bold text-white">
                            Step {s.step_id}: {s.title}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5">
                          {s.permission_level && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                              {s.permission_level}
                            </span>
                          )}

                          {s.approval_required && (
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-0.5">
                              <Lock className="w-2.5 h-2.5" />
                              Approval Gate
                            </span>
                          )}

                          {s.tool && (
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-400 border border-slate-700">
                              {s.tool}
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="text-xs text-slate-400 ml-6.5 leading-relaxed">{s.description}</p>

                      {/* Dependencies and Expected Outcomes */}
                      {s.expected_outcomes && s.expected_outcomes.length > 0 && (
                        <div className="mt-2 ml-6.5 text-[11px] text-slate-400 space-y-0.5">
                          {s.expected_outcomes.map((out, idx) => (
                            <div key={idx} className="flex items-center gap-1.5">
                              <ArrowRight className="w-3 h-3 text-slate-500 flex-shrink-0" />
                              <span>{out}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Actual Result Observation */}
                      {s.result && (
                        <div className="mt-2.5 ml-6.5 bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-[11px] font-mono text-slate-300 whitespace-pre-wrap max-h-36 overflow-y-auto">
                          {s.result}
                        </div>
                      )}

                      {/* Error block if any */}
                      {s.error && (
                        <div className="mt-2.5 ml-6.5 bg-rose-950/40 border border-rose-800/60 rounded-lg p-2.5 text-[11px] font-mono text-rose-300">
                          {s.error}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Completion Report */}
              {activeTask.result_summary && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                    <ShieldCheck className="w-5 h-5" />
                    <span>Completion & Verification Report</span>
                  </div>
                  <div className="whitespace-pre-wrap text-xs text-slate-300 leading-relaxed font-sans bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                    {activeTask.result_summary}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-20 text-slate-500 text-xs">
              Select or launch an autonomous objective to view the real-time execution lifecycle.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
