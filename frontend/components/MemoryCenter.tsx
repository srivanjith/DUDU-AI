"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Search,
  Filter,
  Plus,
  Trash2,
  Edit3,
  Calendar,
  Tag,
  FolderGit2,
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Check,
  X,
  Layers,
  Sliders,
  ShieldCheck,
  Star,
} from "lucide-react";
import { MemoryRecord } from "@/types";
import {
  fetchMemories,
  fetchMemoryCategories,
  fetchMemoryProjects,
  createMemory,
  updateMemory,
  deleteMemory,
  clearProjectMemories,
  clearAllMemories,
  searchMemories,
} from "@/services/api";

const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; border: string; bg: string; icon: any }
> = {
  project: {
    label: "Project Context",
    color: "text-purple-400",
    border: "border-purple-500/30",
    bg: "bg-purple-500/10",
    icon: FolderGit2,
  },
  task_experience: {
    label: "Task & Experience",
    color: "text-indigo-400",
    border: "border-indigo-500/30",
    bg: "bg-indigo-500/10",
    icon: Sparkles,
  },
  preference: {
    label: "User Preference",
    color: "text-cyan-400",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/10",
    icon: Sliders,
  },
  knowledge: {
    label: "Knowledge & Docs",
    color: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/10",
    icon: ShieldCheck,
  },
  conversation: {
    label: "Conversation Summary",
    color: "text-amber-400",
    border: "border-amber-500/30",
    bg: "bg-amber-500/10",
    icon: Brain,
  },
};

