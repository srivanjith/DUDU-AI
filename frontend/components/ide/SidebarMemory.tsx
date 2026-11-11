"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Search,
  Plus,
  Trash2,
  Sparkles,
  RefreshCw,
  FolderGit2,
  Sliders,
  Maximize2,
  Star,
} from "lucide-react";
import { MemoryRecord } from "@/types";
import {
  fetchMemories,
  fetchMemoryCategories,
  createMemory,
  deleteMemory,
} from "@/services/api";

interface SidebarMemoryProps {
  onOpenFullView: () => void;
}

export function SidebarMemory({ onOpenFullView }: SidebarMemoryProps) {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCat, setSelectedCat] = useState<string>("all");
  const [isLoading, setIsLoading] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState("project");

  const loadMemories = async () => {
    setIsLoading(true);
    try {
      const data = await fetchMemories(selectedCat === "all" ? undefined : selectedCat);
      setMemories(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, [selectedCat]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    try {
      await createMemory({
        content: newContent.trim(),
        category: newCategory,
        importance: 4,
        tags: ["ide"],
      });
      setNewContent("");
      setIsAdding(false);
      loadMemories();
    } catch (e) {
      console.error(e);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (e) {
      console.error(e);
    }
  };

  const filtered = memories.filter((m) =>
    m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (m.tags || []).some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 select-none overflow-hidden text-xs">
      {/* Header */}
      <div className="h-8 px-3 border-b border-slate-800/80 flex items-center justify-between font-semibold uppercase tracking-wider text-slate-400">
        <div className="flex items-center gap-1.5 text-purple-400">
          <Brain className="w-3.5 h-3.5" />
          <span className="text-white text-xs">Project Memory</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsAdding(!isAdding)}
            title="Add Quick Memory"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors text-slate-400"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={loadMemories}
            title="Refresh Memory"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors text-slate-400"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
          <button
            onClick={onOpenFullView}
            title="Expand Full Memory Center"
            className="p-1 hover:text-purple-300 hover:bg-purple-950/40 rounded transition-colors text-purple-400"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Search Input */}
      <div className="p-2 border-b border-slate-800/60">
        <div className="relative">
          <Search className="w-3 h-3 absolute left-2 top-2 text-slate-500" />
          <input
            type="text"
            placeholder="Search memories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 pl-6 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500/50"
          />
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1 mt-1.5 overflow-x-auto pb-0.5 text-[10px]">
          {["all", "project", "task_experience", "preference"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCat(cat)}
              className={`px-1.5 py-0.5 rounded capitalize whitespace-nowrap transition-colors ${
                selectedCat === cat
                  ? "bg-purple-600/30 text-purple-300 border border-purple-500/40 font-semibold"
                  : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {cat.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Add Form */}
      {isAdding && (
        <form onSubmit={handleCreate} className="p-2.5 bg-slate-950/90 border-b border-purple-500/30 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-semibold text-purple-300">
            <span>New Memory Record</span>
            <select
              value={newCategory}
              onChange={(e) => setNewCategory(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300"
            >
              <option value="project">Project</option>
              <option value="task_experience">Experience</option>
              <option value="preference">Preference</option>
            </select>
          </div>
          <textarea
            rows={2}
            autoFocus
            placeholder="Store context or architectural rule..."
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 resize-none"
          />
          <div className="flex items-center justify-end gap-1.5">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-2 py-0.5 text-slate-400 hover:text-white text-[11px]"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-2.5 py-0.5 bg-purple-600 hover:bg-purple-500 text-white rounded text-[11px] font-semibold"
            >
              Save
            </button>
          </div>
        </form>
      )}

      {/* Memory List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-slate-500 space-y-1">
            <p className="text-[11px]">No memories found.</p>
            <button
              onClick={() => setIsAdding(true)}
              className="text-purple-400 hover:underline text-[10px]"
            >
              + Add first memory
            </button>
          </div>
        ) : (
          filtered.map((mem) => (
            <div
              key={mem.id}
              className="p-2 rounded bg-slate-950 border border-slate-800 hover:border-slate-700 transition-colors group space-y-1"
            >
              <div className="flex items-center justify-between text-[10px]">
                <span className="px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-300 font-mono capitalize">
                  {mem.category.replace("_", " ")}
                </span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => handleDelete(mem.id, e)}
                    title="Delete Memory"
                    className="p-0.5 text-slate-500 hover:text-rose-400 rounded"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
              <p className="text-slate-300 text-[11px] leading-snug break-words">
                {mem.content}
              </p>
              {mem.tags && mem.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-0.5">
                  {mem.tags.map((t) => (
                    <span
                      key={t}
                      className="text-[9px] px-1 rounded bg-slate-900 text-slate-500 font-mono"
                    >
                      #{t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Bottom Action Footer */}
      <div className="p-2 border-t border-slate-800/80 bg-slate-950">
        <button
          onClick={onOpenFullView}
          className="w-full py-1.5 px-2 rounded bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-[11px] font-semibold flex items-center justify-center gap-1.5 transition-colors"
        >
          <Brain className="w-3.5 h-3.5" />
          <span>Open Full Memory Center</span>
        </button>
      </div>
    </div>
  );
}
