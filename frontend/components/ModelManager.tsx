"use client";

import React, { useState, useEffect } from "react";
import { Cpu, CheckCircle2, RefreshCw, Zap, Award, Layers } from "lucide-react";
import { fetchModels } from "@/services/api";

export function ModelManager() {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      const res = await fetchModels();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const roles = [
    { role: "general", title: "General Conversational", model: data?.role_mapping?.general || "qwen2.5:7b", desc: "Day-to-day conversation, explanations, and long context discussions." },
    { role: "coding", title: "Coding & Debugging", model: data?.role_mapping?.coding || "qwen2.5-coder:7b", desc: "Multi-file code generation, syntax repair, and algorithmic refactoring." },
    { role: "reasoning", title: "Complex Reasoning & Planning", model: data?.role_mapping?.reasoning || "deepseek-r1:8b", desc: "Architectural synthesis, multi-step agent plans, and dependency resolution." },
    { role: "lightweight", title: "Lightweight & Fast", model: data?.role_mapping?.lightweight || "llama3.2:1b", desc: "Fast token generation, classification, and repetitive summarization." },
    { role: "embedding", title: "Semantic Embeddings", model: data?.role_mapping?.embedding || "nomic-embed-text", desc: "Vector indexing, semantic code chunk search, and memory recall." },
  ];

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-y-auto p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-xl font-bold text-white flex items-center gap-2.5">
            <Cpu className="w-5 h-5 text-indigo-400" />
            Model Registry & Hardware Routing
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Dynamic, open-weight model assignments optimized for your local machine hardware.
          </p>
        </div>

        <button
          onClick={load}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Hardware Profile Card */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">RAM Capacity</div>
          <div className="text-xl font-extrabold text-white">16 GB</div>
          <div className="text-[11px] text-slate-500 mt-1">16 Logical CPU cores available</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">GPU VRAM</div>
          <div className="text-xl font-extrabold text-indigo-400">4 GB VRAM</div>
          <div className="text-[11px] text-slate-500 mt-1">NVIDIA RTX 3050 Laptop GPU</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Optimal Quantization</div>
          <div className="text-xl font-extrabold text-emerald-400">4-bit / Q4_K_M</div>
          <div className="text-[11px] text-slate-500 mt-1">Fits 7B-8B models with full GPU offload</div>
        </div>
      </div>

      {/* Role Mappings */}
      <div className="space-y-4">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Configured Intelligence Roles
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {roles.map((r) => (
            <div key={r.role} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-2">
                  <Award className="w-4 h-4 text-indigo-400" />
                  {r.title}
                </span>
                <span className="font-mono text-xs px-2 py-0.5 rounded bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                  {r.model}
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{r.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Installed Ollama Models */}
      <div className="space-y-3 pt-4 border-t border-slate-800">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
          Installed Local Ollama Models ({data?.installed_models?.length || 0})
        </h2>

        {data?.installed_models?.length > 0 ? (
          <div className="grid grid-cols-2 gap-3">
            {data.installed_models.map((m: any) => (
              <div key={m.name} className="p-3 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-mono text-white">{m.name}</span>
                </div>
                <span className="text-[11px] text-slate-400">{(m.size / 1e9).toFixed(2)} GB</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl text-xs text-slate-400 space-y-2">
            <p className="font-semibold text-slate-300">No local Ollama models detected yet.</p>
            <p>
              To pull recommended open-weight models for your RTX 3050 (4GB VRAM), execute in your terminal:
            </p>
            <pre className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-indigo-300 font-mono text-[11px]">
              ollama pull qwen2.5:7b{"\n"}
              ollama pull qwen2.5-coder:7b{"\n"}
              ollama pull deepseek-r1:8b{"\n"}
              ollama pull llama3.2:1b
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

