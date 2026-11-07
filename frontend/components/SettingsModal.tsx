"use client";

import React from "react";
import { Settings as SettingsIcon, Database, Server, Shield, HardDrive } from "lucide-react";
import { SystemHealth } from "@/types";

interface SettingsModalProps {
  health: SystemHealth | null;
}

export function SettingsModal({ health }: SettingsModalProps) {
  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-y-auto p-8 space-y-6">
      <div className="pb-4 border-b border-slate-800">
        <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
          <SettingsIcon className="w-5 h-5 text-indigo-400" />
          DODO Platform Configuration
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Review system connections, permissions, and runtime parameters.
        </p>
      </div>

      <div className="space-y-4 max-w-3xl">
        {/* Database Config */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Database className="w-4 h-4 text-emerald-400" />
            <span>MongoDB Database Layer</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-1">Status:</span>
              <span className="font-semibold text-emerald-400">{health?.database?.status || "Connecting..."}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Active Database:</span>
              <span className="font-mono text-slate-200">{health?.database?.database || "dodo_db"}</span>
            </div>
          </div>
        </div>

        {/* Inference Config */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Server className="w-4 h-4 text-indigo-400" />
            <span>AI Inference Engine</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-1">Runtime Provider:</span>
              <span className="font-medium text-slate-200">Ollama / Open-Weight Engine</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Inference Endpoint:</span>
              <span className="font-mono text-slate-200">{health?.inference_engine?.base_url || "http://localhost:11434"}</span>
            </div>
          </div>
        </div>

        {/* Local Agent Config */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-sm font-bold text-white">
            <Shield className="w-4 h-4 text-amber-400" />
            <span>Local Agent & Security Boundary</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block mb-1">Authorized Workspace Jail:</span>
              <span className="font-mono text-slate-200 text-[11px]">{health?.local_agent?.authorized_workspace || "D:\\DODO\\workspace"}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-1">Agent Endpoint:</span>
              <span className="font-mono text-slate-200">http://127.0.0.1:8001</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

