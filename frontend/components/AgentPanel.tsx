"use client";

import React, { useState } from "react";
import { Sparkles, Play, CheckCircle2, AlertTriangle, Clock, RefreshCw, XCircle, ShieldCheck, Terminal, FileCode2 } from "lucide-react";
import { AgentTask, TaskStep } from "@/types";

interface AgentPanelProps {
  tasks: AgentTask[];
  activeTask: AgentTask | null;
  onSelectTask: (task: AgentTask) => void;
  onCreateTask: (prompt: string) => void;
  onCancelTask: (taskId: string) => void;
  isExecuting: boolean;
}

export function AgentPanel({
  tasks,
  activeTask,
  onSelectTask,
  onCreateTask,
  onCancelTask,
  isExecuting,
}: AgentPanelProps) {
  const [prompt, setPrompt] = useState("");

  const handleStart = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isExecuting) return;
    onCreateTask(prompt.trim());
    setPrompt("");
  };

  const plan = activeTask?.plan;
  const steps = plan?.steps || [];

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
          <span className="text-xs text-slate-400">PLAN → EXECUTE → OBSERVE → EVALUATE → FIX → VERIFY → DELIVER</span>
        </div>

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

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sub-sidebar: Task History */}
        <div className="w-72 border-r border-slate-800/80 bg-slate-900/30 flex flex-col">
          <div className="p-3 border-b border-slate-800/80 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Autonomous Runs
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
                      className={`px-1.5 py-0.5 rounded ${
                        t.status === "completed"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : t.status === "executing"
                          ? "bg-violet-500/10 text-violet-400 animate-pulse"
                          : t.status === "cancelled"
                          ? "bg-slate-700 text-slate-400"
                          : "bg-amber-500/10 text-amber-400"
                      }`}
                    >
                      {t.status}
                    </span>
                    {t.verified && (
                      <span className="text-emerald-400 flex items-center gap-0.5">
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
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 mb-2">
              Launch Autonomous Objective
            </h3>
            <form onSubmit={handleStart} className="flex gap-2">
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. Build a complete task management application using React, FastAPI and MongoDB"
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

          {/* Active Task Execution Monitor */}
          {activeTask ? (
            <div className="space-y-6">
              {/* Task Header */}
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-base font-bold text-white">{activeTask.prompt}</h2>
                  <span
                    className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${
                      activeTask.status === "completed"
                        ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                        : "bg-violet-500/10 text-violet-400 border-violet-500/20"
                    }`}
                  >
                    Status: {activeTask.status}
                  </span>
                </div>
                {plan && (
                  <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-800/60">
                    <span className="font-semibold text-slate-300">Strategy:</span> {plan.analysis}
                  </p>
                )}
              </div>

              {/* Execution Steps List */}
              <div className="space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Plan Steps ({steps.length})
                </h3>

                {steps.map((s) => {
                  const isDone = s.status === "completed";
                  const isRunning = s.status === "in_progress";
                  const isFailed = s.status === "failed";

                  return (
                    <div
                      key={s.step_id}
                      className={`border rounded-xl p-4 transition-all ${
                        isRunning
                          ? "bg-violet-950/20 border-violet-500/50 shadow-md shadow-violet-500/10"
                          : isDone
                          ? "bg-slate-900/80 border-slate-800"
                          : isFailed
                          ? "bg-rose-950/20 border-rose-500/30"
                          : "bg-slate-900/30 border-slate-800/50 opacity-60"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2.5">
                          {isDone ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          ) : isRunning ? (
                            <RefreshCw className="w-4 h-4 text-violet-400 animate-spin" />
                          ) : isFailed ? (
                            <AlertTriangle className="w-4 h-4 text-rose-400" />
                          ) : (
                            <Clock className="w-4 h-4 text-slate-500" />
                          )}
                          <span className="text-xs font-bold text-white">
                            Step {s.step_id}: {s.title}
                          </span>
                        </div>

                        {s.tool && (
                          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-indigo-400 border border-slate-700">
                            {s.tool}
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-400 ml-6.5 leading-relaxed">{s.description}</p>

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

