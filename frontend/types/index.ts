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
  status: "pending" | "awaiting_approval" | "in_progress" | "completed" | "failed" | "skipped";
  result?: string;
  error?: string;
  dependencies?: number[];
  expected_outcomes?: string[];
  required_capabilities?: string[];
  risk_level?: string;
  approval_required?: boolean;
  permission_level?: string;
}

export interface TaskPlan {
  task_id?: string;
  user_request?: string;
  objective: string;
  analysis: string;
  tech_stack?: string[];
  complexity_score?: number;
  risk_level?: string;
  approval_required?: boolean;
  required_capabilities?: string[];
  estimated_steps: number;
  steps: TaskStep[];
}

export interface ExecutionEvent {
  event_id: string;
  timestamp: string;
  type: string;
  phase: string;
  message: string;
  details?: Record<string, any>;
}

export interface ApprovalRequest {
  approval_id: string;
  task_id: string;
  step_id: number;
  tool_name: string;
  permission_level: string;
  risk_level: string;
  description: string;
  parameters?: Record<string, any>;
  status: "pending" | "approved" | "rejected";
}

export interface AgentTask {
  id: string;
  prompt: string;
  workspace_path: string;
  status: "queued" | "planning" | "planned" | "awaiting_approval" | "executing" | "observing" | "evaluating" | "fixing" | "verified" | "completed" | "failed" | "cancelled";
  plan?: TaskPlan;
  current_step_index: number;
  result_summary?: string;
  verified: boolean;
  pending_approval?: ApprovalRequest | null;
  events?: ExecutionEvent[];
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

