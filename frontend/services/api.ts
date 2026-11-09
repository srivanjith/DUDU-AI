const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function fetchConversations(skip = 0, limit = 50) {
  const res = await fetch(`${API_BASE}/api/conversations?skip=${skip}&limit=${limit}`);
  return res.json();
}

export async function createConversation(title: string, mode: string = "assistant") {
  const res = await fetch(`${API_BASE}/api/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, mode }),
  });
  return res.json();
}

export async function fetchConversation(id: string, skip = 0, limit = 100) {
  const res = await fetch(`${API_BASE}/api/conversations/${id}?skip=${skip}&limit=${limit}`);
  return res.json();
}

export async function deleteConversation(id: string) {
  const res = await fetch(`${API_BASE}/api/conversations/${id}`, { method: "DELETE" });
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/api/models`);
  return res.json();
}

export async function fetchModelsStatus() {
  const res = await fetch(`${API_BASE}/api/models/status`);
  return res.json();
}

export async function setModelRole(role: string, model_name: string) {
  const res = await fetch(`${API_BASE}/api/models/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role, model_name }),
  });
  return res.json();
}

export async function fetchTasks() {
  const res = await fetch(`${API_BASE}/api/agent/tasks`);
  return res.json();
}

export async function createTask(prompt: string, mode: string = "developer") {
  const res = await fetch(`${API_BASE}/api/agent/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, mode }),
  });
  return res.json();
}

export async function fetchTask(id: string) {
  const res = await fetch(`${API_BASE}/api/agent/tasks/${id}`);
  return res.json();
}

export async function startTask(id: string) {
  const res = await fetch(`${API_BASE}/api/agent/tasks/${id}/start`, { method: "POST" });
  return res.json();
}

export async function cancelTask(id: string) {
  const res = await fetch(`${API_BASE}/api/agent/tasks/${id}/cancel`, { method: "POST" });
  return res.json();
}

export async function fetchTaskEvents(id: string) {
  const res = await fetch(`${API_BASE}/api/agent/tasks/${id}/events`);
  return res.json();
}

export async function approveTaskStep(id: string, stepId: number, approved: boolean = true, comment?: string) {
  const res = await fetch(`${API_BASE}/api/agent/tasks/${id}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ step_id: stepId, approved, comment }),
  });
  return res.json();
}

export async function fetchWorkspaces() {
  const res = await fetch(`${API_BASE}/api/workspaces`);
  return res.json();
}

export async function registerWorkspace(name: string, path: string, description: string = "", is_default: boolean = false) {
  const res = await fetch(`${API_BASE}/api/workspaces`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, path, description, is_default }),
  });
  return res.json();
}

export async function fetchWorkspace(id: string) {
  const res = await fetch(`${API_BASE}/api/workspaces/${id}`);
  return res.json();
}

export async function scanWorkspace(id: string) {
  const res = await fetch(`${API_BASE}/api/workspaces/${id}/scan`);
  return res.json();
}

export async function deleteWorkspace(id: string) {
  const res = await fetch(`${API_BASE}/api/workspaces/${id}`, { method: "DELETE" });
  return res.json();
}

export async function fetchWorkspaceStatus() {
  const res = await fetch(`${API_BASE}/api/workspace/status`);
  return res.json();
}

export async function previewDiff(path: string, proposed_content: string) {
  const res = await fetch(`${API_BASE}/api/workspace/preview-diff`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, proposed_content }),
  });
  return res.json();
}

export async function searchWorkspace(query: string, subpath: string = "") {
  const res = await fetch(`${API_BASE}/api/workspace/search?query=${encodeURIComponent(query)}&subpath=${encodeURIComponent(subpath)}`);
  return res.json();
}

export async function fetchCheckpoints(workspacePath?: string) {
  const url = workspacePath
    ? `${API_BASE}/api/workspace/checkpoints?workspace_path=${encodeURIComponent(workspacePath)}`
    : `${API_BASE}/api/workspace/checkpoints`;
  const res = await fetch(url);
  return res.json();
}

export async function rollbackCheckpoint(checkpointId: string, workspacePath?: string) {
  const url = workspacePath
    ? `${API_BASE}/api/workspace/checkpoints/${checkpointId}/rollback?workspace_path=${encodeURIComponent(workspacePath)}`
    : `${API_BASE}/api/workspace/checkpoints/${checkpointId}/rollback`;
  const res = await fetch(url, { method: "POST" });
  return res.json();
}

export async function fetchWorkspaceFiles() {
  const res = await fetch(`${API_BASE}/workspace/files`);
  return res.json();
}

export async function fetchFileContent(path: string) {
  const res = await fetch(`${API_BASE}/workspace/file?path=${encodeURIComponent(path)}`);
  return res.json();
}

export async function saveWorkspaceFile(path: string, content: string) {
  const res = await fetch(`${API_BASE}/workspace/file`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path, content, overwrite: true }),
  });
  return res.json();
}

export async function executeTerminalCommand(
  command: string,
  cwd: string = "",
  timeout_seconds: number = 60,
  approved: boolean = false,
  is_dev_server: boolean = false,
  workspace_root?: string
) {
  const res = await fetch(`${API_BASE}/api/terminal/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      command,
      cwd,
      timeout_seconds,
      approved,
      is_dev_server,
      workspace_root,
    }),
  });
  return res.json();
}

