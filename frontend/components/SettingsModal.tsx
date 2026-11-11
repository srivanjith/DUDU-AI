"use client";

import React, { useEffect } from "react";
import {
  Settings as SettingsIcon,
  Database,
  Server,
  Shield,
  HardDrive,
  X,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
} from "lucide-react";
import { SystemHealth } from "@/types";

interface SettingsModalProps {
  health: SystemHealth | null;
  onClose: () => void;
}

export function SettingsModal({ health, onClose }: SettingsModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const dbStatus = health?.database?.status || "connecting";
  const ollamaStatus = health?.inference_engine?.status || "offline";
  const localAgentStatus = health?.local_agent?.status || "offline";

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh] animate-in zoom-in-95 duration-150"
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between select-none">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <SettingsIcon className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                DODO Platform Configuration
              </h2>
              <p className="text-xs text-slate-400">
                Hardware parameters, local endpoints, and security isolation
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4 text-xs font-sans">
          {/* Database Configuration Card */}
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-white text-sm">
                <Database className="w-4 h-4 text-emerald-400" />
                <span>MongoDB Storage Engine</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                  dbStatus === "connected"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                }`}
              >
                {dbStatus === "connected" ? "Atlas Production Live" : "Fallback Mock"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-slate-300">
              <div>
                <span className="text-slate-500 block text-[11px] mb-0.5">Database Name:</span>
                <span className="font-mono text-slate-200">{health?.database?.database || "dodo_db"}</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px] mb-0.5">Roundtrip Latency:</span>
                <span className="font-mono text-emerald-400">
                  {health?.database?.latency_ms ? `${Math.round(health.database.latency_ms)} ms` : "N/A"}
                </span>
              </div>
            </div>
          </div>

          {/* Inference Model & GPU Card */}
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-white text-sm">
                <Server className="w-4 h-4 text-indigo-400" />
                <span>Local AI Inference Engine</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                  ollamaStatus === "online"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                }`}
              >
                {ollamaStatus === "online" ? "Online (11434)" : "Offline"}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-slate-300">
              <div>
                <span className="text-slate-500 block text-[11px] mb-0.5">Default Model:</span>
                <span className="font-mono text-slate-200">qwen2.5-coder:1.5b</span>
              </div>
              <div>
                <span className="text-slate-500 block text-[11px] mb-0.5">Target Hardware Profile:</span>
                <span className="text-slate-200">16GB RAM + RTX 3050 (4GB VRAM)</span>
              </div>
            </div>
          </div>

          {/* Local Agent & Workspace Boundary */}
          <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-bold text-white text-sm">
                <Shield className="w-4 h-4 text-amber-400" />
                <span>Security Jail & Local Agent</span>
              </div>
              <span
                className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold uppercase ${
                  localAgentStatus === "online"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-slate-800 text-slate-400 border border-slate-700"
                }`}
              >
                Port 8001 {localAgentStatus}
              </span>
            </div>
            <div className="space-y-2 text-slate-300">
              <div>
                <span className="text-slate-500 block text-[11px] mb-0.5">Authorized Workspace Root:</span>
                <span className="font-mono text-amber-300 bg-slate-900 px-2 py-1 rounded block text-[11px] border border-slate-800">
                  {health?.local_agent?.authorized_workspace || "D:\\DODO\\workspace"}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-normal">
                Strict path-jailing prevents traversal outside the authorized workspace directory. High-risk commands require explicit user approval.
              </p>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs select-none">
          <span className="text-slate-500 font-mono text-[11px]">DODO v1.0 • Autonomous AI IDE</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
