"use client";

import React, { useState } from "react";
import { Terminal as TerminalIcon, Play, CornerDownLeft, ShieldAlert } from "lucide-react";
import { executeTerminalCommand } from "@/services/api";

interface CommandLog {
  command: string;
  output: string;
  error?: string;
  exit_code: number;
}

export function TerminalPanel() {
  const [command, setCommand] = useState("");
  const [logs, setLogs] = useState<CommandLog[]>([
    {
      command: "dodo --status",
      output: "🦅 DODO Terminal Execution Subsystem Online.\nWorkspace: D:\\DODO\\workspace\nPermission Policy: Controlled Subprocess Isolation Active.",
      exit_code: 0,
    },
  ]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRun = async (cmdToRun?: string) => {
    const cmd = cmdToRun || command;
    if (!cmd.trim() || isRunning) return;

    setIsRunning(true);
    try {
      const res = await executeTerminalCommand(cmd);
      setLogs((prev) => [
        ...prev,
        {
          command: cmd,
          output: res.stdout || (res.success ? "Command completed successfully." : ""),
          error: res.stderr || res.error,
          exit_code: res.exit_code,
        },
      ]);
      if (!cmdToRun) setCommand("");
    } catch (e: any) {
      setLogs((prev) => [
        ...prev,
        {
          command: cmd,
          output: "",
          error: e.message || "Failed to execute command",
          exit_code: -1,
        },
      ]);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 font-mono">
      {/* Header */}
      <div className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/50">
        <div className="flex items-center gap-2.5 text-xs text-amber-400 font-semibold uppercase tracking-wider">
          <TerminalIcon className="w-4 h-4" />
          <span>Mode C — Terminal & Process Execution</span>
        </div>

        {/* Quick run presets */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleRun("pytest -v")}
            disabled={isRunning}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-colors"
          >
            Run pytest
          </button>
          <button
            onClick={() => handleRun("git status")}
            disabled={isRunning}
            className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-colors"
          >
            git status
          </button>
        </div>
      </div>

      {/* Terminal Output Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
        {logs.map((log, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex items-center gap-2 text-slate-400">
              <span className="text-amber-400 font-bold">$</span>
              <span className="text-white font-medium">{log.command}</span>
              <span
                className={`text-[10px] ml-auto px-1.5 py-0.2 rounded ${
                  log.exit_code === 0 ? "text-emerald-400 bg-emerald-500/10" : "text-rose-400 bg-rose-500/10"
                }`}
              >
                exit: {log.exit_code}
              </span>
            </div>
            {log.output && (
              <pre className="text-slate-300 whitespace-pre-wrap pl-4 border-l border-slate-800 leading-relaxed font-mono">
                {log.output}
              </pre>
            )}
            {log.error && (
              <pre className="text-rose-400 whitespace-pre-wrap pl-4 border-l border-rose-900/60 leading-relaxed font-mono">
                {log.error}
              </pre>
            )}
          </div>
        ))}
      </div>

      {/* Terminal Input Bar */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRun();
          }}
          className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5"
        >
          <span className="text-amber-400 font-bold text-sm">$</span>
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter terminal command (e.g. pytest, dir, python backend_app.py)..."
            disabled={isRunning}
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={!command.trim() || isRunning}
            className="p-1.5 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 text-white rounded-lg text-xs transition-colors"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
          </button>
        </form>
      </div>
    </div>
  );
}