export function MemoryCenter() {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [categories, setCategories] = useState<Record<string, number>>({});
  const [totalCount, setTotalCount] = useState<number>(0);
  const [projects, setProjects] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedProject, setSelectedProject] = useState<string>("all");

  // Modals
  const [isAddOpen, setIsAddOpen] = useState<boolean>(false);
  const [editingMemory, setEditingMemory] = useState<MemoryRecord | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [confirmClearAll, setConfirmClearAll] = useState<boolean>(false);

  // Form State
  const [formContent, setFormContent] = useState<string>("");
  const [formCategory, setFormCategory] = useState<string>("project");
  const [formProject, setFormProject] = useState<string>("");
  const [formImportance, setFormImportance] = useState<number>(3);
  const [formTags, setFormTags] = useState<string>("");

  useEffect(() => {
    loadMemoryData();
  }, [selectedCategory, selectedProject]);

  const loadMemoryData = async () => {
    setLoading(true);
    try {
      const catData = await fetchMemoryCategories();
      setCategories(catData.categories || {});
      setTotalCount(catData.total || 0);

      const projData = await fetchMemoryProjects();
      setProjects(projData.projects || []);

      const catParam = selectedCategory === "all" ? undefined : selectedCategory;
      const projParam = selectedProject === "all" ? undefined : selectedProject;
      const mems = await fetchMemories(catParam, projParam, searchQuery || undefined, 100);
      setMemories(mems || []);
    } catch (err) {
      console.error("Failed to load memory data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadMemoryData();
      return;
    }
    setLoading(true);
    try {
      const catParam = selectedCategory === "all" ? undefined : selectedCategory;
      const projParam = selectedProject === "all" ? undefined : selectedProject;
      const searchRes = await searchMemories(searchQuery, catParam, projParam);
      setMemories(searchRes.results || []);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!formContent.trim()) return;
    try {
      const tagsArray = formTags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);
      await createMemory({
        content: formContent.trim(),
        category: formCategory,
        project_id: formProject.trim() || undefined,
        importance: formImportance,
        tags: tagsArray,
      });
      setIsAddOpen(false);
      resetForm();
      loadMemoryData();
    } catch (err) {
      console.error("Create error:", err);
    }
  };

  const handleUpdate = async () => {
    if (!editingMemory || !formContent.trim()) return;
    try {
      const tagsArray = formTags
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0);
      await updateMemory(editingMemory.id, {
        content: formContent.trim(),
        category: formCategory,
        project_id: formProject.trim() || undefined,
        importance: formImportance,
        tags: tagsArray,
      });
      setEditingMemory(null);
      resetForm();
      loadMemoryData();
    } catch (err) {
      console.error("Update error:", err);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      setConfirmDeleteId(null);
      loadMemoryData();
    } catch (err) {
      console.error("Delete error:", err);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllMemories();
      setConfirmClearAll(false);
      loadMemoryData();
    } catch (err) {
      console.error("Clear all error:", err);
    }
  };

  const openEdit = (mem: MemoryRecord) => {
    setEditingMemory(mem);
    setFormContent(mem.content);
    setFormCategory(mem.category);
    setFormProject(mem.project_id || "");
    setFormImportance(mem.importance || 3);
    setFormTags((mem.tags || []).join(", "));
  };

  const resetForm = () => {
    setFormContent("");
    setFormCategory("project");
    setFormProject("");
    setFormImportance(3);
    setFormTags("");
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 overflow-hidden text-slate-100">
      {/* Top Header */}
      <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/60 backdrop-blur flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2">
              Memory Center
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                Phase 7 Persistent Context
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Long-term project memory, user preferences, and verified technical outcomes.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              resetForm();
              setIsAddOpen(true);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/20 transition-all active:scale-[0.98]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Memory</span>
          </button>

          <button
            onClick={() => setConfirmClearAll(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-950/40 hover:text-rose-400 text-slate-400 text-xs font-semibold border border-slate-700/60 transition-all"
            title="Clear all memories across DODO"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear All</span>
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* Category Breakdown Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          {Object.entries(CATEGORY_CONFIG).map(([catKey, cfg]) => {
            const Icon = cfg.icon;
            const count = categories[catKey] || 0;
            const isSelected = selectedCategory === catKey;

            return (
              <button
                key={catKey}
                onClick={() => setSelectedCategory(isSelected ? "all" : catKey)}
                className={`p-3.5 rounded-xl border text-left transition-all relative overflow-hidden ${
                  isSelected
                    ? `${cfg.bg} ${cfg.border} ring-1 ring-purple-500`
                    : "bg-slate-900/60 border-slate-800/80 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className={`p-1.5 rounded-lg ${cfg.bg} ${cfg.color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <span className="text-xl font-extrabold text-white">{count}</span>
                </div>
                <div className="text-xs font-semibold text-slate-200">{cfg.label}</div>
                <div className="text-[10px] text-slate-400 mt-0.5">
                  {((count / Math.max(1, totalCount)) * 100).toFixed(0)}% of total
                </div>
              </button>
            );
          })}
        </div>

        {/* Action & Filter Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-3 p-3 bg-slate-900/80 border border-slate-800 rounded-xl">
          <form onSubmit={handleSearch} className="flex-1 flex items-center gap-2 w-full">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                placeholder="Search memories by keyword, technology, error fix, or tag..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300"
            >
              Search
            </button>
          </form>

          <div className="flex items-center gap-2 w-full md:w-auto">
            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-purple-500"
            >
              <option value="all">All Categories</option>
              <option value="project">Project Context</option>
              <option value="task_experience">Task & Experience</option>
              <option value="preference">User Preference</option>
              <option value="knowledge">Knowledge</option>
              <option value="conversation">Conversation</option>
            </select>

            {/* Project Filter */}
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-slate-950 border border-slate-800 text-xs text-slate-300 rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-purple-500"
            >
              <option value="all">All Projects</option>
              {(projects || []).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>

            <button
              onClick={loadMemoryData}
              className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
              title="Refresh memories"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Memory Items List */}
        <div className="space-y-3">
          {loading ? (
            <div className="text-center py-12 text-slate-500 text-xs flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-purple-400" />
              <span>Loading persistent memories from database store...</span>
            </div>
          ) : (memories || []).length === 0 ? (
            <div className="text-center py-16 border border-dashed border-slate-800 rounded-2xl p-8 bg-slate-900/20">
              <Brain className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-slate-300">No Memories Found</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                No memories match the current filters. DODO automatically captures memories during
                conversations, or you can add one manually.
              </p>
            </div>
          ) : (
            (memories || []).map((mem) => {
              const cfg = CATEGORY_CONFIG[mem.category] || CATEGORY_CONFIG.conversation;
              const Icon = cfg.icon;

              return (
                <div
                  key={mem.id}
                  className="bg-slate-900/70 border border-slate-800/80 hover:border-slate-700/90 rounded-xl p-4 transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-2">
                        {/* Category Badge */}
                        <span
                          className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color} ${cfg.border} border`}
                        >
                          <Icon className="w-3 h-3" />
                          {cfg.label}
                        </span>

                        {/* Project Badge */}
                        {mem.project_id && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/60">
                            <FolderGit2 className="w-3 h-3 text-slate-400" />
                            {mem.project_id}
                          </span>
                        )}

                        {/* Importance Stars */}
                        <div className="flex items-center gap-0.5 text-amber-400 ml-1">
                          {[1, 2, 3, 4, 5].map((star) => (
                            <Star
                              key={star}
                              className={`w-3 h-3 ${
                                star <= (mem.importance || 3)
                                  ? "fill-amber-400 text-amber-400"
                                  : "text-slate-700"
                              }`}
                            />
                          ))}
                        </div>

                        {/* Relevance Score (if searched) */}
                        {mem.relevance_score !== undefined && (
                          <span className="text-[10px] text-emerald-400 font-mono ml-auto">
                            Relevance: {(mem.relevance_score * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>

                      {/* Content */}
                      <p className="text-xs font-normal text-slate-200 leading-relaxed whitespace-pre-wrap">
                        {mem.content}
                      </p>

                      {/* Match Reasons (if searched) */}
                      {mem.match_reasons && mem.match_reasons.length > 0 && (
                        <div className="mt-2 text-[10px] text-slate-400 font-mono bg-slate-950/60 p-1.5 rounded border border-slate-800">
                          {mem.match_reasons.join(" • ")}
                        </div>
                      )}

                      {/* Tags & Timestamp */}
                      <div className="flex flex-wrap items-center gap-2 mt-3 pt-2 border-t border-slate-800/60 text-[10px] text-slate-500">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {mem.created_at ? new Date(mem.created_at).toLocaleString() : "Recent"}
                        </span>

                        {mem.tags &&
                          mem.tags.map((t) => (
                            <span
                              key={t}
                              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 bg-slate-800/60 rounded text-slate-400 border border-slate-800"
                            >
                              <Tag className="w-2.5 h-2.5" />
                              {t}
                            </span>
                          ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEdit(mem)}
                        className="p-1.5 text-slate-400 hover:text-slate-200 rounded-lg hover:bg-slate-800 transition-colors"
                        title="Edit Memory"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => setConfirmDeleteId(mem.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800 transition-colors"
                        title="Delete Memory"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Add / Edit Modal */}
      {(isAddOpen || editingMemory) && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <Brain className="w-4 h-4 text-purple-400" />
                {editingMemory ? "Edit Memory Item" : "Create New Memory Item"}
              </h2>
              <button
                onClick={() => {
                  setIsAddOpen(false);
                  setEditingMemory(null);
                }}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                  Memory Content <span className="text-rose-400">*</span>
                </label>
                <textarea
                  rows={4}
                  placeholder="Record project architecture decisions, tech stacks, verified bug fixes, or developer preferences..."
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Category
                  </label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  >
                    <option value="project">Project Context</option>
                    <option value="task_experience">Task & Experience</option>
                    <option value="preference">User Preference</option>
                    <option value="knowledge">Knowledge</option>
                    <option value="conversation">Conversation</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Project Identifier (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. demo_task_app_phase4"
                    value={formProject}
                    onChange={(e) => setFormProject(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Importance (1–5)
                  </label>
                  <div className="flex items-center gap-2 pt-1">
                    {[1, 2, 3, 4, 5].map((lvl) => (
                      <button
                        key={lvl}
                        type="button"
                        onClick={() => setFormImportance(lvl)}
                        className={`w-7 h-7 rounded-lg text-xs font-bold transition-all ${
                          formImportance === lvl
                            ? "bg-purple-600 text-white"
                            : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                        }`}
                      >
                        {lvl}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-slate-300 block mb-1">
                    Tags (Comma separated)
                  </label>
                  <input
                    type="text"
                    placeholder="react, fastapi, auth, fix"
                    value={formTags}
                    onChange={(e) => setFormTags(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
              <button
                onClick={() => {
                  setIsAddOpen(false);
                  setEditingMemory(null);
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={editingMemory ? handleUpdate : handleCreate}
                disabled={!formContent.trim()}
                className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-purple-600/20"
              >
                {editingMemory ? "Save Changes" : "Create Memory"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      {confirmDeleteId && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-sm shadow-2xl p-5 space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <h3 className="text-sm font-bold text-white">Delete Memory</h3>
            </div>
            <p className="text-xs text-slate-400">
              Are you sure you want to delete this memory? This action is permanent and cannot be
              undone.
            </p>
            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(confirmDeleteId)}
                className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clear All Confirmation Dialog */}
      {confirmClearAll && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-rose-900/60 rounded-2xl w-full max-w-md shadow-2xl p-5 space-y-4">
            <div className="flex items-center gap-3 text-rose-400">
              <AlertTriangle className="w-6 h-6 flex-shrink-0 text-rose-500" />
              <h3 className="text-sm font-bold text-white">Danger: Clear All Memories</h3>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">
              This will irreversibly delete <strong>all {totalCount} persistent memories</strong>{" "}
              across all projects, conversations, and preferences stored in DODO.
            </p>
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-[11px] text-rose-300">
              ⚠️ Application context will be reset to default clean state.
            </div>
            <div className="pt-2 flex items-center justify-end gap-2">
              <button
                onClick={() => setConfirmClearAll(false)}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleClearAll}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/30"
              >
                Confirm & Wipe Memories
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