export async function fetchLocalAgentStatus() {
  const res = await fetch(`${API_BASE}/api/terminal/agent/status`);
  return res.json();
}

export async function fetchTerminalProcesses() {
  const res = await fetch(`${API_BASE}/api/terminal/processes?active_only=true`);
  return res.json();
}

export async function killTerminalProcess(pid: number) {
  const res = await fetch(`${API_BASE}/api/terminal/processes/${pid}/kill`, {
    method: "POST",
  });
  return res.json();
}

export async function fetchTerminalHistory(limit: number = 50) {
  const res = await fetch(`${API_BASE}/api/terminal/history?limit=${limit}`);
  return res.json();
}

export async function fetchPendingApprovals() {
  const res = await fetch(`${API_BASE}/api/terminal/pending-approvals`);
  return res.json();
}

export async function approveTerminalCommand(executionId: string) {
  const res = await fetch(`${API_BASE}/api/terminal/approve/${executionId}`, {
    method: "POST",
  });
  return res.json();
}

export async function cancelTerminalCommand(executionId: string) {
  const res = await fetch(`${API_BASE}/api/terminal/cancel/${executionId}`, {
    method: "POST",
  });
  return res.json();
}

export function streamChatMessage(
  conversationId: string,
  content: string,
  model: string,
  onToken: (token: string, model: string) => void,
  onComplete: () => void,
  onError: (err: any) => void,
  signal?: AbortSignal
) {
  fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      message: content,
      model: model,
    }),
    signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const errorText = await response.text();
        onError(errorText || `HTTP ${response.status}`);
        return;
      }
      if (!response.body) {
        onComplete();
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.substring(6));
                if (data.type === "token" && data.token) {
                  onToken(data.token, data.model || model);
                } else if (data.type === "error") {
                  onError(data.error);
                  return;
                } else if (data.type === "done") {
                  onComplete();
                  return;
                }
              } catch (e) {
                // Ignore json parse error on partial chunks
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === "AbortError") {
          console.log("Stream aborted by user");
        } else {
          onError(err);
        }
      }
      onComplete();
    })
    .catch((err) => {
      if (err.name === "AbortError") {
        console.log("Stream aborted by user");
        onComplete();
      } else {
        onError(err);
      }
    });
}

// ==============================================================================
// Memory Center API Services (Phase 7)
// ==============================================================================

export async function fetchMemories(category?: string, projectId?: string, q?: string, limit = 50) {
  const params = new URLSearchParams();
  if (category) params.append("category", category);
  if (projectId) params.append("project_id", projectId);
  if (q) params.append("q", q);
  params.append("limit", limit.toString());
  const res = await fetch(`${API_BASE}/api/memory?${params.toString()}`);
  return res.json();
}

export async function fetchMemoryCategories() {
  const res = await fetch(`${API_BASE}/api/memory/categories`);
  return res.json();
}

export async function fetchMemoryProjects() {
  const res = await fetch(`${API_BASE}/api/memory/projects`);
  return res.json();
}

export async function createMemory(data: {
  content: string;
  category?: string;
  project_id?: string;
  importance?: number;
  tags?: string[];
}) {
  const res = await fetch(`${API_BASE}/api/memory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function updateMemory(id: string, data: {
  content?: string;
  category?: string;
  project_id?: string;
  importance?: number;
  tags?: string[];
}) {
  const res = await fetch(`${API_BASE}/api/memory/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteMemory(id: string) {
  const res = await fetch(`${API_BASE}/api/memory/${id}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function clearProjectMemories(projectId: string) {
  const res = await fetch(`${API_BASE}/api/memory/project/${projectId}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function clearAllMemories() {
  const res = await fetch(`${API_BASE}/api/memory/clear?confirm=true`, {
    method: "DELETE",
  });
  return res.json();
}

export async function searchMemories(query: string, category?: string, projectId?: string) {
  const res = await fetch(`${API_BASE}/api/memory/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, category, project_id: projectId }),
  });
  return res.json();
}
