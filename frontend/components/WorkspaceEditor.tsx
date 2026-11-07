"use client";

import React, { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { Folder, File, Save, Check, RefreshCw, Code2 } from "lucide-react";
import { WorkspaceFile } from "@/types";
import { fetchWorkspaceFiles, fetchFileContent, saveWorkspaceFile } from "@/services/api";

export function WorkspaceEditor() {
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const loadFiles = async () => {
    try {
      const res = await fetchWorkspaceFiles();
      setFiles(res.items || []);
      if (!selectedFile && res.items?.length > 0) {
        const firstFile = res.items.find((f: any) => !f.is_dir);
        if (firstFile) {
          loadFile(firstFile.path);
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFile = async (path: string) => {
    setIsLoading(true);
    try {
      const res = await fetchFileContent(path);
      setSelectedFile(path);
      setContent(res.content || "");
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!selectedFile) return;
    setIsSaving(true);
    try {
      await saveWorkspaceFile(selectedFile, content);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  const getLanguage = (path: string) => {
    if (path.endsWith(".py")) return "python";
    if (path.endsWith(".ts") || path.endsWith(".tsx")) return "typescript";
    if (path.endsWith(".js") || path.endsWith(".jsx")) return "javascript";
    if (path.endsWith(".json")) return "json";
    if (path.endsWith(".html")) return "html";
    if (path.endsWith(".css")) return "css";
    return "plaintext";
  };

  return (
    <div className="flex-1 flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* File Tree Explorer */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/40 flex flex-col">
        <div className="p-3 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Code2 className="w-3.5 h-3.5 text-emerald-400" />
            Workspace Files
          </span>
          <button
            onClick={loadFiles}
            className="p-1 hover:text-white text-slate-400 rounded transition-colors"
            title="Refresh files"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {files.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-500">Workspace is empty.</div>
          ) : (
            files.map((f) => (
              <div
                key={f.path}
                onClick={() => !f.is_dir && loadFile(f.path)}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs cursor-pointer transition-colors ${
                  f.is_dir ? "text-slate-400 font-semibold" : selectedFile === f.path ? "bg-slate-800 text-white font-medium border border-slate-700" : "text-slate-300 hover:bg-slate-800/40"
                }`}
              >
                {f.is_dir ? <Folder className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" /> : <File className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />}
                <span className="truncate">{f.name}</span>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Monaco Editor Container */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Editor Toolbar */}
        <div className="h-12 border-b border-slate-800 px-4 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
            <File className="w-3.5 h-3.5 text-emerald-400" />
            <span>{selectedFile || "No file selected"}</span>
          </div>

          {selectedFile && (
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-all active:scale-95"
            >
              {savedSuccess ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
              <span>{savedSuccess ? "Saved!" : isSaving ? "Saving..." : "Save File"}</span>
            </button>
          )}
        </div>

        {/* Editor Instance */}
        <div className="flex-1 relative">
          {isLoading ? (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              Loading file content...
            </div>
          ) : selectedFile ? (
            <Editor
              height="100%"
              theme="vs-dark"
              language={getLanguage(selectedFile)}
              value={content}
              onChange={(val) => setContent(val || "")}
              options={{
                minimap: { enabled: false },
                fontSize: 13,
                fontFamily: "Fira Code, Menlo, monospace",
                scrollBeyondLastLine: false,
                wordWrap: "on",
                automaticLayout: true,
              }}
            />
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-500">
              Select a file from the left tree to inspect and edit code.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

