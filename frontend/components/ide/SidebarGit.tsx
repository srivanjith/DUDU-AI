"use client";

import React, { useState, useEffect } from "react";
import {
  GitBranch,
  GitCommit,
  GitPullRequest,
  ArrowUp,
  ArrowDown,
  Plus,
  Minus,
  RefreshCw,
  FileCode,
  Check,
  History,
  FileDiff,
  Loader2,
} from "lucide-react";
import { GitStatusResult, GitFileStatus, GitCommitRecord } from "@/types";
import {
  fetchGitStatus,
  stageGitFile,
  unstageGitFile,
  commitGitChanges,
  fetchGitHistory,
  pushGitChanges,
  pullGitChanges,
} from "@/services/api";

interface SidebarGitProps {
  onOpenFileDiff: (filePath: string) => void;
}

export function SidebarGit({ onOpenFileDiff }: SidebarGitProps) {
  const [gitStatus, setGitStatus] = useState<GitStatusResult | null>(null);
  const [commitMessage, setCommitMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [isPushing, setIsPushing] = useState(false);
  const [isPulling, setIsPulling] = useState(false);
  const [commitHistory, setCommitHistory] = useState<GitCommitRecord[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadStatus = async () => {
    setIsLoading(true);
    try {
      const res = await fetchGitStatus();
      setGitStatus(res);
      if (showHistory) {
        loadHistory();
      }
    } catch (e) {
      console.error("Git status error", e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const h = await fetchGitHistory(15);
      setCommitHistory(h || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleStage = async (filePath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await stageGitFile(filePath);
      loadStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleUnstage = async (filePath: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await unstageGitFile(filePath);
      loadStatus();
    } catch (e) {
      console.error(e);
    }
  };

  const handleCommit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commitMessage.trim() || isCommitting) return;
    setIsCommitting(true);
    try {
      const res = await commitGitChanges(commitMessage.trim());
      setActionMessage(`Committed: ${res.commit}`);
      setCommitMessage("");
      setTimeout(() => setActionMessage(null), 3000);
      loadStatus();
    } catch (e: any) {
      alert(`Commit error: ${e.message || e}`);
    } finally {
      setIsCommitting(false);
    }
  };

  const handlePush = async () => {
    if (!confirm("Push current branch commits to origin?")) return;
    setIsPushing(true);
    try {
      await pushGitChanges();
      setActionMessage("Pushed to remote successfully!");
      setTimeout(() => setActionMessage(null), 3000);
      loadStatus();
    } catch (e: any) {
      alert(`Push error: ${e.message || e}`);
    } finally {
      setIsPushing(false);
    }
  };

  const handlePull = async () => {
    setIsPulling(true);
    try {
      await pullGitChanges();
      setActionMessage("Pulled latest changes from remote!");
      setTimeout(() => setActionMessage(null), 3000);
      loadStatus();
    } catch (e: any) {
      alert(`Pull error: ${e.message || e}`);
    } finally {
      setIsPulling(false);
    }
  };

  const files = gitStatus?.files || [];
  const stagedFiles = files.filter((f) => f.is_staged);
  const unstagedFiles = files.filter((f) => !f.is_staged);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 select-none overflow-hidden text-xs">
      {/* Header */}
      <div className="h-8 px-3 border-b border-slate-800/80 flex items-center justify-between font-semibold uppercase tracking-wider text-slate-400">
        <div className="flex items-center gap-1.5 text-white">
          <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
          <span className="truncate">{gitStatus?.branch || "main"}</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setShowHistory(!showHistory);
              if (!showHistory) loadHistory();
            }}
            title="Toggle Commit History"
            className={`p-1 hover:text-white rounded transition-colors ${showHistory ? "text-amber-400 bg-slate-800" : "text-slate-400 hover:bg-slate-800"}`}
          >
            <History className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={loadStatus}
            title="Refresh Git Status"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors text-slate-400"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-2 bg-emerald-500/10 border-b border-emerald-500/30 text-emerald-400 text-[11px] font-medium flex items-center gap-1.5">
          <Check className="w-3.5 h-3.5" />
          <span>{actionMessage}</span>
        </div>
      )}

      {/* Commit Input Form */}
      <form onSubmit={handleCommit} className="p-2.5 border-b border-slate-800/80 space-y-2">
        <textarea
          rows={2}
          placeholder="Commit message (Ctrl+Enter to commit)..."
          value={commitMessage}
          onChange={(e) => setCommitMessage(e.target.value)}
          onKeyDown={(e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
              handleCommit(e);
            }
          }}
          className="w-full bg-slate-950 border border-slate-800 rounded p-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 resize-none font-mono"
        />
        <div className="flex items-center gap-2">
          <button
            type="submit"
            disabled={!commitMessage.trim() || isCommitting || stagedFiles.length === 0}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white font-medium py-1.5 px-3 rounded flex items-center justify-center gap-1.5 transition-colors shadow-sm"
          >
            {isCommitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitCommit className="w-3.5 h-3.5" />}
            <span>Commit ({stagedFiles.length})</span>
          </button>
          <button
            type="button"
            onClick={handlePull}
            disabled={isPulling}
            title="Pull from origin"
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition-colors"
          >
            <ArrowDown className={`w-3.5 h-3.5 ${isPulling ? "animate-bounce" : ""}`} />
          </button>
          <button
            type="button"
            onClick={handlePush}
            disabled={isPushing}
            title="Push to origin"
            className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition-colors"
          >
            <ArrowUp className={`w-3.5 h-3.5 ${isPushing ? "animate-bounce" : ""}`} />
          </button>
        </div>
      </form>

      {/* Main Lists */}
      <div className="flex-1 overflow-y-auto p-2 space-y-4">
        {/* If History is toggled */}
        {showHistory ? (
          <div className="space-y-1">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-1">
              Recent Commits
            </span>
            <div className="divide-y divide-slate-800/60 mt-1">
              {commitHistory.map((c) => (
                <div key={c.hash} className="py-1.5 px-2 hover:bg-slate-800/40 rounded flex flex-col gap-0.5">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-mono text-amber-400 font-bold">{c.hash}</span>
                    <span className="text-slate-500 text-[10px]">{c.time_ago}</span>
                  </div>
                  <span className="text-slate-200 text-[11px] truncate">{c.subject}</span>
                  <span className="text-slate-500 text-[10px]">by {c.author}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Staged Changes Section */}
            <div>
              <div className="flex items-center justify-between px-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <span>Staged Changes ({stagedFiles.length})</span>
              </div>
              <div className="space-y-0.5 mt-1">
                {stagedFiles.length === 0 ? (
                  <div className="p-2 text-slate-600 text-[11px] italic">No staged changes</div>
                ) : (
                  stagedFiles.map((file) => (
                    <div
                      key={file.path}
                      onClick={() => onOpenFileDiff(file.path)}
                      className="group flex items-center justify-between px-2 py-1 rounded hover:bg-slate-800/50 cursor-pointer text-slate-200"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="text-emerald-400 font-mono text-[10px] font-bold">
                          {file.index_status}
                        </span>
                        <span className="truncate text-[12px]">{file.path}</span>
                      </div>
                      <button
                        onClick={(e) => handleUnstage(file.path, e)}
                        title="Unstage changes"
                        className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-white hover:bg-slate-700 rounded"
                      >
                        <Minus className="w-3 h-3 text-slate-400" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Changes Section */}
            <div>
              <div className="flex items-center justify-between px-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                <span>Changes ({unstagedFiles.length})</span>
              </div>
              <div className="space-y-0.5 mt-1">
                {unstagedFiles.length === 0 ? (
                  <div className="p-2 text-slate-600 text-[11px] italic">Working tree clean</div>
                ) : (
                  unstagedFiles.map((file) => (
                    <div
                      key={file.path}
                      onClick={() => onOpenFileDiff(file.path)}
                      className="group flex items-center justify-between px-2 py-1 rounded hover:bg-slate-800/50 cursor-pointer text-slate-200"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span className={`font-mono text-[10px] font-bold ${file.status === "untracked" ? "text-amber-400" : "text-sky-400"}`}>
                          {file.worktree_status || "U"}
                        </span>
                        <span className="truncate text-[12px]">{file.path}</span>
                      </div>
                      <button
                        onClick={(e) => handleStage(file.path, e)}
                        title="Stage changes"
                        className="opacity-0 group-hover:opacity-100 p-0.5 hover:text-white hover:bg-slate-700 rounded"
                      >
                        <Plus className="w-3 h-3 text-slate-400" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
