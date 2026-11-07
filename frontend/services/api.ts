const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchConversations() {
  const res = await fetch(`${API_BASE}/conversations`);
  return res.json();
}

export async function createConversation(title: string, mode: string = "assistant") {
  const res = await fetch(`${API_BASE}/conversations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, mode }),
  });
  return res.json();
}

export async function fetchConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`);
  return res.json();
}

export async function deleteConversation(id: string) {
  const res = await fetch(`${API_BASE}/conversations/${id}`, { method: "DELETE" });
  return res.json();
}

export async function fetchTasks() {
  const res = await fetch(`${API_BASE}/tasks`);
  return res.json();
}

export async function createTask(prompt: string, mode: string = "developer") {
  const res = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, mode }),
  });
  return res.json();
}

export async function fetchTask(id: string) {
  const res = await fetch(`${API_BASE}/tasks/${id}`);
  return res.json();
}

export async function cancelTask(id: string) {
  const res = await fetch(`${API_BASE}/tasks/${id}/cancel`, { method: "POST" });
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

export async function executeTerminalCommand(command: string) {
  const res = await fetch(`${API_BASE}/terminal/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command }),
  });
  return res.json();
}

export async function fetchModels() {
  const res = await fetch(`${API_BASE}/models`);
  return res.json();
}

export function streamChatMessage(
  conversationId: string,
  content: string,
  model: string,
  onToken: (token: string, model: string) => void,
  onComplete: () => void,
  onError: (err: any) => void
) {
  fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, model }),
  })
    .then(async (response) => {
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

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
              if (data.token) {
                onToken(data.token, data.model);
              }
              if (data.done) {
                onComplete();
                return;
              }
            } catch (e) {
              // ignore parse errors for partial chunks
            }
          }
        }
      }
      onComplete();
    })
    .catch((err) => {
      onError(err);
    });
}

