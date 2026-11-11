"use client";

import React from "react";
import Editor, { DiffEditor } from "@monaco-editor/react";
import {
  FileCode,
  File,
  X,
  Split,
  Save,
  Check,
  History,
  Sparkles,
  Command,
  FolderOpen,
  FolderPlus,
} from "lucide-react";

export interface FileTab {
  path: string;
  originalContent: string;
  currentContent: string;
}

interface EditorAreaProps {
  openTabs: FileTab[];
  activeTabPath: string | null;
  onSelectTab: (path: string) => void;
  onCloseTab: (path: string, e: React.MouseEvent) => void;
  onContentChange: (newContent: string) => void;
  onSave: () => void;
  showDiff: boolean;
  onToggleDiff: () => void;
  onTriggerAgentTask?: (prompt: string) => void;
  onOpenProject?: () => void;
  onNewProject?: () => void;
}

export function EditorArea({
  openTabs,
  activeTabPath,
  onSelectTab,
  onCloseTab,
  onContentChange,
  onSave,
  showDiff,
  onToggleDiff,
  onTriggerAgentTask,
  onOpenProject,
  onNewProject,
}: EditorAreaProps) {
  const activeTab = openTabs.find((t) => t.path === activeTabPath);
  const isDirty = activeTab ? activeTab.originalContent !== activeTab.currentContent : false;

  const getLanguage = (path: string) => {
    const lower = path.toLowerCase();
    if (lower.endsWith(".py")) return "python";
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return "typescript";
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return "javascript";
    if (lower.endsWith(".json")) return "json";
    if (lower.endsWith(".html")) return "html";
    if (lower.endsWith(".css")) return "css";
    if (lower.endsWith(".md")) return "markdown";
    if (lower.endsWith(".sql")) return "sql";
    if (lower.endsWith(".sh") || lower.endsWith(".ps1")) return "shell";
    if (lower.endsWith(".c") || lower.endsWith(".h") || lower.endsWith(".cpp")) return "cpp";
    if (lower.endsWith(".java")) return "java";
    return "plaintext";
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* Tab Bar */}
      <div className="h-9 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-2 overflow-x-auto text-xs">
        <div className="flex items-center gap-0.5 overflow-x-auto max-w-[calc(100%-140px)]">
          {(openTabs || []).map((tab) => {
            const isActive = tab.path === activeTabPath;
            const tabDirty = tab.originalContent !== tab.currentContent;
            const fileName = tab.path.split("/").pop() || tab.path;

            return (
              <div
                key={tab.path}
                onClick={() => onSelectTab(tab.path)}
                className={`group flex items-center gap-1.5 px-3 py-1.5 border-r border-slate-800/80 cursor-pointer transition-colors max-w-xs ${
                  isActive
                    ? "bg-slate-950 text-white border-t-2 border-t-amber-400 font-medium"
                    : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <FileCode className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? "text-amber-400" : "text-slate-500"}`} />
                <span className="truncate text-[12px]">{fileName}</span>

                {/* Dirty Indicator / Close Button */}
                <div className="w-4 h-4 flex items-center justify-center">
                  {tabDirty ? (
                    <span
                      onClick={(e) => onCloseTab(tab.path, e)}
                      title="Unsaved changes. Click to close."
                      className="w-2 h-2 rounded-full bg-amber-400 group-hover:hidden"
                    />
                  ) : null}
                  <button
                    onClick={(e) => onCloseTab(tab.path, e)}
                    className={`${tabDirty ? "hidden group-hover:flex" : "flex"} p-0.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white`}
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Tab Right Controls (Diff Toggle, Language Badge, Save Button) */}
        {activeTab && (
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              {getLanguage(activeTab.path)}
            </span>

            <button
              onClick={onToggleDiff}
              title={showDiff ? "Show standard editor" : "Show diff with saved disk version"}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[11px] border transition-colors ${
                showDiff
                  ? "bg-indigo-600/30 text-indigo-300 border-indigo-500/50 font-semibold"
                  : "bg-slate-800 text-slate-300 border-slate-700 hover:text-white"
              }`}
            >
              <Split className="w-3 h-3" />
              <span>Diff</span>
            </button>

            <button
              onClick={onSave}
              disabled={!isDirty}
              title="Save (Ctrl+S)"
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] border transition-colors ${
                isDirty
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30 font-semibold"
                  : "bg-slate-800/40 text-slate-500 border-slate-800 cursor-default"
              }`}
            >
              <Save className="w-3 h-3" />
              <span>Save</span>
            </button>
          </div>
        )}
      </div>

      {/* Breadcrumb Path */}
      {activeTab && (
        <div className="h-6 bg-slate-950/70 border-b border-slate-800/60 px-3 flex items-center text-[11px] text-slate-400 font-mono">
          <span>workspace</span>
          <span className="mx-1 text-slate-600">/</span>
          <span className="text-slate-200">{activeTab.path}</span>
        </div>
      )}

      {/* Editor Body */}
      <div className="flex-1 relative overflow-hidden bg-slate-950">
        {!activeTab ? (
          /* Empty Workspace / Welcome Splash */
          <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4 p-8">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-amber-500/20 to-slate-800 border border-amber-500/30 flex items-center justify-center shadow-lg">
              <span className="text-3xl">🦅</span>
            </div>
            <div className="text-center space-y-1">
              <h2 className="text-xl font-bold text-white tracking-tight">DODO IDE</h2>
              <p className="text-xs text-slate-400 font-medium">Your AI. Your Machine. Your Rules.</p>
            </div>

            {/* Quick Project Actions */}
            <div className="flex items-center gap-3 pt-1">
              {onOpenProject && (
                <button
                  onClick={onOpenProject}
                  className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold transition-colors shadow-sm"
                >
                  <FolderOpen className="w-3.5 h-3.5 text-amber-400" />
                  <span>Open Project...</span>
                </button>
              )}
              {onNewProject && (
                <button
                  onClick={onNewProject}
                  className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 border border-emerald-800/80 text-xs font-semibold transition-colors shadow-sm"
                >
                  <FolderPlus className="w-3.5 h-3.5 text-emerald-400" />
                  <span>New Project...</span>
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs text-slate-400 max-w-sm mt-4">
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 bg-slate-950 border border-slate-700 rounded font-mono text-[10px] text-amber-400">Ctrl+P</kbd>
                <span>Quick Open File</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 bg-slate-950 border border-slate-700 rounded font-mono text-[10px] text-amber-400">Ctrl+Shift+P</kbd>
                <span>Command Palette</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 bg-slate-950 border border-slate-700 rounded font-mono text-[10px] text-amber-400">Ctrl+`</kbd>
                <span>Toggle Terminal</span>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2">
                <kbd className="px-1.5 py-0.5 bg-slate-950 border border-slate-700 rounded font-mono text-[10px] text-amber-400">Ctrl+Shift+A</kbd>
                <span>Focus AI Agent</span>
              </div>
            </div>
          </div>
        ) : showDiff ? (
          <DiffEditor
            height="100%"
            theme="vs-dark"
            language={getLanguage(activeTab.path)}
            original={activeTab.originalContent}
            modified={activeTab.currentContent}
            options={{
              readOnly: true,
              renderSideBySide: true,
              minimap: { enabled: false },
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
              scrollBeyondLastLine: false,
              automaticLayout: true,
            }}
          />
        ) : (
          <Editor
            height="100%"
            theme="vs-dark"
            language={getLanguage(activeTab.path)}
            value={activeTab.currentContent}
            onChange={(val) => onContentChange(val || "")}
            options={{
              fontSize: 13,
              fontFamily: "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
              minimap: { enabled: true },
              lineNumbers: "on",
              wordWrap: "on",
              tabSize: 4,
              automaticLayout: true,
              scrollBeyondLastLine: false,
              renderWhitespace: "selection",
              bracketPairColorization: { enabled: true },
              cursorBlinking: "smooth",
              smoothScrolling: true,
            }}
          />
        )}
      </div>
    </div>
  );
}

