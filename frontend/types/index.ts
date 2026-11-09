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

export interface ProjectScan {
  workspace_path: string;
  project_name: string;
  is_git_repo: boolean;
  git_branch?: string;
  git_status?: string;
  languages: Record<string, number>;
  primary_language: string;
  frameworks: string[];
  package_managers: string[];
  entry_points: string[];
  dependencies: string[];
  config_files: string[];
  test_files: string[];
  total_files: number;
  total_size_bytes: number;
  source_directories: string[];
  summary: string;
}

export interface Workspace {
  id: string;
  name: string;
  path: string;
  description?: string;
  is_default: boolean;
  scan_summary?: ProjectScan;
  created_at: string;
  updated_at: string;
}

export interface Checkpoint {
  id: string;
  workspace_id: string;
  task_id?: string;
  title: string;
  description?: string;
  file_count: number;
  created_at: string;
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
    host?: string;
    port?: number;
    active_processes_count?: number;
  };
}

export interface TerminalProcess {
  pid: number;
  execution_id: string;
  command: string;
  cwd: string;
  category: string;
  port?: number | null;
  status: "running" | "stopped" | "completed" | "failed";
  start_time: string;
  end_time?: string | null;
  exit_code?: number | null;
  log_lines_count?: number;
  recent_logs?: string[];
}

export interface TerminalAuditRecord {
  execution_id: string;
  command: string;
  category: string;
  cwd: string;
  success: boolean;
  exit_code: number;
  duration_ms: number;
  error?: string | null;
  timestamp: string;
}

export interface PendingApprovalCommand {
  execution_id: string;
  command: string;
  cwd: string;
  workspace_root?: string | null;
  category: string;
  reason: string;
  status: string;
  risk_level?: string;
}

export interface TerminalExecutionResult {
  execution_id?: string;
  command?: string;
  category?: string;
  success: boolean;
  exit_code: number;
  stdout?: string;
  stderr?: string;
  error?: string;
  duration_ms?: number;
  requires_approval?: boolean;
  reason?: string;
  risk_level?: string;
}

export interface MemoryRecord {
  id: string;
  content: string;
  category: "conversation" | "preference" | "project" | "task_experience" | "knowledge";
  project_id?: string | null;
  conversation_id?: string | null;
  importance: number;
  tags: string[];
  source?: string;
  is_verified: boolean;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  relevance_score?: number;
  match_reasons?: string[];
}


