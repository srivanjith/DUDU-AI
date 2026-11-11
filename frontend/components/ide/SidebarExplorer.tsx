"use client";

import React, { useState } from "react";
import {
  Folder,
  FolderOpen,
  File,
  FileCode,
  FileText,
  FileJson,
  FileSpreadsheet,
  Plus,
  FolderPlus,
  RefreshCw,
  Search,
  MoreVertical,
  Trash2,
  Edit2,
  ChevronRight,
  ChevronDown,
} from "lucide-react";
import { WorkspaceFile } from "@/types";

interface SidebarExplorerProps {
  files: WorkspaceFile[];
  onOpenFile: (path: string) => void;
  activeFilePath: string | null;
  onRefresh: () => void;
  onCreateFile: (path: string) => void;
  onCreateFolder: (path: string) => void;
  onRenameFile: (oldPath: string, newPath: string) => void;
  onDeleteFile: (path: string) => void;
  projectName: string;
}

export function SidebarExplorer({
  files,
  onOpenFile,
  activeFilePath,
  onRefresh,
  onCreateFile,
  onCreateFolder,
  onRenameFile,
  onDeleteFile,
  projectName,
}: SidebarExplorerProps) {
  const [filter, setFilter] = useState("");
  const [isCreatingFile, setIsCreatingFile] = useState(false);
  const [isCreatingFolder, setIsCreatingFolder] = useState(false);
  const [newItemName, setNewItemName] = useState("");
  const [editingPath, setEditingPath] = useState<string | null>(null);
  const [renamedName, setRenamedName] = useState("");
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({ "": true });

  const toggleFolder = (folderPath: string) => {
    setExpandedFolders((prev) => ({
      ...prev,
      [folderPath]: !prev[folderPath],
    }));
  };

  const getFileIcon = (fileName: string, isDir: boolean) => {
    if (isDir) {
      return Folder;
    }
    const lower = fileName.toLowerCase();
    if (lower.endsWith(".py")) return FileCode;
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return FileCode;
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return FileCode;
    if (lower.endsWith(".json")) return FileJson;
    if (lower.endsWith(".html") || lower.endsWith(".css")) return FileCode;
    if (lower.endsWith(".md")) return FileText;
    return File;
  };

  const getIconColor = (fileName: string, isDir: boolean) => {
    if (isDir) return "text-amber-400";
    const lower = fileName.toLowerCase();
    if (lower.endsWith(".py")) return "text-sky-400";
    if (lower.endsWith(".ts") || lower.endsWith(".tsx")) return "text-blue-400";
    if (lower.endsWith(".js") || lower.endsWith(".jsx")) return "text-yellow-400";
    if (lower.endsWith(".json")) return "text-emerald-400";
    if (lower.endsWith(".html")) return "text-orange-400";
    if (lower.endsWith(".css")) return "text-cyan-400";
    if (lower.endsWith(".md")) return "text-slate-300";
    return "text-slate-400";
  };

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newItemName.trim()) {
      setIsCreatingFile(false);
      setIsCreatingFolder(false);
      return;
    }
    if (isCreatingFile) {
      onCreateFile(newItemName.trim());
    } else if (isCreatingFolder) {
      onCreateFolder(newItemName.trim());
    }
    setNewItemName("");
    setIsCreatingFile(false);
    setIsCreatingFolder(false);
  };

  const handleRenameSubmit = (oldPath: string, e: React.FormEvent) => {
    e.preventDefault();
    if (!renamedName.trim() || renamedName === oldPath) {
      setEditingPath(null);
      return;
    }
    onRenameFile(oldPath, renamedName.trim());
    setEditingPath(null);
    setRenamedName("");
  };

  const safeFiles = files || [];
  const filteredFiles = safeFiles.filter((f) =>
    (f?.name || "").toLowerCase().includes(filter.toLowerCase()) ||
    (f?.path || "").toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 select-none overflow-hidden">
      {/* Explorer Header */}
      <div className="h-8 px-3 border-b border-slate-800/80 flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-slate-400">
        <span className="truncate">{projectName || "EXPLORER"}</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => {
              setIsCreatingFile(true);
              setIsCreatingFolder(false);
              setNewItemName("");
            }}
            title="New File"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setIsCreatingFolder(true);
              setIsCreatingFile(false);
              setNewItemName("");
            }}
            title="New Folder"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors"
          >
            <FolderPlus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onRefresh}
            title="Refresh Explorer"
            className="p-1 hover:text-white hover:bg-slate-800 rounded transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Filter Input */}
      <div className="p-2 border-b border-slate-800/60">
        <div className="relative">
          <Search className="w-3 h-3 absolute left-2 top-2 text-slate-500" />
          <input
            type="text"
            placeholder="Filter files..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2 py-1 pl-6 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-slate-700"
          />
        </div>
      </div>

      {/* New Item Input Box */}
      {(isCreatingFile || isCreatingFolder) && (
        <form onSubmit={handleCreateSubmit} className="p-2 bg-slate-950/80 border-b border-slate-800">
          <div className="flex items-center gap-1.5 text-xs text-slate-300 mb-1">
            {isCreatingFile ? <File className="w-3.5 h-3.5 text-amber-400" /> : <Folder className="w-3.5 h-3.5 text-indigo-400" />}
            <span>{isCreatingFile ? "New File Name:" : "New Folder Name:"}</span>
          </div>
          <input
            autoFocus
            type="text"
            placeholder={isCreatingFile ? "e.g. app.py, script.js" : "e.g. components, utils"}
            value={newItemName}
            onChange={(e) => setNewItemName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setIsCreatingFile(false);
                setIsCreatingFolder(false);
              }
            }}
            className="w-full bg-slate-900 border border-amber-500/50 rounded px-2 py-1 text-xs text-white focus:outline-none"
          />
        </form>
      )}

      {/* File Tree List */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-1 space-y-0.5 text-xs">
        {filteredFiles.length === 0 ? (
          <div className="p-4 text-center text-slate-500 text-[11px]">
            {filter ? "No files match filter" : "Workspace is empty. Create a file above."}
          </div>
        ) : (
          filteredFiles.map((file) => {
            const Icon = getFileIcon(file.name, file.is_dir);
            const iconColor = getIconColor(file.name, file.is_dir);
            const isSelected = activeFilePath === file.path;

            if (editingPath === file.path) {
              return (
                <form
                  key={file.path}
                  onSubmit={(e) => handleRenameSubmit(file.path, e)}
                  className="px-2 py-1 bg-slate-950 border border-amber-500/50 rounded flex items-center gap-1.5"
                >
                  <Icon className={`w-3.5 h-3.5 ${iconColor}`} />
                  <input
                    autoFocus
                    type="text"
                    value={renamedName}
                    onChange={(e) => setRenamedName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Escape") setEditingPath(null);
                    }}
                    className="flex-1 bg-transparent text-xs text-white focus:outline-none"
                  />
                </form>
              );
            }

            return (
              <div
                key={file.path}
                onClick={() => {
                  if (file.is_dir) {
                    toggleFolder(file.path);
                  } else {
                    onOpenFile(file.path);
                  }
                }}
                className={`group flex items-center justify-between px-2 py-1 rounded cursor-pointer transition-colors ${
                  isSelected
                    ? "bg-slate-800/90 text-white font-medium"
                    : "text-slate-300 hover:bg-slate-800/40 hover:text-white"
                }`}
              >
                <div className="flex items-center gap-1.5 min-w-0 flex-1">
                  {file.is_dir && (
                    <ChevronRight
                      className={`w-3 h-3 text-slate-500 transition-transform ${
                        expandedFolders[file.path] ? "rotate-90" : ""
                      }`}
                    />
                  )}
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${iconColor}`} />
                  <span className="truncate text-[12px]">{file.name}</span>
                </div>

                {/* Hover Actions: Rename / Delete */}
                <div className="hidden group-hover:flex items-center gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingPath(file.path);
                      setRenamedName(file.name);
                    }}
                    title="Rename"
                    className="p-1 hover:text-white hover:bg-slate-700/60 rounded"
                  >
                    <Edit2 className="w-3 h-3 text-slate-400" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Are you sure you want to delete '${file.name}'?`)) {
                        onDeleteFile(file.path);
                      }
                    }}
                    title="Delete"
                    className="p-1 hover:text-rose-400 hover:bg-slate-700/60 rounded"
                  >
                    <Trash2 className="w-3 h-3 text-slate-400" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

