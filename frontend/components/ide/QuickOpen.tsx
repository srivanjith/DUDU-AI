"use client";

import React, { useState, useEffect } from "react";
import { Search, FileCode, File, X } from "lucide-react";
import { WorkspaceFile } from "@/types";

interface QuickOpenProps {
  isOpen: boolean;
  onClose: () => void;
  files: WorkspaceFile[];
  onSelectFile: (path: string) => void;
}

export function QuickOpen({ isOpen, onClose, files, onSelectFile }: QuickOpenProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const codeFiles = files.filter((f) => !f.is_dir);
  const filteredFiles = codeFiles.filter((f) =>
    f.name.toLowerCase().includes(query.toLowerCase()) ||
    f.path.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredFiles.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredFiles.length) % Math.max(1, filteredFiles.length));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredFiles[selectedIndex]) {
        onSelectFile(filteredFiles[selectedIndex].path);
        onClose();
      }
    } else if (e.key === "Escape") {
      onClose();
    }
  };

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-start justify-center pt-20 p-4 select-none animate-in fade-in duration-100"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl overflow-hidden flex flex-col text-xs font-sans"
      >
        {/* Search Input Bar */}
        <div className="p-3 border-b border-slate-800 flex items-center gap-2.5 bg-slate-950">
          <Search className="w-4 h-4 text-slate-400" />
          <input
            autoFocus
            type="text"
            placeholder="Type name to open file in workspace..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 focus:outline-none font-mono"
          />
          <kbd className="px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-[10px] font-mono text-slate-400">
            Ctrl+P
          </kbd>
        </div>

        {/* Files List */}
        <div className="max-h-80 overflow-y-auto p-1.5 space-y-0.5">
          {filteredFiles.length === 0 ? (
            <div className="p-6 text-center text-slate-500 text-xs">
              No files matching "{query}"
            </div>
          ) : (
            filteredFiles.map((file, idx) => {
              const isSelected = idx === selectedIndex;
              const fileName = file.name;
              const dirPath = file.path.includes("/")
                ? file.path.substring(0, file.path.lastIndexOf("/"))
                : "";

              return (
                <div
                  key={file.path}
                  onClick={() => {
                    onSelectFile(file.path);
                    onClose();
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                    isSelected ? "bg-amber-500/20 text-white font-medium" : "text-slate-300 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <FileCode className={`w-4 h-4 flex-shrink-0 ${isSelected ? "text-amber-400" : "text-slate-400"}`} />
                    <span className="font-mono text-xs">{fileName}</span>
                    {dirPath && (
                      <span className="text-[11px] text-slate-500 font-mono truncate">
                        {dirPath}
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

