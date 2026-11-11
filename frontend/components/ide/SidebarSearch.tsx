"use client";

import React, { useState } from "react";
import { Search, FileCode, ArrowRight, Loader2 } from "lucide-react";
import { searchWorkspace } from "@/services/api";

interface SearchMatch {
  file: string;
  line: number;
  content: string;
}

interface SidebarSearchProps {
  onOpenFileAtLine: (path: string, line: number) => void;
  workspacePath?: string;
}

export function SidebarSearch({ onOpenFileAtLine, workspacePath }: SidebarSearchProps) {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [matches, setMatches] = useState<SearchMatch[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setSearched(true);
    try {
      const res = await searchWorkspace(query.trim(), "", workspacePath);
      setMatches(res.matches || []);
    } catch (e) {
      console.error(e);
      setMatches([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Group matches by file
  const groupedMatches = matches.reduce((acc, m) => {
    if (!acc[m.file]) acc[m.file] = [];
    acc[m.file].push(m);
    return acc;
  }, {} as Record<string, SearchMatch[]>);

  const fileCount = Object.keys(groupedMatches).length;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900/60 select-none overflow-hidden text-xs">
      {/* Header */}
      <div className="h-8 px-3 border-b border-slate-800/80 flex items-center justify-between font-semibold uppercase tracking-wider text-slate-400">
        <span>SEARCH IN WORKSPACE</span>
        {matches.length > 0 && (
          <span className="text-[10px] text-slate-500 font-normal lowercase">
            {matches.length} results in {fileCount} files
          </span>
        )}
      </div>

      {/* Search Input Box */}
      <form onSubmit={handleSearch} className="p-2 border-b border-slate-800/60">
        <div className="relative">
          <input
            type="text"
            placeholder="Search text or symbol (e.g. FastAPI, def)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500/50"
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="absolute right-1.5 top-1.5 p-1 text-slate-400 hover:text-white transition-colors"
          >
            {isSearching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
          </button>
        </div>
      </form>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-3">
        {isSearching && (
          <div className="p-4 text-center text-slate-500 text-xs flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
            <span>Searching workspace...</span>
          </div>
        )}

        {!isSearching && searched && matches.length === 0 && (
          <div className="p-4 text-center text-slate-500 text-xs">
            No matches found for "{query}".
          </div>
        )}

        {!isSearching && Object.entries(groupedMatches).map(([filePath, fileMatches]) => (
          <div key={filePath} className="bg-slate-950/60 border border-slate-800/80 rounded overflow-hidden">
            <div className="px-2.5 py-1.5 bg-slate-900 border-b border-slate-800 flex items-center justify-between text-slate-300 font-mono text-[11px]">
              <div className="flex items-center gap-1.5 truncate">
                <FileCode className="w-3.5 h-3.5 text-sky-400 flex-shrink-0" />
                <span className="truncate">{filePath}</span>
              </div>
              <span className="text-[10px] text-slate-500 px-1 rounded bg-slate-800">
                {fileMatches.length}
              </span>
            </div>

            <div className="divide-y divide-slate-800/40">
              {fileMatches.map((m, idx) => (
                <div
                  key={idx}
                  onClick={() => onOpenFileAtLine(filePath, m.line)}
                  className="px-2.5 py-1 hover:bg-slate-800/50 cursor-pointer flex items-center gap-2 group transition-colors"
                >
                  <span className="text-slate-500 font-mono text-[10px] w-6 text-right">
                    {m.line}
                  </span>
                  <span className="text-slate-300 truncate font-mono text-[11px] group-hover:text-amber-200">
                    {m.content.trim()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

