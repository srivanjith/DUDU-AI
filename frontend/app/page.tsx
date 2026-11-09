"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { ChatArea } from "@/components/ChatArea";
import { AgentPanel } from "@/components/AgentPanel";
import { WorkspaceEditor } from "@/components/WorkspaceEditor";
import { TerminalPanel } from "@/components/TerminalPanel";
import { BrowserPreview } from "@/components/BrowserPreview";
import { MemoryCenter } from "@/components/MemoryCenter";
import { ModelManager } from "@/components/ModelManager";
import { SettingsModal } from "@/components/SettingsModal";
import { Conversation, Message, AgentTask, SystemHealth } from "@/types";
import {
  fetchHealth,
  fetchConversations,
  createConversation,
  fetchConversation,
  deleteConversation,
  streamChatMessage,
  fetchTasks,
  createTask,
  cancelTask,
  approveTaskStep,
} from "@/services/api";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activeTab, setActiveTab] = useState<
    "chat" | "developer" | "editor" | "terminal" | "browser" | "memory" | "models" | "settings"
  >("chat");

  // Models
  const [selectedModel, setSelectedModel] = useState("auto");
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  // Streaming State
  const [isStreaming, setIsStreaming] = useState(false);
  const abortControllerRef = React.useRef<AbortController | null>(null);

  // Autonomous Tasks State
  const [tasks, setTasks] = useState<AgentTask[]>([]);
  const [activeTask, setActiveTask] = useState<AgentTask | null>(null);
  const [isExecutingTask, setIsExecutingTask] = useState(false);

  // Initial Load
  useEffect(() => {
    loadHealth();
    loadConversations();
    loadTasks();
    const interval = setInterval(loadHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    try {
      const h = await fetchHealth();
      setHealth(h);
      if (h?.inference_engine?.models) {
        setAvailableModels(h.inference_engine.models);
      }
    } catch (e) {
      console.error("Health check error", e);
    }
  };

  const loadConversations = async () => {
    try {
      const res = await fetchConversations();
      setConversations(res || []);
      if (res?.length > 0 && !activeConvId) {
        selectConversation(res[0].id);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const loadTasks = async () => {
    try {
      const res = await fetchTasks();
      setTasks(res || []);
      if (res?.length > 0 && !activeTask) {
        setActiveTask(res[0]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const selectConversation = async (id: string) => {
    setActiveConvId(id);
    try {
      const res = await fetchConversation(id);
      setMessages(res.messages || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleNewChat = async () => {
    try {
      const newConv = await createConversation("New Conversation", "assistant");
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
      setActiveTab("chat");
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteConv = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeConvId === id) {
        setActiveConvId(null);
        setMessages([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendMessage = async (content: string, model: string) => {
    let currentConvId = activeConvId;
    if (!currentConvId) {
      const newConv = await createConversation(content.slice(0, 30) + "...", "assistant");
      setConversations((prev) => [newConv, ...prev]);
      currentConvId = newConv.id;
      setActiveConvId(newConv.id);
    }

    // Append user message immediately
    const userMsg: Message = { role: "user", content, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);

    // Prepare assistant message
    const assistantMsg: Message = {
      role: "assistant",
      content: "",
      model_used: model,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, assistantMsg]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    streamChatMessage(
      currentConvId,
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
        setIsStreaming(false);
        abortControllerRef.current = null;
      },
      (err) => {
        console.error("Stream error", err);
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0) {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content: `⚠️ ${err}`,
            };
          }
          return updated;
        });
        setIsStreaming(false);
        abortControllerRef.current = null;
      },
      controller.signal
    );
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  };

  const handleCreateTask = async (prompt: string) => {
    try {
      const task = await createTask(prompt, "developer");
      setTasks((prev) => [task, ...prev]);
      setActiveTask(task);
      setIsExecutingTask(true);

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
                s.step_id === data.step_id
                  ? { ...s, status: "in_progress" }
                  : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
          } else if (data.type === "observation") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id
                  ? { ...s, result: data.observation }
                  : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
          } else if (data.type === "step_complete") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id
                  ? { ...s, status: "completed", result: data.result_preview }
                  : s
              );
              return { ...prev, plan: { ...prev.plan, steps: updatedSteps } };
            });
          } else if (data.type === "step_failed") {
            setActiveTask((prev: any) => {
              if (!prev?.plan) return prev;
              const updatedSteps = prev.plan.steps.map((s: any) =>
                s.step_id === data.step_id
                  ? { ...s, status: "failed", error: data.error }
                  : s
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
        // Re-attach stream with resume=true
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
            } else if (data.type === "task_completed") {
              setActiveTask((prev: any) => ({
                ...prev,
                status: "completed",
                verified: data.verified,
                result_summary: data.report,
              }));
              setIsExecutingTask(false);
              eventSource.close();
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
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-screen bg-slate-950 font-sans antialiased text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelectConv={selectConversation}
        onNewChat={handleNewChat}
        onDeleteConv={handleDeleteConv}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        health={health}
      />

      {/* Main Content Area Based on Active Tab */}
      <main className="flex-1 flex overflow-hidden">
        {activeTab === "chat" && (
          <ChatArea
            messages={messages}
            onSendMessage={handleSendMessage}
            isStreaming={isStreaming}
            onStopStreaming={handleStopStreaming}
            selectedModel={selectedModel}
            onSelectModel={setSelectedModel}
            availableModels={availableModels}
            ollamaStatus={health?.inference_engine}
          />
        )}

        {activeTab === "developer" && (
          <AgentPanel
            tasks={tasks}
            activeTask={activeTask}
            onSelectTask={setActiveTask}
            onCreateTask={handleCreateTask}
            onCancelTask={handleCancelTask}
            onApproveStep={handleApproveStep}
            isExecuting={isExecutingTask}
          />
        )}

        {activeTab === "editor" && <WorkspaceEditor />}
        {activeTab === "terminal" && <TerminalPanel />}
        {activeTab === "browser" && <BrowserPreview />}
        {activeTab === "memory" && <MemoryCenter />}
        {activeTab === "models" && <ModelManager />}
        {activeTab === "settings" && <SettingsModal health={health} />}
      </main>
    </div>
  );
}

