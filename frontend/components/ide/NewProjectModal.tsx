"use client";

import React, { useState, useEffect } from "react";
import {
  FolderPlus,
  Zap,
  Code2,
  FileCode,
  Terminal,
  Layers,
  Folder,
  X,
  AlertCircle,
  CheckCircle2,
  Loader2,
  GitBranch,
} from "lucide-react";
import { createProject, fetchQuickPaths } from "@/services/api";

interface NewProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onProjectCreated: (projectData: {
    project: any;
    scan: any;
    files: any[];
    workspace_path: string;
  }) => void;
}

interface TemplateOption {
  id: string;
  name: string;
  tagline: string;
  icon: any;
  iconColor: string;
  badge: string;
  badgeColor: string;
  filesSummary: string[];
}

const TEMPLATES: TemplateOption[] = [
  {
    id: "react-ts",
    name: "React + TypeScript",
    tagline: "Vite + React 18 + TS + Lucide Icons",
    icon: Zap,
    iconColor: "text-amber-400",
    badge: "Frontend SPA",
    badgeColor: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    filesSummary: ["package.json", "vite.config.ts", "tsconfig.json", "src/App.tsx", "src/main.tsx"],
  },
  {
    id: "nextjs",
    name: "Next.js",
    tagline: "Next.js 14 + React 18 + App Router + TS",
    icon: Code2,
    iconColor: "text-sky-400",
    badge: "Full Stack",
    badgeColor: "bg-sky-500/10 text-sky-300 border-sky-500/30",
    filesSummary: ["package.json", "next.config.js", "tsconfig.json", "app/page.tsx", "app/layout.tsx"],
  },
  {
    id: "python-fastapi",
    name: "Python + FastAPI",
    tagline: "FastAPI REST API + Pydantic + Pytest",
    icon: FileCode,
    iconColor: "text-emerald-400",
    badge: "Backend API",
    badgeColor: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    filesSummary: ["main.py", "requirements.txt", "tests/test_main.py", "README.md"],
  },
  {
    id: "node-express",
    name: "Node.js + Express",
    tagline: "Express REST Server + CORS + Static UI",
    icon: Terminal,
    iconColor: "text-yellow-400",
    badge: "Node Server",
    badgeColor: "bg-yellow-500/10 text-yellow-300 border-yellow-500/30",
    filesSummary: ["package.json", "index.js", "public/index.html", "README.md"],
  },
  {
    id: "empty",
    name: "Empty Project",
    tagline: "Clean directory with README.md & .gitignore",
    icon: Layers,
    iconColor: "text-purple-400",
    badge: "Starter",
    badgeColor: "bg-purple-500/10 text-purple-300 border-purple-500/30",
    filesSummary: ["README.md", ".gitignore"],
  },
];

