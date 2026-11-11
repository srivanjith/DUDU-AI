"use client";

import React, { useState, useEffect, useRef } from "react";
import { TopNavBar } from "@/components/ide/TopNavBar";
import { ActivityBar, SidebarTab } from "@/components/ide/ActivityBar";
import { SidebarExplorer } from "@/components/ide/SidebarExplorer";
import { SidebarSearch } from "@/components/ide/SidebarSearch";
import { SidebarGit } from "@/components/ide/SidebarGit";
import { EditorArea, FileTab } from "@/components/ide/EditorArea";
import { BottomPanel, BottomTab } from "@/components/ide/BottomPanel";
import { RightAgentPanel } from "@/components/ide/RightAgentPanel";
import { StatusBar } from "@/components/ide/StatusBar";
import { CommandPalette, CommandItem } from "@/components/ide/CommandPalette";
import { QuickOpen } from "@/components/ide/QuickOpen";
import { SettingsModal } from "@/components/SettingsModal";
import { MemoryCenter } from "@/components/MemoryCenter";
import { SidebarMemory } from "@/components/ide/SidebarMemory";
import { OpenProjectModal } from "@/components/ide/OpenProjectModal";
import { NewProjectModal } from "@/components/ide/NewProjectModal";

import {
  WorkspaceFile,
  ProjectScan,
  AgentTask,
  Message,
  SystemHealth,
  GitStatusResult,
} from "@/types";

import {
  fetchHealth,
  fetchWorkspaceFiles,
  fetchFileContent,
  saveWorkspaceFile,
  fetchWorkspaceStatus,
  deleteWorkspaceFile,
  renameWorkspaceFile,
  createWorkspaceFolder,
  fetchGitStatus,
  fetchTasks,
  createTask,
  cancelTask,
  approveTaskStep,
  streamChatMessage,
  createConversation,
} from "@/services/api";

import {
  Files,
  Search,
  Terminal,
  Globe,
  Sparkles,
  Save,
  RotateCcw,
  Settings,
  Split,
  Plus,
  X,
  FolderOpen,
  FolderPlus,
} from "lucide-react";

