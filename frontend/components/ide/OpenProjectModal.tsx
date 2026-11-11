"use client";

import React, { useState, useEffect } from "react";
import {
  FolderOpen,
  Folder,
  History,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  FolderGit2,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { fetchProjects, fetchQuickPaths, openProject, ProjectRecord } from "@/services/api";

interface OpenProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectOpened: (projectData: {
    project: any;
    scan: any;
    files: any[];
    workspace_path: string;
  }) => void;
}

export function OpenProjectModal({ isOpen, onClose, onProjectOpened }: OpenProjectModalProps) {
  const [folderPath, setFolderPath] = useState("");
  const [recentProjects, setRecentProjects] = useState<ProjectRecord[]>([]);
  const [quickPaths, setQuickPaths] = useState<Array<{ label: string; path: string; is_default: boolean }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingRecents, setIsLoadingRecents] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    setErrorMsg(null);
    loadRecentAndQuickPaths();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const loadRecentAndQuickPaths = async () => {
    setIsLoadingRecents(true);
    try {
      const [projs, qPaths] = await Promise.all([
        fetchProjects().catch(() => []),
        fetchQuickPaths().catch(() => []),
      ]);
      setRecentProjects(projs);
      setQuickPaths(qPaths);
      if (qPaths.length > 0 && !folderPath) {
        setFolderPath(qPaths[0].path);
      }
    } catch (e) {
      console.error("Error loading project data", e);
    } finally {
      setIsLoadingRecents(false);
    }
  };

  const handleOpen = async (pathToOpen?: string) => {
    const target = (pathToOpen || folderPath).trim();
    if (!target) {
      setErrorMsg("Please enter or select a valid project folder path.");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const data = await openProject(target);
      onProjectOpened(data);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || `Failed to open folder: ${target}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNativeFolderPick = async () => {
    try {
      if ("showDirectoryPicker" in window) {
        const handle = await (window as any).showDirectoryPicker();
        if (handle && handle.name) {
          // In browser sandbox, showDirectoryPicker gives the folder name
          // If the folder is inside current workspace or we have default, let user confirm path
          const defaultBase = quickPaths[0]?.path || "D:\\DODO\\workspace";
          const suggested = `${defaultBase}\\${handle.name}`;
          setFolderPath(suggested);
        }
      }
    } catch (err: any) {
      // User cancelled picker
      if (err.name !== "AbortError") {
        console.warn("Folder picker warning:", err);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-150"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between select-none">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <FolderOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Open Project
              </h2>
              <p className="text-xs text-slate-400">
                Select an existing project directory on Windows to load into DODO IDE
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

        {/* Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs font-sans">
          {/* Error Alert */}
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-semibold block text-xs">Cannot Open Project</span>
                <span className="text-[11px] leading-relaxed block">{errorMsg}</span>
              </div>
            </div>
          )}

          {/* Folder Path Input */}
          <div className="space-y-2">
            <label className="text-slate-300 font-semibold text-xs block">
              Project Folder Path (Windows Absolute Path)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                autoFocus
                placeholder="e.g. D:\DODO\workspace\my-project"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleOpen();
                  }
                }}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/60 font-mono"
              />
              {typeof window !== "undefined" && "showDirectoryPicker" in window && (
                <button
                  type="button"
                  onClick={handleNativeFolderPick}
                  title="Browse local folder with Windows File Picker"
                  className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors whitespace-nowrap"
                >
                  <Folder className="w-3.5 h-3.5 text-amber-400" />
                  <span>Browse...</span>
                </button>
              )}
            </div>
          </div>

          {/* Quick Paths */}
          {(quickPaths || []).length > 0 && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                Quick Locations
              </span>
              <div className="flex flex-wrap gap-2">
                {(quickPaths || []).map((qp) => (
                  <button
                    key={qp.path}
                    type="button"
                    onClick={() => setFolderPath(qp.path)}
                    className={`px-2.5 py-1.5 rounded-lg border text-[11px] font-mono flex items-center gap-1.5 transition-colors ${
                      folderPath === qp.path
                        ? "bg-amber-500/10 border-amber-500/40 text-amber-300"
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800"
                    }`}
                  >
                    <FolderGit2 className="w-3 h-3 text-slate-500" />
                    <span>{qp.label}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Recently Opened Projects */}
          <div className="space-y-2 pt-1 border-t border-slate-800/80">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-indigo-400" />
                <span>Recently Opened Projects</span>
              </span>
              <span className="text-[10px] text-slate-500 font-mono">
                {(recentProjects || []).length} registered
              </span>
            </div>

            {isLoadingRecents ? (
              <div className="p-4 text-center text-slate-500 flex items-center justify-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                <span>Loading projects...</span>
              </div>
            ) : (recentProjects || []).length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/60 text-center text-slate-500">
                No previous projects recorded.
              </div>
            ) : (
              <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1">
                {(recentProjects || []).map((proj) => (
                  <div
                    key={proj.id}
                    onClick={() => {
                      setFolderPath(proj.path);
                      handleOpen(proj.path);
                    }}
                    className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-amber-500/40 hover:bg-slate-900 cursor-pointer transition-all flex items-center justify-between group"
                  >
                    <div className="space-y-0.5 truncate max-w-[420px]">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-white text-xs group-hover:text-amber-300 transition-colors truncate">
                          {proj.name}
                        </span>
                        {proj.scan_summary?.primary_language && (
                          <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                            {proj.scan_summary.primary_language}
                          </span>
                        )}
                        {!proj.exists_on_disk && (
                          <span className="text-[9px] px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            Missing on disk
                          </span>
                        )}
                      </div>
                      <span className="text-[11px] text-slate-500 font-mono truncate block" title={proj.path}>
                        {proj.path}
                      </span>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <span className="text-[11px] text-amber-400 font-semibold flex items-center gap-1">
                        Open <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs select-none">
          <span className="text-slate-500 font-mono text-[11px]">
            Target: {folderPath ? folderPath.slice(0, 45) + (folderPath.length > 45 ? "..." : "") : "None selected"}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => handleOpen()}
              disabled={isLoading || !folderPath.trim()}
              className="px-5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-amber-500/20 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Opening...</span>
                </>
              ) : (
                <>
                  <FolderOpen className="w-3.5 h-3.5" />
                  <span>Open in DODO</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

