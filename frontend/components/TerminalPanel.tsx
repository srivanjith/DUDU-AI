"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Terminal as TerminalIcon,
  Play,
  Square,
  Trash2,
  Server,
  History,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  Radio,
  RefreshCw,
  X,
  ExternalLink,
} from "lucide-react";
import {
  executeTerminalCommand,
  fetchLocalAgentStatus,
  fetchTerminalProcesses,
  killTerminalProcess,
  fetchTerminalHistory,
  approveTerminalCommand,
  cancelTerminalCommand,
  fetchPendingApprovals,
} from "@/services/api";
import { TerminalProcess, TerminalAuditRecord, PendingApprovalCommand } from "@/types";

export function TerminalPanel() {
  const terminalRef = useRef<HTMLDivElement>(null);
  const termInstance = useRef<any>(null);
  const fitAddonRef = useRef<any>(null);

  const [command, setCommand] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [currentExecId, setCurrentExecId] = useState<string | null>(null);
  const [lastExitCode, setLastExitCode] = useState<number | null>(null);
  const [localAgentStatus, setLocalAgentStatus] = useState<{
    status: string;
    port?: number;
    authorized_workspace?: string;
    active_processes_count?: number;
  }>({ status: "checking" });

  // Drawers & Modals
  const [activeTab, setActiveTab] = useState<"terminal" | "processes" | "history">("terminal");
  const [processes, setProcesses] = useState<TerminalProcess[]>([]);
  const [history, setHistory] = useState<TerminalAuditRecord[]>([]);
  const [pendingApproval, setPendingApproval] = useState<PendingApprovalCommand | null>(null);
  const [isApproving, setIsApproving] = useState(false);

  // Initialize xterm.js
  useEffect(() => {
    let term: any = null;
    let fitAddon: any = null;

    const initXterm = async () => {
      if (!terminalRef.current) return;
      terminalRef.current.innerHTML = "";

      const { Terminal } = await import("@xterm/xterm");
      const { FitAddon } = await import("@xterm/addon-fit");
      await import("@xterm/xterm/css/xterm.css");

      term = new Terminal({
        cursorBlink: true,
        fontSize: 13,
        fontFamily: "'JetBrains Mono', 'Fira Code', 'Courier New', monospace",
        theme: {
          background: "#020617", // slate-950
          foreground: "#e2e8f0", // slate-200
          cursor: "#f59e0b",     // amber-500
          selectionBackground: "#334155",
          black: "#020617",
          red: "#f43f5e",
          green: "#10b981",
          yellow: "#f59e0b",
          blue: "#38bdf8",
          magenta: "#c084fc",
          cyan: "#2dd4bf",
          white: "#f8fafc",
          brightBlack: "#475569",
          brightRed: "#fb7185",
          brightGreen: "#34d399",
          brightYellow: "#fbbf24",
          brightBlue: "#60a5fa",
          brightMagenta: "#e879f9",
          brightCyan: "#5eead4",
          brightWhite: "#ffffff",
        },
        convertEol: true,
        scrollback: 5000,
      });

      fitAddon = new FitAddon();
      term.loadAddon(fitAddon);
      term.open(terminalRef.current);
      fitAddon.fit();

      termInstance.current = term;
      fitAddonRef.current = fitAddon;

      // Welcome Banner
      term.writeln("\x1b[1;33m=================================================================\x1b[0m");
      term.writeln("\x1b[1;36m  🦅 DODO Local Agent Terminal Subsystem Online (Phase 5)\x1b[0m");
      term.writeln("\x1b[90m  Autonomous Development Runtime with Path Jailing & Audit Logging\x1b[0m");
      term.writeln("\x1b[1;33m=================================================================\x1b[0m");
      term.writeln("");
    };

    initXterm();

    const handleResize = () => {
      try {
        fitAddonRef.current?.fit();
      } catch (e) {}
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      try {
        term?.dispose();
      } catch (e) {}
    };
  }, []);

  // Poll Local Agent Status & Processes
  useEffect(() => {
    checkAgentStatus();
    loadProcesses();
    const interval = setInterval(() => {
      checkAgentStatus();
      if (activeTab === "processes") loadProcesses();
      checkPendingApprovals();
    }, 6000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const checkAgentStatus = async () => {
    try {
      const res = await fetchLocalAgentStatus();
      setLocalAgentStatus(res);
    } catch {
      setLocalAgentStatus({ status: "offline" });
    }
  };

  const loadProcesses = async () => {
    try {
      const procs = await fetchTerminalProcesses();
      setProcesses(procs || []);
    } catch (e) {
      console.error("Failed to load processes:", e);
    }
  };

  const loadHistory = async () => {
    try {
      const hist = await fetchTerminalHistory(50);
      setHistory(hist || []);
    } catch (e) {
      console.error("Failed to load history:", e);
    }
  };

  const checkPendingApprovals = async () => {
    try {
      const pend = await fetchPendingApprovals();
      if (pend && pend.length > 0) {
        setPendingApproval(pend[0]);
      } else {
        setPendingApproval(null);
      }
    } catch (e) {}
  };

  // Run command handler
  const handleRun = async (cmdToRun?: string, approved: boolean = false) => {
    const cmd = cmdToRun || command;
    if (!cmd.trim() || isRunning) return;

    const term = termInstance.current;
    if (term) {
      term.writeln(`\r\n\x1b[1;33m$\x1b[0m \x1b[1;37m${cmd}\x1b[0m`);
    }

    setIsRunning(true);
    setLastExitCode(null);

    try {
      const res = await executeTerminalCommand(cmd, "", 60, approved);
      setCurrentExecId(res.execution_id || null);

      if (res.requires_approval) {
        if (term) {
          term.writeln(
            `\r\n\x1b[1;33m[SECURITY GATEKEEPER]\x1b[0m Command requires explicit approval: \x1b[36m${res.reason || "Dependency installation or system modification"}\x1b[0m`
          );
        }
        setPendingApproval({
          execution_id: res.execution_id,
          command: cmd,
          cwd: "",
          category: res.category || "DEPENDENCY_INSTALL",
          reason: res.reason || "Action requires user confirmation",
          status: "pending_approval",
          risk_level: res.risk_level || "requires_approval",
        });
        setIsRunning(false);
        return;
      }

      if (res.stdout && term) {
        term.write(res.stdout);
      }
      if (res.stderr && term) {
        term.writeln(`\x1b[31m${res.stderr}\x1b[0m`);
      }

      setLastExitCode(res.exit_code !== undefined ? res.exit_code : 0);

      if (term) {
        if (res.exit_code === 0) {
          term.writeln(`\r\n\x1b[1;32m✔ Process exited successfully (code 0)\x1b[0m`);
        } else {
          term.writeln(`\r\n\x1b[1;31m✘ Process failed with exit code ${res.exit_code}\x1b[0m`);
        }
      }

      if (!cmdToRun) setCommand("");
      loadProcesses();
    } catch (err: any) {
      if (term) {
        term.writeln(`\r\n\x1b[1;31m[DODO Execution Error]: ${err.message || "Failed to execute command."}\x1b[0m`);
      }
      setLastExitCode(-1);
    } finally {
      setIsRunning(false);
      setCurrentExecId(null);
    }
  };

  const handleCancel = async () => {
    if (!currentExecId) return;
    try {
      await cancelTerminalCommand(currentExecId);
      termInstance.current?.writeln(`\r\n\x1b[1;31m[PROCESS CANCELLED BY USER]\x1b[0m`);
      setIsRunning(false);
      setCurrentExecId(null);
    } catch (e: any) {
      console.error("Cancel failed:", e);
    }
  };

  const handleApprove = async () => {
    if (!pendingApproval) return;
    setIsApproving(true);
    try {
      termInstance.current?.writeln(`\r\n\x1b[1;32m[APPROVAL GRANTED]\x1b[0m Executing: ${pendingApproval.command}`);
      const res = await approveTerminalCommand(pendingApproval.execution_id);
      if (res.stdout && termInstance.current) {
        termInstance.current.write(res.stdout);
      }
      if (res.stderr && termInstance.current) {
        termInstance.current.writeln(`\x1b[31m${res.stderr}\x1b[0m`);
      }
      setLastExitCode(res.exit_code);
      setPendingApproval(null);
      loadProcesses();
    } catch (e: any) {
      termInstance.current?.writeln(`\r\n\x1b[1;31m[Approval Execution Failed]: ${e.message}\x1b[0m`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleDeny = async () => {
    if (!pendingApproval) return;
    try {
      await cancelTerminalCommand(pendingApproval.execution_id);
      termInstance.current?.writeln(`\r\n\x1b[1;31m[COMMAND REJECTED BY USER]\x1b[0m Approval denied for: ${pendingApproval.command}`);
      setPendingApproval(null);
    } catch (e) {}
  };

  const handleKillProcess = async (pid: number) => {
    try {
      await killTerminalProcess(pid);
      termInstance.current?.writeln(`\r\n\x1b[1;33m[Dev Server Stopped]\x1b[0m Terminated process PID ${pid}`);
      loadProcesses();
    } catch (e) {}
  };

  const handleClear = () => {
    termInstance.current?.clear();
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 font-mono relative overflow-hidden">
      {/* Header Bar */}
      <div className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/60 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400">
            <TerminalIcon className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-white">Mode C — Terminal & Local Runtime</span>
              <span className="px-1.5 py-0.5 text-[10px] rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">
                Phase 5 Active
              </span>
            </div>
          </div>
        </div>

        {/* View Switchers & Controls */}
        <div className="flex items-center gap-3">
          {/* Local Agent Status Pill */}
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border ${
              localAgentStatus.status === "online"
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-rose-500/10 border-rose-500/30 text-rose-400"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                localAgentStatus.status === "online" ? "bg-emerald-400 animate-pulse" : "bg-rose-400"
              }`}
            />
            <span>
              {localAgentStatus.status === "online"
                ? `Local Agent :${localAgentStatus.port || 8001}`
                : "Local Agent Offline"}
            </span>
          </div>

          {/* Tab Selector */}
          <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-xs">
            <button
              onClick={() => setActiveTab("terminal")}
              className={`px-3 py-1 rounded-md transition-colors ${
                activeTab === "terminal" ? "bg-amber-500/20 text-amber-400 font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              Terminal
            </button>
            <button
              onClick={() => {
                setActiveTab("processes");
                loadProcesses();
              }}
              className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === "processes" ? "bg-amber-500/20 text-amber-400 font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>Processes ({processes.length})</span>
            </button>
            <button
              onClick={() => {
                setActiveTab("history");
                loadHistory();
              }}
              className={`px-3 py-1 rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === "history" ? "bg-amber-500/20 text-amber-400 font-semibold" : "text-slate-400 hover:text-white"
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>History</span>
            </button>
          </div>

          {/* Quick Presets */}
          <button
            onClick={() => handleRun("python -m pytest test_tasks.py -v")}
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

          {/* Clear Button */}
          <button
            onClick={handleClear}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            title="Clear Terminal"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative flex flex-col overflow-hidden">
        {/* Terminal Container */}
        <div
          ref={terminalRef}
          className={`flex-1 p-3 bg-slate-950 overflow-hidden ${activeTab !== "terminal" ? "hidden" : ""}`}
        />

        {/* Processes View */}
        {activeTab === "processes" && (
          <div className="flex-1 p-6 overflow-y-auto bg-slate-950 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">Active Background Processes & Dev Servers</h3>
                <p className="text-xs text-slate-400">Processes running in the jailed workspace monitored by DODO Local Agent.</p>
              </div>
              <button
                onClick={loadProcesses}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {processes.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No active development servers or background processes currently running.
              </div>
            ) : (
              <div className="grid gap-3">
                {processes.map((p) => (
                  <div
                    key={p.pid}
                    className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="text-xs font-bold text-white font-mono">{p.command}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 font-mono">
                          PID {p.pid}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          {p.category}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Started: {new Date(p.start_time).toLocaleTimeString()} | CWD: {p.cwd}
                      </div>
                      {p.recent_logs && p.recent_logs.length > 0 && (
                        <div className="mt-2 p-2 bg-slate-950 rounded border border-slate-800/80 text-[10px] text-slate-400 font-mono">
                          {p.recent_logs[p.recent_logs.length - 1]}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => handleKillProcess(p.pid)}
                      className="px-3 py-1.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-lg text-xs font-semibold transition-colors"
                    >
                      Stop Server
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* History View */}
        {activeTab === "history" && (
          <div className="flex-1 p-6 overflow-y-auto bg-slate-950 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-semibold text-white">Command Execution Audit History</h3>
                <p className="text-xs text-slate-400">Verifiable tamper-evident execution logs recorded by Local Agent.</p>
              </div>
              <button
                onClick={loadHistory}
                className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {history.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No execution audit records logged yet.
              </div>
            ) : (
              <div className="space-y-2">
                {history.slice().reverse().map((h, i) => (
                  <div
                    key={i}
                    className="p-3 bg-slate-900/40 border border-slate-800/80 rounded-lg flex items-center justify-between text-xs"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className={`w-1.5 h-1.5 rounded-full ${h.success ? "bg-emerald-400" : "bg-rose-400"}`} />
                        <span className="font-bold text-white font-mono">{h.command}</span>
                        <span className="text-[10px] text-slate-500 font-mono">({h.category})</span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {new Date(h.timestamp).toLocaleTimeString()} · {h.duration_ms}ms · CWD: {h.cwd}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                          h.success ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                        }`}
                      >
                        exit: {h.exit_code}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Command Approval Modal */}
      {pendingApproval && (
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-amber-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-amber-500/20 text-amber-400 rounded-xl">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white">Security Gate: Approval Required</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  The autonomous engine requested a command that modifies dependencies or requires user authorization.
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-slate-400">Category:</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono font-semibold">
                  {pendingApproval.category}
                </span>
              </div>
              <div className="text-xs font-mono bg-slate-900 p-2 rounded text-amber-300 break-all border border-slate-800">
                {pendingApproval.command}
              </div>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                <strong className="text-slate-200">Justification:</strong> {pendingApproval.reason}
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={handleDeny}
                disabled={isApproving}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
              >
                Deny & Abort
              </button>
              <button
                onClick={handleApprove}
                disabled={isApproving}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-xl text-xs font-bold transition-colors flex items-center gap-1.5 shadow-lg shadow-amber-950"
              >
                {isApproving ? "Executing..." : "Approve & Execute"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Terminal Input Bar */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60 z-10">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRun();
          }}
          className="flex items-center gap-2 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2"
        >
          <span className="text-amber-400 font-bold text-sm">$</span>
          <input
            type="text"
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter terminal command (e.g. python -m pytest test_tasks.py -v, git status, dir)..."
            disabled={isRunning}
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none"
          />

          {isRunning ? (
            <button
              type="button"
              onClick={handleCancel}
              className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              <Square className="w-3.5 h-3.5 fill-white" />
              <span>Cancel</span>
            </button>
          ) : (
            <button
              type="submit"
              disabled={!command.trim() || isRunning}
              className="p-1.5 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-800 text-white rounded-lg text-xs transition-colors"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
