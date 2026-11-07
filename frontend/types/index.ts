export interface Conversation {
  id: string;
  title: string;
  mode: "assistant" | "developer" | "computer";
  project_id?: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id?: string;
  conversation_id?: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  thought_process?: string;
  model_used?: string;
  created_at?: string;
}

export interface TaskStep {
  step_id: number;
  title: string;
  description: string;
  tool?: string;
  parameters?: Record<string, any>;
  status: "pending" | "in_progress" | "completed" | "failed" | "skipped";
  result?: string;
  error?: string;
}

export interface TaskPlan {
  objective: string;
  analysis: string;
  estimated_steps: number;
  steps: TaskStep[];
}

export interface AgentTask {
  id: string;
  prompt: string;
  workspace_path: string;
  status: "queued" | "planning" | "executing" | "evaluating" | "fixing" | "verified" | "completed" | "failed" | "cancelled";
  plan?: TaskPlan;
  current_step_index: number;
  result_summary?: string;
  verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceFile {
  name: string;
  path: string;
  is_dir: boolean;
  size?: number;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  platform: {
    system: string;
    python_version: string;
    cpu_cores: number;
  };
  database: {
    status: string;
    database: string;
    is_mock: boolean;
    latency_ms?: number;
  };
  inference_engine: {
    status: string;
    base_url: string;
    model_count: number;
    models: string[];
  };
  local_agent: {
    status: string;
    authorized_workspace: string;
  };
}

