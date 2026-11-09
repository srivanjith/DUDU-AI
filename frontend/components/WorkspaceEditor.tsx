"use client";

import React, { useState, useEffect } from "react";
import Editor, { DiffEditor } from "@monaco-editor/react";
import {
  Folder,
  File,
  Save,
  Check,
  RefreshCw,
  Code2,
  X,
  Search,
  GitBranch,
  Split,
  History,
  Layers,
  FileCode,
  ShieldCheck,
} from "lucide-react";
import { WorkspaceFile, ProjectScan } from "@/types";
import {
  fetchWorkspaceFiles,
  fetchFileContent,
  saveWorkspaceFile,
  fetchWorkspaceStatus,
  fetchCheckpoints,
  rollbackCheckpoint,
} from "@/services/api";

interface FileTab {
  path: string;
  originalContent: string;
  currentContent: string;
}

export function WorkspaceEditor() {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [searchFilter, setSearchFilter] = useState("");
  const [openTabs, setOpenTabs] = useState<FileTab[]>([]);
  const [activeTabPath, setActiveTabPath] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [showDiff, setShowDiff] = useState(false);
  const [projectScan, setProjectScan] = useState<ProjectScan | null>(null);
  const [workspacePath, setWorkspacePath] = useState<string>("");
  const [checkpoints, setCheckpoints] = useState<any[]>([]);
  const [showCheckpoints, setShowCheckpoints] = useState(false);

  const activeTab = openTabs.find((t) => t.path === activeTabPath);

  const loadFiles = async () => {
    try {
      const res = await fetchWorkspaceFiles();
      setFiles(res.items || []);

      const statusRes = await fetchWorkspaceStatus();
      if (statusRes?.scan) {
        setProjectScan(statusRes.scan);
        setWorkspacePath(statusRes.authorized_workspace || "");
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const openFile = async (path: string) => {
    // If already open, switch tab
    const existing = openTabs.find((t) => t.path === path);
    if (existing) {
      setActiveTabPath(path);
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetchFileContent(path);
      const text = res.content || "";
      const newTab: FileTab = {
        path,
        originalContent: text,
        currentContent: text,
      };
      setOpenTabs((prev) => [...prev, newTab]);
      setActiveTabPath(path);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const closeTab = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const remaining = openTabs.filter((t) => t.path !== path);
    setOpenTabs(remaining);
    if (activeTabPath === path) {
      setActiveTabPath(remaining.length > 0 ? remaining[remaining.length - 1].path : null);
    }
  };

  const updateActiveContent = (newVal: string) => {
    if (!activeTabPath) return;
    setOpenTabs((prev) =>
      prev.map((t) => (t.path === activeTabPath ? { ...t, currentContent: newVal } : t))
    );
  };

  const handleSave = async () => {
    if (!activeTab) return;
    setIsSaving(true);
    try {
      await saveWorkspaceFile(activeTab.path, activeTab.currentContent);
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === activeTab.path ? { ...t, originalContent: activeTab.currentContent } : t
        )
      );
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
      loadFiles();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  const loadCheckpointsList = async () => {
    try {
      const list = await fetchCheckpoints(workspacePath);
      setCheckpoints(list || []);
      setShowCheckpoints(true);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRollback = async (cpId: string) => {
    if (!confirm("Are you sure you want to rollback to this checkpoint snapshot?")) return;
    try {
      await rollbackCheckpoint(cpId, workspacePath);
      alert("Checkpoint rollback completed successfully.");
      setShowCheckpoints(false);
      loadFiles();
      if (activeTabPath) {
        openFile(activeTabPath);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getLanguage = (path: string) => {
    if (path.endsWith(".py")) return "python";
    if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
    if (path.endsWith(".js") || path.endsWith(".jsx")) return "javascript";
    if (path.endsWith(".json")) return "json";
    if (path.endsWith(".html")) return "html";
    if (path.endsWith(".css")) return "css";
    if (path.endsWith(".md")) return "markdown";
    if (path.endsWith(".sql")) return "sql";
    if (path.endsWith(".sh") || path.endsWith(".ps1")) return "shell";
    return "plaintext";
  };

  const filteredFiles = files.filter((f) =>
    f.name.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Workspace Project Summary Bar */}
      <div className="h-11 border-b border-slate-800 bg-slate-900/70 px-4 flex items-center justify-between text-xs backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="font-bold text-white flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            {projectScan?.project_name || "Authorized Workspace"}
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400 font-mono text-[11px] truncate max-w-sm">
            {workspacePath || "Default Local Workspace"}
          </span>

          {projectScan?.primary_language && projectScan.primary_language !== "Unknown" && (
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-mono border border-emerald-500/20">
              {projectScan.primary_language}
            </span>
          )}

          {projectScan?.frameworks?.map((fw) => (
            <span key={fw} className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300 text-[10px] font-mono border border-indigo-500/20">
              {fw}
            </span>
          ))}

          {projectScan?.git_branch && (
            <span className="text-slate-400 text-[11px] flex items-center gap-1">
              <GitBranch className="w-3 h-3 text-slate-500" />
              {projectScan.git_branch}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadCheckpointsList}
            className="flex items-center gap-1 px-2.5 py-1 text-slate-400 hover:text-white rounded-lg border border-slate-800 hover:bg-slate-800/60 text-xs transition-colors"
          >
            <History className="w-3.5 h-3.5" />
            <span>Checkpoints</span>
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* File Tree Explorer */}
        <div className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Code2 className="w-3.5 h-3.5 text-emerald-400" />
              Files ({files.length})
            </span>
            <button
              onClick={loadFiles}
              className="p-1 hover:text-white text-slate-400 rounded transition-colors"
              title="Refresh files"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Search Filter */}
          <div className="p-2 border-b border-slate-800/60">
            <div className="relative">
              <Search className="w-3 h-3 text-slate-500 absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Filter files..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-7 pr-2 py-1 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-slate-700"
              />
            </div>
          </div>

          {/* File List */}
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {filteredFiles.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">No files found.</div>
            ) : (
              filteredFiles.map((f) => (
                <div
                  key={f.path}
                  onClick={() => !f.is_dir && openFile(f.path)}
                  className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                    f.is_dir
                      ? "text-slate-400 font-semibold cursor-default"
                      : activeTabPath === f.path
                      ? "bg-slate-800 text-white font-medium border border-slate-700 shadow-sm"
                      : "text-slate-300 hover:bg-slate-800/50"
                  }`}
                >
                  {f.is_dir ? (
                    <Folder className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                  ) : (
                    <File className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                  )}
                  <span className="truncate">{f.name}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Monaco Editor & Tab Container */}
        <div className="flex-1 flex flex-col overflow-hidden bg-slate-950">
          {/* File Tabs Bar */}
          <div className="h-10 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between px-2 overflow-x-auto">
            <div className="flex items-center gap-1 overflow-x-auto">
              {openTabs.map((tab) => {
                const isActive = tab.path === activeTabPath;
                const isModified = tab.currentContent !== tab.originalContent;
                const fileName = tab.path.split("/").pop();

                return (
                  <div
                    key={tab.path}
                    onClick={() => setActiveTabPath(tab.path)}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-t-lg text-xs cursor-pointer border-t-2 transition-all ${
                      isActive
                        ? "bg-slate-950 border-emerald-400 text-white font-medium"
                        : "bg-slate-900/50 border-transparent text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    <FileCode className="w-3 h-3 text-slate-400" />
                    <span>{fileName}</span>
                    {isModified && <span className="w-1.5 h-1.5 rounded-full bg-amber-400" title="Unsaved changes" />}
                    <button
                      onClick={(e) => closeTab(tab.path, e)}
                      className="p-0.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </div>
                );
              })}
            </div>

            {/* Editor Action Buttons */}
            {activeTab && (
              <div className="flex items-center gap-2 flex-shrink-0 pl-2">
                <button
                  onClick={() => setShowDiff(!showDiff)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs transition-colors border ${
                    showDiff
                      ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                      : "text-slate-400 hover:text-white border-slate-800 hover:bg-slate-800/60"
                  }`}
                  title="Toggle side-by-side Diff Preview against disk"
                >
                  <Split className="w-3.5 h-3.5" />
                  <span>{showDiff ? "Close Diff" : "Preview Diff"}</span>
                </button>

                <button
                  onClick={handleSave}
                  disabled={isSaving || activeTab.currentContent === activeTab.originalContent}
                  className="flex items-center gap-1.5 px-3 py-1 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-all active:scale-95"
                >
                  {savedSuccess ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                  <span>{savedSuccess ? "Saved!" : isSaving ? "Saving..." : "Save File"}</span>
                </button>
              </div>
            )}
          </div>

          {/* Monaco Editor / Diff Editor Container */}
          <div className="flex-1 relative">
            {isLoading ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-500">
                Loading file content...
              </div>
            ) : activeTab ? (
              showDiff ? (
                <DiffEditor
                  height="100%"
                  theme="vs-dark"
                  original={activeTab.originalContent}
                  modified={activeTab.currentContent}
                  language={getLanguage(activeTab.path)}
                  options={{
                    renderSideBySide: true,
                    fontSize: 13,
                    fontFamily: "Fira Code, Menlo, monospace",
                    automaticLayout: true,
                  }}
                />
              ) : (
                <Editor
                  height="100%"
                  theme="vs-dark"
                  language={getLanguage(activeTab.path)}
                  value={activeTab.currentContent}
                  onChange={(val) => updateActiveContent(val || "")}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: "Fira Code, Menlo, monospace",
                    scrollBeyondLastLine: false,
                    wordWrap: "on",
                    automaticLayout: true,
                  }}
                />
              )
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-xs text-slate-500 space-y-2">
                <FileCode className="w-8 h-8 opacity-40" />
                <span>Select a file from the explorer to view and edit code with Monaco Editor.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Checkpoints Modal */}
      {showCheckpoints && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <History className="w-4 h-4 text-emerald-400" />
                <span>Workspace Checkpoints & Rollback History</span>
              </h3>
              <button
                onClick={() => setShowCheckpoints(false)}
                className="p-1 hover:text-white text-slate-400 rounded"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              DODO creates automated snapshot checkpoints before applying approved code changes. You can rollback to any previous snapshot safely.
            </p>

            <div className="max-h-72 overflow-y-auto space-y-2 font-mono text-xs">
              {checkpoints.length === 0 ? (
                <div className="text-center py-8 text-slate-500">No checkpoints recorded yet.</div>
              ) : (
                checkpoints.map((cp) => (
                  <div
                    key={cp.id}
                    className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-white font-semibold text-xs">{cp.title}</div>
                      <div className="text-[10px] text-slate-500">
                        {new Date(cp.created_at).toLocaleString()} • {cp.file_count || 1} file(s)
                      </div>
                    </div>
                    <button
                      onClick={() => handleRollback(cp.id)}
                      className="px-3 py-1 bg-amber-600/20 hover:bg-amber-600 text-amber-300 hover:text-white rounded-lg text-xs font-semibold transition-all border border-amber-500/30"
                    >
                      Rollback
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