export function NewProjectModal({ isOpen, onClose, onProjectCreated }: NewProjectModalProps) {
  const [projectName, setProjectName] = useState("");
  const [destinationFolder, setDestinationFolder] = useState("D:\\DODO\\workspace");
  const [selectedTemplate, setSelectedTemplate] = useState("react-ts");
  const [description, setDescription] = useState("");
  const [initGit, setInitGit] = useState(true);

  const [quickPaths, setQuickPaths] = useState<Array<{ label: string; path: string; is_default: boolean }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    setErrorMsg(null);
    fetchQuickPaths()
      .then((paths) => {
        setQuickPaths(paths);
        if (paths.length > 0 && !destinationFolder) {
          setDestinationFolder(paths[0].path);
        }
      })
      .catch(() => {});

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const targetPathPreview = projectName.trim()
    ? `${destinationFolder.replace(/[\\/]+$/, "")}\\${projectName.trim()}`
    : destinationFolder;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();

    const name = projectName.trim();
    if (!name) {
      setErrorMsg("Please enter a valid project name.");
      return;
    }

    if (!destinationFolder.trim()) {
      setErrorMsg("Please enter or select a valid destination folder.");
      return;
    }

    setIsLoading(true);
    setErrorMsg(null);

    try {
      const data = await createProject({
        name,
        destination_folder: destinationFolder.trim(),
        template: selectedTemplate,
        description: description.trim(),
        init_git: initGit,
      });

      onProjectCreated(data);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create project");
    } finally {
      setIsLoading(false);
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
        className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[92vh] animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/60 flex items-center justify-between select-none">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <FolderPlus className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                Create New Project
              </h2>
              <p className="text-xs text-slate-400">
                Generate production starter files, configure project architecture, and launch in DODO
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

        {/* Form Body */}
        <form onSubmit={handleCreate} className="p-6 overflow-y-auto space-y-5 text-xs font-sans">
          {/* Error Banner */}
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-semibold block text-xs">Project Creation Error</span>
                <span className="text-[11px] leading-relaxed block">{errorMsg}</span>
              </div>
            </div>
          )}

          {/* Project Name & Destination Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-slate-300 font-semibold text-xs block">
                Project Name <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                autoFocus
                placeholder="e.g. task-manager-app"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/60 font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-slate-300 font-semibold text-xs block">
                Destination Folder <span className="text-amber-400">*</span>
              </label>
              <input
                type="text"
                placeholder="e.g. D:\DODO\workspace"
                value={destinationFolder}
                onChange={(e) => setDestinationFolder(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/60 font-mono"
              />
            </div>
          </div>

          {/* Target Path Preview */}
          <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <div className="flex items-center gap-1.5 truncate">
              <span className="text-slate-500">Target Path:</span>
              <span className="text-amber-300 truncate" title={targetPathPreview}>
                {targetPathPreview}
              </span>
            </div>
            {(quickPaths || []).length > 0 && (
              <div className="flex items-center gap-1 ml-2 flex-shrink-0">
                {(quickPaths || []).map((qp) => (
                  <button
                    key={qp.path}
                    type="button"
                    onClick={() => setDestinationFolder(qp.path)}
                    className="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-[10px] text-slate-400 hover:text-white"
                  >
                    {qp.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Template Selection */}
          <div className="space-y-2">
            <label className="text-slate-300 font-semibold text-xs block">
              Choose Project Architecture & Starter Template
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {TEMPLATES.map((tmpl) => {
                const Icon = tmpl.icon;
                const isSelected = selectedTemplate === tmpl.id;

                return (
                  <div
                    key={tmpl.id}
                    onClick={() => setSelectedTemplate(tmpl.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                      isSelected
                        ? "bg-amber-500/10 border-amber-500/50 shadow-md shadow-amber-500/10"
                        : "bg-slate-950 border-slate-800/80 hover:border-slate-700 hover:bg-slate-900/50"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`p-1.5 rounded-lg bg-slate-900 border border-slate-800 ${tmpl.iconColor}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="font-bold text-white text-xs">{tmpl.name}</h4>
                          <span className="text-[11px] text-slate-400 block">{tmpl.tagline}</span>
                        </div>
                      </div>
                      <span className={`text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded border ${tmpl.badgeColor}`}>
                        {tmpl.badge}
                      </span>
                    </div>

                    <div className="mt-2.5 pt-2 border-t border-slate-800/50 flex flex-wrap gap-1">
                      {tmpl.filesSummary.slice(0, 3).map((f) => (
                        <span key={f} className="text-[9px] font-mono text-slate-500 bg-slate-900/60 px-1 rounded">
                          {f}
                        </span>
                      ))}
                      {tmpl.filesSummary.length > 3 && (
                        <span className="text-[9px] font-mono text-slate-600">
                          +{tmpl.filesSummary.length - 3} more
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Description (Optional) */}
          <div className="space-y-1.5">
            <label className="text-slate-400 font-medium text-xs block">
              Project Description (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Full-stack task management dashboard with real-time updates"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500/60"
            />
          </div>

          {/* Git Init Checkbox */}
          <div className="flex items-center gap-2 pt-1 text-xs">
            <input
              type="checkbox"
              id="init-git-check"
              checked={initGit}
              onChange={(e) => setInitGit(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-amber-500 focus:ring-0 focus:ring-offset-0 cursor-pointer"
            />
            <label htmlFor="init-git-check" className="text-slate-300 cursor-pointer flex items-center gap-1.5 select-none">
              <GitBranch className="w-3.5 h-3.5 text-indigo-400" />
              <span>Initialize a new Git repository in the created directory</span>
            </label>
          </div>
        </form>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs select-none">
          <span className="text-slate-500 font-mono text-[11px]">
            Selected: {TEMPLATES.find((t) => t.id === selectedTemplate)?.name}
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
              onClick={handleCreate}
              disabled={isLoading || !projectName.trim()}
              className="px-5 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-all shadow-md shadow-emerald-500/20 flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Creating & Opening...</span>
                </>
              ) : (
                <>
                  <FolderPlus className="w-3.5 h-3.5" />
                  <span>Create Project</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