export default function DodoIDE() {
  // 1. Project & Workspace State
  const [workspacePath, setWorkspacePath] = useState("D:\\DODO\\workspace");
  const [projectName, setProjectName] = useState("DODO Workspace");
  const [projectScan, setProjectScan] = useState<ProjectScan | null>(null);
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [gitStatus, setGitStatus] = useState<GitStatusResult | null>(null);

  // 2. Editor State (Tabs, Active Content, Diff)
  const [openTabs, setOpenTabs] = useState<FileTab[]>([]);
  const [activeTabPath, setActiveTabPath] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  // 3. Layout Panels Visibility & Resizable Dimensions
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("explorer");
  const [sidebarWidth, setSidebarWidth] = useState(280);
  const [showBottomPanel, setShowBottomPanel] = useState(true);
  const [bottomTab, setBottomTab] = useState<BottomTab>("terminal");
  const [bottomHeight, setBottomHeight] = useState(250);
  const [showRightAgent, setShowRightAgent] = useState(true);
  const [rightAgentWidth, setRightAgentWidth] = useState(400);

  // Splitter dragging states
  const [isDraggingSidebar, setIsDraggingSidebar] = useState(false);
  const [isDraggingRightAgent, setIsDraggingRightAgent] = useState(false);

  // 4. Modals State
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isQuickOpenOpen, setIsQuickOpenOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isMemoryCenterOpen, setIsMemoryCenterOpen] = useState(false);
  const [isOpenProjectOpen, setIsOpenProjectOpen] = useState(false);
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);

  // 5. AI Models & Health
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [selectedModel, setSelectedModel] = useState("auto");
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  // 6. Autonomous Agent Tasks State
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [activeTask, setActiveTask] = useState<AgentTask | null>(null);
  const [isExecutingTask, setIsExecutingTask] = useState(false);

  // 7. Conversational Chat State
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [isStreamingChat, setIsStreamingChat] = useState(false);
  const abortChatRef = useRef<AbortController | null>(null);

  // Active File & Dirty Check
  const activeTab = openTabs.find((t) => t.path === activeTabPath);
  const isDirty = activeTab ? activeTab.originalContent !== activeTab.currentContent : false;

  // Initial Load
  useEffect(() => {
    loadHealth();
    loadWorkspace();
    loadGit();
    loadTasks();

    const healthInterval = setInterval(loadHealth, 10000);
    return () => clearInterval(healthInterval);
  }, []);

  // Keyboard Shortcuts Listener
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Shift+P: Command Palette
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "p") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
      // Ctrl+P: Quick Open File
      else if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "p") {
        e.preventDefault();
        setIsQuickOpenOpen((prev) => !prev);
      }
      // Ctrl+O: Open Project
      else if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        setIsOpenProjectOpen(true);
      }
      // Ctrl+S: Save Active File
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        handleSaveActiveFile();
      }
      // Ctrl+`: Toggle Bottom Panel
      else if ((e.ctrlKey || e.metaKey) && e.key === "`") {
        e.preventDefault();
        setShowBottomPanel((prev) => !prev);
      }
      // Ctrl+B: Toggle Left Sidebar
      else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "b") {
        e.preventDefault();
        setShowLeftSidebar((prev) => !prev);
      }
      // Ctrl+Shift+E: Open Explorer
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "e") {
        e.preventDefault();
        setShowLeftSidebar(true);
        setSidebarTab("explorer");
      }
      // Ctrl+Shift+F: Open Search
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "f") {
        e.preventDefault();
        setShowLeftSidebar(true);
        setSidebarTab("search");
      }
      // Ctrl+Shift+A: Toggle Right AI Agent
      else if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key.toLowerCase() === "a") {
        e.preventDefault();
        setShowRightAgent((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [activeTab]);

  // Dynamic Horizontal Splitter Dragging (Sidebar & Right Agent)
  useEffect(() => {
    if (!isDraggingSidebar && !isDraggingRightAgent) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (isDraggingSidebar) {
        // Activity bar is 48px wide
        const newWidth = e.clientX - 48;
        if (newWidth >= 180 && newWidth <= 520) {
          setSidebarWidth(newWidth);
        }
      }
      if (isDraggingRightAgent) {
        const newWidth = window.innerWidth - e.clientX;
        if (newWidth >= 280 && newWidth <= 720) {
          setRightAgentWidth(newWidth);
        }
      }
    };

    const handleMouseUp = () => {
      setIsDraggingSidebar(false);
      setIsDraggingRightAgent(false);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDraggingSidebar, isDraggingRightAgent]);

  // Loaders
  const loadHealth = async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
      if (h?.inference_engine?.models) {
        setAvailableModels(h.inference_engine.models);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadWorkspace = async (customPath?: string) => {
    try {
      const activeP = customPath || workspacePath;
      const res = await fetchWorkspaceFiles(activeP);
      setFiles(res.items || []);

      const statusRes = await fetchWorkspaceStatus(activeP);
      if (statusRes) {
        const resolved = statusRes.authorized_workspace || activeP;
        setWorkspacePath(resolved);
        if (statusRes.scan) {
          setProjectScan(statusRes.scan);
          setProjectName(statusRes.scan.project_name || "workspace");
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadGit = async (customPath?: string) => {
    try {
      const g = await fetchGitStatus(customPath || workspacePath);
      setGitStatus(g);
    } catch (e) {
      console.error(e);
    }
  };

  const handleProjectLoaded = (data: {
    project: any;
    scan: any;
    files: any[];
    workspace_path: string;
  }) => {
    const newPath = data.workspace_path;
    setWorkspacePath(newPath);
    setProjectName(data.project?.name || data.scan?.project_name || "Project");
    setProjectScan(data.scan);
    setFiles(data.files || []);
    setOpenTabs([]);
    setActiveTabPath(null);

    loadGit(newPath);
    loadTasks();

    // Automatically open first key file
    const items = data.files || [];
    const priorityFiles = ["README.md", "src/App.tsx", "main.py", "index.html", "index.js", "package.json"];
    const fileToOpen =
      priorityFiles.find((pf) => items.some((f: any) => !f.is_dir && (f.path === pf || f.path.endsWith(pf)))) ||
      items.find((f: any) => !f.is_dir)?.path;

    if (fileToOpen) {
      handleOpenFile(fileToOpen, newPath);
    }
  };

  const loadTasks = async () => {
    try {
      const t = await fetchTasks();
      setTasks(t || []);
      if (t?.length > 0 && !activeTask) {
        setActiveTask(t[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Editor Tab Actions
  const handleOpenFile = async (path: string, customWorkspace?: string) => {
    const existing = openTabs.find((t) => t.path === path);
    if (existing) {
      setActiveTabPath(path);
      return;
    }
    try {
      const ws = customWorkspace || workspacePath;
      const res = await fetchFileContent(path, ws);
      const content = res.content || "";
      const newTab: FileTab = {
        path,
        originalContent: content,
        currentContent: content,
      };
      setOpenTabs((prev) => [...prev, newTab]);
      setActiveTabPath(path);
    } catch (e) {
      console.error("Open file error", e);
    }
  };

  const handleCloseTab = (path: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const remaining = openTabs.filter((t) => t.path !== path);
    setOpenTabs(remaining);
    if (activeTabPath === path) {
      setActiveTabPath(remaining.length > 0 ? remaining[remaining.length - 1].path : null);
    }
  };

  const handleContentChange = (newContent: string) => {
    if (!activeTabPath) return;
    setOpenTabs((prev) =>
      prev.map((t) => (t.path === activeTabPath ? { ...t, currentContent: newContent } : t))
    );
  };

  const handleSaveActiveFile = async () => {
    if (!activeTab || !isDirty) return;
    try {
      await saveWorkspaceFile(activeTab.path, activeTab.currentContent, workspacePath);
      setOpenTabs((prev) =>
        prev.map((t) =>
          t.path === activeTab.path ? { ...t, originalContent: activeTab.currentContent } : t
        )
      );
      loadWorkspace(workspacePath);
      loadGit(workspacePath);
    } catch (e) {
      console.error("Save error", e);
    }
  };

  // File Operations
  const handleCreateFile = async (name: string) => {
    try {
      await saveWorkspaceFile(name, "", workspacePath);
      loadWorkspace(workspacePath);
      handleOpenFile(name, workspacePath);
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateFolder = async (name: string) => {
    try {
      await createWorkspaceFolder(name, workspacePath);
      loadWorkspace(workspacePath);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRenameFile = async (oldPath: string, newPath: string) => {
    try {
      await renameWorkspaceFile(oldPath, newPath, false, workspacePath);
      loadWorkspace(workspacePath);
      // Update tab if open
      setOpenTabs((prev) =>
        prev.map((t) => (t.path === oldPath ? { ...t, path: newPath } : t))
      );
      if (activeTabPath === oldPath) {
        setActiveTabPath(newPath);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteFile = async (path: string) => {
    try {
      await deleteWorkspaceFile(path, true, workspacePath);
      loadWorkspace(workspacePath);
      // Close tab if open
      setOpenTabs((prev) => prev.filter((t) => t.path !== path));
      if (activeTabPath === path) {
        setActiveTabPath(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Autonomous Task Orchestration
  const handleCreateTask = async (prompt: string) => {
    try {
      const task = await createTask(prompt, "developer");
      setTasks((prev) => [task, ...prev]);
      setActiveTask(task);
      setIsExecutingTask(true);
      setShowRightAgent(true);

      const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const eventSource = new EventSource(`${apiBase}/api/agent/tasks/${task.id}/stream`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "plan_generated") {
            setActiveTask((prev: any) => ({
              ...prev,
              plan: {
                objective: data.objective,
                analysis: data.analysis,
                tech_stack: data.tech_stack,
                complexity_score: data.complexity_score,
                risk_level: data.risk_level,
                approval_required: data.approval_required,
                estimated_steps: data.total_steps,
                steps: data.steps,
              },
            }));
          } else if (data.type === "approval_required") {
            setActiveTask((prev: any) => ({
              ...prev,
              status: "awaiting_approval",
              pending_approval: {
                approval_id: data.approval_id,
                task_id: task.id,
                step_id: data.step_id,
                tool_name: data.title,
                permission_level: data.permission_level,
                risk_level: data.risk_level,
                description: data.message,
                status: "pending",
              },
            }));
            setIsExecutingTask(false);
            eventSource.close();
          } else if (data.type === "step_start") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id ? { ...s, status: "in_progress" } : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
          } else if (data.type === "step_complete") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id ? { ...s, status: "completed", result: data.result_preview } : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
            loadWorkspace();
            loadGit();
          } else if (data.type === "step_failed") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id ? { ...s, status: "failed", error: data.error } : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
          } else if (data.type === "task_completed") {
            setActiveTask((prev: any) => ({
              ...prev,
              status: "completed",
              verified: data.verified,
              result_summary: data.report,
            }));
            setIsExecutingTask(false);
            eventSource.close();
            loadWorkspace();
            loadGit();
            loadTasks();
          } else if (data.type === "cancelled") {
            setActiveTask((prev: any) => ({ ...prev, status: "cancelled" }));
            setIsExecutingTask(false);
            eventSource.close();
          }
        } catch (e) {
          console.error(e);
        }
      };

      eventSource.onerror = () => {
        setIsExecutingTask(false);
        eventSource.close();
      };
    } catch (e) {
      console.error(e);
      setIsExecutingTask(false);
    }
  };

  const handleApproveStep = async (taskId: string, stepId: number, approved: boolean) => {
    try {
      await approveTaskStep(taskId, stepId, approved);
      if (approved) {
        setIsExecutingTask(true);
        setActiveTask((prev: any) => ({ ...prev, pending_approval: null, status: "executing" }));

        const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const eventSource = new EventSource(`${apiBase}/api/agent/tasks/${taskId}/stream?resume=true`);

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "step_complete") {
              setActiveTask((prev: any) => {
                if (!prev?.plan) return prev;
                const updated = prev.plan.steps.map((s: any) =>
                  s.step_id === data.step_id ? { ...s, status: "completed", result: data.result_preview } : s
                );
                return { ...prev, plan: { ...prev.plan, steps: updated } };
              });
              loadWorkspace();
              loadGit();
            } else if (data.type === "task_completed") {
              setActiveTask((prev: any) => ({
                ...prev,
                status: "completed",
                verified: data.verified,
                result_summary: data.report,
              }));
              setIsExecutingTask(false);
              eventSource.close();
              loadWorkspace();
              loadGit();
              loadTasks();
            }
          } catch (e) {
            console.error(e);
          }
        };

        eventSource.onerror = () => {
          setIsExecutingTask(false);
          eventSource.close();
        };
      } else {
        setActiveTask((prev: any) => ({ ...prev, pending_approval: null, status: "cancelled" }));
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCancelTask = async (taskId: string) => {
    try {
      await cancelTask(taskId);
      setIsExecutingTask(false);
      setActiveTask((prev: any) => ({ ...prev, status: "cancelled" }));
    } catch (e) {
      console.error(e);
    }
  };

  // Chat Q&A Actions
  const handleSendMessage = async (content: string, model: string) => {
    let currentConvId = activeConvId;
    if (!currentConvId) {
      const newConv = await createConversation("IDE Assistant Chat", "assistant");
      currentConvId = newConv.id;
      setActiveConvId(newConv.id);
    }

    const userMsg: Message = { role: "user", content, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);

    const assistantMsg: Message = {
      role: "assistant",
      content: "",
      model_used: model,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);
    setIsStreamingChat(true);

    const controller = new AbortController();
    abortChatRef.current = controller;

    streamChatMessage(
      currentConvId!,
      content,
      model,
      (token, usedModel) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0) {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: updated[lastIdx].content + token,
              model_used: usedModel,
            };
          }
          return updated;
        });
      },
      () => {
        setIsStreamingChat(false);
        abortChatRef.current = null;
      },
      (err) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0) {
            updated[lastIdx] = { ...updated[lastIdx], content: `⚠️ ${err}` };
          }
          return updated;
        });
        setIsStreamingChat(false);
        abortChatRef.current = null;
      },
      controller.signal
    );
  };

  const handleStopStreamingChat = () => {
    if (abortChatRef.current) {
      abortChatRef.current.abort();
      abortChatRef.current = null;
    }
    setIsStreamingChat(false);
  };

  // Command Palette Items
  const commands: CommandItem[] = [
    {
      id: "open_project",
      label: "File: Open Project Folder...",
      category: "Project",
      shortcut: "Ctrl+O",
      icon: FolderOpen,
      action: () => setIsOpenProjectOpen(true),
    },
    {
      id: "new_project",
      label: "File: Create New Project...",
      category: "Project",
      icon: FolderPlus,
      action: () => setIsNewProjectOpen(true),
    },
    {
      id: "toggle_terminal",
      label: "View: Toggle Terminal",
      category: "Terminal",
      shortcut: "Ctrl+`",
      icon: Terminal,
      action: () => {
        setShowBottomPanel((prev) => !prev);
        setBottomTab("terminal");
      },
    },
    {
      id: "toggle_browser",
      label: "View: Open Browser Preview",
      category: "Browser",
      icon: Globe,
      action: () => {
        setShowBottomPanel(true);
        setBottomTab("browser");
      },
    },
    {
      id: "toggle_agent",
      label: "View: Toggle Autonomous AI Agent Panel",
      category: "Agent",
      shortcut: "Ctrl+Shift+A",
      icon: Sparkles,
      action: () => setShowRightAgent((prev) => !prev),
    },
    {
      id: "save_file",
      label: "File: Save Active File",
      category: "File",
      shortcut: "Ctrl+S",
      icon: Save,
      action: handleSaveActiveFile,
    },
    {
      id: "quick_open",
      label: "File: Quick Open File...",
      category: "File",
      shortcut: "Ctrl+P",
      icon: Files,
      action: () => setIsQuickOpenOpen(true),
    },
    {
      id: "toggle_diff",
      label: "Editor: Toggle File Diff Preview",
      category: "Editor",
      icon: Split,
      action: () => setShowDiff((prev) => !prev),
    },
    {
      id: "open_settings",
      label: "Preferences: Open Settings",
      category: "Preferences",
      icon: Settings,
      action: () => setIsSettingsOpen(true),
    },
  ];

  const agentStatusValue = activeTask
    ? isExecutingTask
      ? (activeTask.status as any)
      : activeTask.status === "awaiting_approval"
      ? "awaiting_approval"
      : "idle"
    : "idle";

  return (
    <div className="flex flex-col h-screen w-screen bg-slate-950 text-slate-100 overflow-hidden font-sans antialiased">
      {/* 1. TOP NAVIGATION BAR */}
      <TopNavBar
        projectName={projectName}
        workspacePath={workspacePath}
        isDirty={isDirty}
        onSaveActiveFile={handleSaveActiveFile}
        selectedModel={selectedModel}
        onSelectModel={setSelectedModel}
        availableModels={availableModels}
        agentStatus={agentStatusValue}
        showLeftSidebar={showLeftSidebar}
        onToggleLeftSidebar={() => setShowLeftSidebar(!showLeftSidebar)}
        showBottomPanel={showBottomPanel}
        onToggleBottomPanel={() => setShowBottomPanel(!showBottomPanel)}
        showRightAgent={showRightAgent}
        onToggleRightAgent={() => setShowRightAgent(!showRightAgent)}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        onOpenQuickOpen={() => setIsQuickOpenOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenProjectModal={() => setIsOpenProjectOpen(true)}
        onNewProjectModal={() => setIsNewProjectOpen(true)}
        ollamaStatus={health?.inference_engine?.status === "online" ? "online" : "offline"}
        openRouterConfigured={health?.openrouter?.is_configured}
      />

      {/* 2. MAIN WORKSPACE ROW */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Activity Bar (Vertical Left Strip) */}
        <ActivityBar
          activeTab={sidebarTab}
          onSelectTab={(tab) => {
            setSidebarTab(tab);
            setShowLeftSidebar(true);
          }}
          isOpen={showLeftSidebar}
          onToggleOpen={() => setShowLeftSidebar(!showLeftSidebar)}
          stagedGitCount={gitStatus?.staged_count || 0}
          onOpenSettings={() => setIsSettingsOpen(true)}
        />

        {/* Primary Sidebar Content (Explorer, Search, Git, Memory) */}
        {showLeftSidebar && (
          <div
            style={{ width: `${sidebarWidth}px` }}
            className="border-r border-slate-800/80 bg-slate-900/40 flex flex-col overflow-hidden z-10 flex-shrink-0"
          >
            {sidebarTab === "explorer" && (
              <SidebarExplorer
                files={files}
                onOpenFile={handleOpenFile}
                activeFilePath={activeTabPath}
                onRefresh={loadWorkspace}
                onCreateFile={handleCreateFile}
                onCreateFolder={handleCreateFolder}
                onRenameFile={handleRenameFile}
                onDeleteFile={handleDeleteFile}
                projectName={projectName}
              />
            )}

            {sidebarTab === "search" && (
              <SidebarSearch
                onOpenFileAtLine={(path, line) => {
                  handleOpenFile(path);
                }}
                workspacePath={workspacePath}
              />
            )}

            {sidebarTab === "git" && (
              <SidebarGit
                onOpenFileDiff={(path) => {
                  handleOpenFile(path);
                  setShowDiff(true);
                }}
                workspacePath={workspacePath}
              />
            )}

            {sidebarTab === "agent_history" && (
              <div className="flex-1 flex flex-col h-full bg-slate-900/60 p-3 space-y-2 overflow-y-auto text-xs">
                <span className="font-semibold uppercase tracking-wider text-slate-400 text-[11px]">
                  Autonomous Agent Runs
                </span>
                <div className="space-y-1.5 mt-2">
                  {(tasks || []).length === 0 ? (
                    <div className="text-slate-500 italic p-2 text-center">No runs recorded yet.</div>
                  ) : (
                    (tasks || []).map((t) => (
                      <div
                        key={t.id}
                        onClick={() => {
                          setActiveTask(t);
                          setShowRightAgent(true);
                        }}
                        className={`p-2.5 rounded border cursor-pointer transition-colors ${
                          activeTask?.id === t.id
                            ? "bg-amber-500/10 border-amber-500/40 text-white"
                            : "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] text-slate-500 mb-1">
                          <span className="font-mono">{t.id.slice(0, 8)}</span>
                          <span className={`px-1.5 py-0.2 rounded font-semibold uppercase ${
                            t.status === "completed" ? "bg-emerald-500/20 text-emerald-300" :
                            t.status === "failed" ? "bg-rose-500/20 text-rose-300" : "bg-indigo-500/20 text-indigo-300"
                          }`}>
                            {t.status}
                          </span>
                        </div>
                        <p className="font-medium truncate text-xs">{t.prompt}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {sidebarTab === "memory" && (
              <SidebarMemory onOpenFullView={() => setIsMemoryCenterOpen(true)} />
            )}
          </div>
        )}

        {/* Draggable Vertical Splitter: Sidebar / Editor */}
        {showLeftSidebar && (
          <div
            onMouseDown={() => setIsDraggingSidebar(true)}
            className="w-1 cursor-col-resize bg-slate-800/80 hover:bg-amber-400/50 transition-colors z-20 flex-shrink-0"
            title="Drag to resize sidebar"
          />
        )}

        {/* Center: Monaco Editor Area + Bottom Resizable Panel */}
        <div className="flex-1 flex flex-col overflow-hidden relative min-w-0">
          {/* Main Editor Center */}
          <div className="flex-1 flex flex-col overflow-hidden relative">
            <EditorArea
              openTabs={openTabs}
              activeTabPath={activeTabPath}
              onSelectTab={setActiveTabPath}
              onCloseTab={handleCloseTab}
              onContentChange={handleContentChange}
              onSave={handleSaveActiveFile}
              showDiff={showDiff}
              onToggleDiff={() => setShowDiff(!showDiff)}
              onTriggerAgentTask={handleCreateTask}
              onOpenProject={() => setIsOpenProjectOpen(true)}
              onNewProject={() => setIsNewProjectOpen(true)}
            />
          </div>

          {/* Bottom Resizable Panel (Terminal, Browser Preview, Problems, Output) */}
          <BottomPanel
            isOpen={showBottomPanel}
            onClose={() => setShowBottomPanel(false)}
            activeTab={bottomTab}
            onSelectTab={setBottomTab}
            height={bottomHeight}
            onResize={setBottomHeight}
          />
        </div>

        {/* Draggable Vertical Splitter: Editor / Right Agent */}
        {showRightAgent && (
          <div
            onMouseDown={() => setIsDraggingRightAgent(true)}
            className="w-1 cursor-col-resize bg-slate-800/80 hover:bg-amber-400/50 transition-colors z-20 flex-shrink-0"
            title="Drag to resize AI Agent panel"
          />
        )}

        {/* Right: Antigravity-like Persistent AI Agent Panel */}
        {showRightAgent && (
          <RightAgentPanel
            tasks={tasks}
            activeTask={activeTask}
            onSelectTask={setActiveTask}
            onCreateTask={handleCreateTask}
            onCancelTask={handleCancelTask}
            onApproveStep={handleApproveStep}
            isExecutingTask={isExecutingTask}
            messages={messages}
            onSendMessage={handleSendMessage}
            isStreamingChat={isStreamingChat}
            onStopStreamingChat={handleStopStreamingChat}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            onClose={() => setShowRightAgent(false)}
            width={rightAgentWidth}
            ollamaStatus={health?.inference_engine?.status === "online" ? "online" : "offline"}
            onStartOllama={loadHealth}
            onRetryChat={() => {
              for (let i = messages.length - 1; i >= 0; i--) {
                if (messages[i].role === "user") {
                  handleSendMessage(messages[i].content, selectedModel);
                  break;
                }
              }
            }}
          />
        )}
      </div>

      {/* 3. STATUS BAR */}
      <StatusBar
        branchName={gitStatus?.branch || "main"}
        activeLanguage={activeTab ? activeTab.path.split(".").pop()?.toUpperCase() : "PLAINTEXT"}
        health={health}
        onOpenTerminal={() => {
          setShowBottomPanel(true);
          setBottomTab("terminal");
        }}
        onOpenDiagnostics={() => setIsSettingsOpen(true)}
      />

      {/* Modals & Overlays */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        commands={commands}
      />

      <QuickOpen
        isOpen={isQuickOpenOpen}
        onClose={() => setIsQuickOpenOpen(false)}
        files={files}
        onSelectFile={handleOpenFile}
      />

      {isSettingsOpen && (
        <SettingsModal
          health={health}
          onClose={() => setIsSettingsOpen(false)}
        />
      )}

      {isMemoryCenterOpen && (
        <div
          onClick={() => setIsMemoryCenterOpen(false)}
          className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-6 animate-in fade-in duration-150"
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-6xl h-[88vh] bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col relative"
          >
            <div className="absolute top-4 right-4 z-50">
              <button
                onClick={() => setIsMemoryCenterOpen(false)}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              <MemoryCenter />
            </div>
          </div>
        </div>
      )}

      {/* Open & New Project Modals */}
      <OpenProjectModal
        isOpen={isOpenProjectOpen}
        onClose={() => setIsOpenProjectOpen(false)}
        onProjectOpened={handleProjectLoaded}
      />

      <NewProjectModal
        isOpen={isNewProjectOpen}
        onClose={() => setIsNewProjectOpen(false)}
        onProjectCreated={handleProjectLoaded}
      />
    </div>
  );
}
