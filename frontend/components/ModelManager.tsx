"use client";

import React, { useState, useEffect } from "react";
import { Cpu, CheckCircle2, RefreshCw, Zap, Award, Layers, AlertCircle, HardDrive, ShieldAlert, Check } from "lucide-react";
import { fetchModels, fetchModelsStatus, setModelRole } from "@/services/api";

export function ModelManager() {
  const [data, setData] = useState<any>(null);
  const [statusData, setStatusData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [savingRole, setSavingRole] = useState<string | null>(null);
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);

  const load = async () => {
    setIsLoading(true);
    try {
      const [modelsRes, statusRes] = await Promise.all([
        fetchModels(),
        fetchModelsStatus(),
      ]);
      setData(modelsRes);
      setStatusData(statusRes);
    } catch (e) {
      console.error("Failed to load models data", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleRoleChange = async (role: string, modelName: string) => {
    setSavingRole(role);
    try {
      await setModelRole(role, modelName);
      setSavedSuccess(role);
      setTimeout(() => setSavedSuccess(null), 2000);
      await load();
    } catch (e) {
      console.error("Failed to assign model role", e);
    } finally {
      setSavingRole(null);
    }
  };

  const isOnline = statusData?.ollama?.status === "online";
  const installedModels = data?.installed_models || [];
  const roleMapping = data?.role_mapping || {};
  const rolesStatus = data?.roles_status || {};
  const hw = statusData?.hardware || {
    system_ram_gb: 16.0,
    gpu_name: "NVIDIA GeForce RTX 3050 Laptop GPU",
    gpu_vram_gb: 4.0,
    vram_headroom_gb: 3.2,
    recommended_quantization: "Q4_K_M (4-bit)",
  };

  const roles = [
    { role: "general", title: "General Assistant", desc: "Day-to-day conversation, explanations, and long context understanding." },
    { role: "coding", title: "Coding & Debugging", desc: "Source code generation, bug fixing, and syntax refactoring." },
    { role: "reasoning", title: "Complex Reasoning & Planning", desc: "System design, step-by-step logic, and architectural analysis." },
    { role: "lightweight", title: "Lightweight & Fast", desc: "Instant classification, short summaries, and low-latency triage." },
    { role: "embedding", title: "Semantic Retrieval", desc: "Local vector indexing and semantic memory search." },
  ];

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-y-auto p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Model Manager & Local Intelligence Registry
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time local open-weight model status, role mappings, and hardware VRAM allocation.
          </p>
        </div>

        <button
          onClick={load}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh Status</span>
        </button>
      </div>

      {/* Ollama Daemon Status Banner */}
      <div className={`p-4 rounded-2xl border flex items-center justify-between ${
        isOnline
          ? "bg-emerald-950/20 border-emerald-500/30 text-emerald-300"
          : "bg-rose-950/20 border-rose-500/30 text-rose-300"
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isOnline ? "bg-emerald-400 animate-pulse" : "bg-rose-500"}`} />
          <div>
            <div className="text-xs font-bold uppercase tracking-wider">
              Ollama Daemon: {isOnline ? "Connected & Active" : "Offline / Unreachable"}
            </div>
            <div className="text-[11px] text-slate-400 mt-0.5 font-mono">
              Endpoint: {statusData?.ollama?.base_url || "http://127.0.0.1:11434"} | Version: {statusData?.ollama?.version || "—"} | Latency: {statusData?.ollama?.latency_ms ? `${statusData.ollama.latency_ms} ms` : "—"}
            </div>
          </div>
        </div>

        <span className="text-xs font-medium px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-300">
          Installed Models: {installedModels.length}
        </span>
      </div>

      {/* Machine Hardware Profile */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">System RAM</div>
          <div className="text-xl font-extrabold text-white">{hw.system_ram_gb} GB</div>
          <div className="text-[11px] text-slate-500 mt-1">16 Logical CPU cores available</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">GPU Dedicated VRAM</div>
          <div className="text-xl font-extrabold text-indigo-400">{hw.gpu_vram_gb} GB VRAM</div>
          <div className="text-[11px] text-slate-500 mt-1">{hw.gpu_name}</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Recommended Quantization</div>
          <div className="text-xl font-extrabold text-emerald-400">{hw.recommended_quantization}</div>
          <div className="text-[11px] text-slate-500 mt-1">Optimal VRAM fit for 7B/8B models</div>
        </div>
      </div>

      {/* Role Assignment Controls */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Intelligence Role Mappings
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map((r) => {
            const currentModel = roleMapping[r.role] || "—";
            const statusInfo = rolesStatus[r.role];
            const isInstalled = statusInfo?.is_installed ?? false;

            return (
              <div key={r.role} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-2">
                    <Award className="w-4 h-4 text-indigo-400" />
                    {r.title}
                  </span>
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                    isInstalled
                      ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                  }`}>
                    {isInstalled ? "Ready Locally" : "Not Yet Downloaded"}
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">{r.desc}</p>

                <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
                  <label className="text-[11px] text-slate-400 font-medium">Model:</label>
                  <select
                    value={currentModel}
                    onChange={(e) => handleRoleChange(r.role, e.target.value)}
                    disabled={savingRole === r.role}
                    className="flex-1 bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-indigo-500 cursor-pointer font-mono"
                  >
                    <option value={currentModel}>{currentModel} (Assigned)</option>
                    {installedModels
                      .filter((m: any) => m.name !== currentModel)
                      .map((m: any) => (
                        <option key={m.name} value={m.name}>
                          {m.name} ({m.size_gb} GB)
                        </option>
                      ))}
                  </select>
                  {savedSuccess === r.role && (
                    <span className="text-emerald-400 text-xs flex items-center gap-0.5">
                      <Check className="w-3.5 h-3.5" />
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Installed Ollama Models Table */}
      <div className="space-y-3 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Actual Installed Local Models ({installedModels.length})
          </h2>
          <span className="text-[11px] text-slate-500">Source: GET /api/tags (Ollama API)</span>
        </div>

        {installedModels.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {installedModels.map((m: any) => (
              <div key={m.name} className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-mono font-bold text-white">{m.name}</span>
                  </div>
                  <span className="text-[11px] font-mono text-indigo-400 bg-indigo-600/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {m.size_gb} GB
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 flex items-center gap-3 font-mono">
                  <span>Family: {m.family || "—"}</span>
                  <span>Params: {m.parameter_size || "—"}</span>
                  <span>Quant: {m.quantization_level || "—"}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl text-xs text-slate-400 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-semibold text-sm">
              <AlertCircle className="w-4 h-4" />
              <span>No models downloaded yet in Ollama</span>
            </div>
            <p className="leading-relaxed">
              Ollama is running on your machine, but no local weights have been pulled yet. In accordance with Phase 2 safety rules, <strong>DODO will never download models automatically</strong> without your explicit command.
            </p>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 font-mono text-[11px] text-slate-300 space-y-1">
              <div className="text-slate-500 text-[10px] uppercase font-bold tracking-wider mb-1">
                Recommended Models for 4GB VRAM GPU (Run manually with your approval):
              </div>
              <div className="text-indigo-400">ollama pull llama3.2:1b        # Ultra-fast lightweight model (~1.3 GB, 100% VRAM)</div>
              <div className="text-indigo-400">ollama pull qwen2.5-coder:7b     # High-accuracy coding model (~4.7 GB)</div>
              <div className="text-indigo-400">ollama pull deepseek-r1:8b      # Reasoning and planning model (~4.9 GB)</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
