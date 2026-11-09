"""
DODO Task Decomposer
Decomposes high-level autonomous requests into sequential, dependency-aware,
and permission-tagged execution steps.
"""
from typing import Any, Dict, List, Optional
from backend.app.intelligence.request_analyzer import RequestAnalysisResult, request_analyzer
from backend.app.models.schemas import TaskStep
from backend.app.tools.registry import PermissionLevel, RiskLevel


class DecomposedStep(TaskStep):
    dependencies: List[int] = []
    expected_outcomes: List[str] = []
    required_capabilities: List[str] = []
    risk_level: str = "low"
    approval_required: bool = False
    permission_level: str = "READ"


class TaskDecomposer:
    """
    Decomposes development and engineering tasks into ordered, actionable steps.
    For Phase 3, all steps operate in controlled planning and simulation mode
    without modifying real files or executing arbitrary terminal commands.
    """

    def decompose(self, prompt: str, analysis: Optional[RequestAnalysisResult] = None) -> List[DecomposedStep]:
        if not analysis:
            analysis = request_analyzer.analyze(prompt)

        prompt_lower = prompt.lower()
        tech_stack = analysis.tech_stack or ["React", "FastAPI", "MongoDB"]
        tech_str = ", ".join(tech_stack)

        # Check if this is a Phase 5 Terminal Testing & Execution task
        is_terminal_testing = (
            ("test" in prompt_lower or "pytest" in prompt_lower or "terminal" in prompt_lower)
            and any(w in prompt_lower for w in ["run", "execute", "check", "verify", "suite"])
            and not any(w in prompt_lower for w in ["create a simple python task", "build a task app from scratch"])
        )

        if is_terminal_testing:
            return [
                DecomposedStep(
                    step_id=1,
                    title="PLAN: Inspect Workspace & Discover Test Files",
                    description="Inspect registered project workspace directory to locate test suites and configuration files.",
                    dependencies=[],
                    expected_outcomes=["Workspace layout and test files discovered."],
                    required_capabilities=["READ", "WORKSPACE_INSPECTION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="list_workspace_files",
                    parameters={"subpath": "", "depth": 2},
                ),
                DecomposedStep(
                    step_id=2,
                    title="INSPECT: Analyze Test Suite & Dependency Requirements",
                    description="Read test_tasks.py, verify imports, and detect required test runner dependencies (pytest).",
                    dependencies=[1],
                    expected_outcomes=["Test specifications inspected and dependency requirements analyzed."],
                    required_capabilities=["READ", "DEPENDENCY_ANALYSIS"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="read_file",
                    parameters={"path": "test_tasks.py"},
                ),
                DecomposedStep(
                    step_id=3,
                    title="REQUEST APPROVAL: Verify & Request Approval for Dependencies",
                    description="Explain dependency requirements to user and request approval before running dependency installation.",
                    dependencies=[2],
                    expected_outcomes=["User presented with dependency justification and explicit approval request."],
                    required_capabilities=["DEPENDENCY_INSTALL", "APPROVAL_GATING"],
                    risk_level=RiskLevel.HIGH.value,
                    approval_required=True,
                    permission_level="DEPENDENCY_INSTALL",
                    tool="execute_terminal_command",
                    parameters={"command": "python -m pip install pytest", "timeout_seconds": 60},
                ),
                DecomposedStep(
                    step_id=4,
                    title="EXECUTE: Execute Test Suite via Local Agent",
                    description="Execute python -m pytest test_tasks.py -v inside the authorized workspace via the authenticated Local Agent.",
                    dependencies=[3],
                    expected_outcomes=["Real terminal execution initiated and real-time stdout/stderr streamed."],
                    required_capabilities=["TEST", "REAL_TERMINAL_EXECUTION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="execute_terminal_command",
                    parameters={"command": "python -m pytest test_tasks.py -v", "timeout_seconds": 60},
                ),
                DecomposedStep(
                    step_id=5,
                    title="OBSERVE: Capture Real Terminal stdout/stderr & Exit Code",
                    description="Observe real process exit code, assertion failures, or passing indicators directly from process output.",
                    dependencies=[4],
                    expected_outcomes=["Terminal output and exit code captured without fabrication."],
                    required_capabilities=["READ", "EXECUTION_OBSERVATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=6,
                    title="EVALUATE: Evaluate Test Assertions & Diagnose Execution Failures",
                    description="Analyze test results, stack traces, and verify whether all CRUD operations succeeded or if fixes are required.",
                    dependencies=[5],
                    expected_outcomes=["Root cause analysis of test outcome documented."],
                    required_capabilities=["EVALUATION", "ROOT_CAUSE_ANALYSIS"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=7,
                    title="FIX: Formulate & Verify Corrections",
                    description="Propose and validate code changes if test failures were identified.",
                    dependencies=[6],
                    expected_outcomes=["Remediation diffs validated or confirmation that all tests already pass."],
                    required_capabilities=["WRITE", "DIFF_GENERATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=8,
                    title="VERIFY: Re-run Test Suite to Verify Complete Passing Status",
                    description="Execute final regression verification run of python -m pytest test_tasks.py -v.",
                    dependencies=[7],
                    expected_outcomes=["All test assertions confirmed passing with exit code 0."],
                    required_capabilities=["TEST", "VERIFICATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="execute_terminal_command",
                    parameters={"command": "python -m pytest test_tasks.py -v", "timeout_seconds": 60},
                ),
                DecomposedStep(
                    step_id=9,
                    title="DELIVER: Synthesize Verified Test Execution Results & Publish Delivery Report",
                    description="Compile verified terminal output, execution timestamps, duration, and final delivery report.",
                    dependencies=[8],
                    expected_outcomes=["Phase 5 acceptance demonstration report published."],
                    required_capabilities=["REPORTING"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
            ]

        # Check if this is a real autonomous coding execution task (Phase 4 Spec)
        is_coding_implementation = (
            any(w in prompt_lower for w in ["create", "build", "implement", "add, view", "crud"])
            and not prompt_lower.startswith("plan ")
            and ("task" in prompt_lower or "python" in prompt_lower or "app" in prompt_lower)
        )

        if is_coding_implementation:
            from backend.app.intelligence.code_generator import code_generator
            app_files = code_generator.get_task_app_files()
            task_manager_code = app_files.get("task_manager.py", "")
            cli_code = app_files.get("main.py", "")
            test_code = app_files.get("test_tasks.py", "")

            return [
                DecomposedStep(
                    step_id=1,
                    title="Scan Workspace Environment",
                    description="Inspect existing project directory, detect conflicts and project layout.",
                    dependencies=[],
                    expected_outcomes=["Workspace directory structure and existing files mapped."],
                    required_capabilities=["READ", "WORKSPACE_INSPECTION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="list_workspace_files",
                    parameters={"subpath": "", "depth": 2},
                ),
                DecomposedStep(
                    step_id=2,
                    title="Analyze Project Architecture & Data Models",
                    description="Formulate Task dataclass, JSON persistence schema, and CRUD interface.",
                    dependencies=[1],
                    expected_outcomes=["Data model schemas and CRUD interface specifications finalized."],
                    required_capabilities=["ARCHITECTURE_PLANNING"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=3,
                    title="Plan Code Changes & Generate Diffs",
                    description="Prepare proposed code changes and unified diffs for review.",
                    dependencies=[2],
                    expected_outcomes=["Unified diffs and Python syntax validated for all proposed files."],
                    required_capabilities=["READ", "DIFF_GENERATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=4,
                    title="Apply Core TaskManager Logic",
                    description="Create or update task_manager.py with Task dataclass and JSON persistence.",
                    dependencies=[3],
                    expected_outcomes=["task_manager.py created on disk with valid syntax and hash verified."],
                    required_capabilities=["WRITE", "ATOMIC_FILE_WRITE"],
                    risk_level=RiskLevel.MEDIUM.value,
                    approval_required=True,
                    permission_level=PermissionLevel.WRITE.value,
                    tool="write_file",
                    parameters={"path": "task_manager.py", "content": task_manager_code, "overwrite": True},
                ),
                DecomposedStep(
                    step_id=5,
                    title="Apply CLI Entry Point",
                    description="Create or update main.py for command-line task operations.",
                    dependencies=[4],
                    expected_outcomes=["main.py CLI entrypoint created on disk."],
                    required_capabilities=["WRITE", "ATOMIC_FILE_WRITE"],
                    risk_level=RiskLevel.MEDIUM.value,
                    approval_required=True,
                    permission_level=PermissionLevel.WRITE.value,
                    tool="write_file",
                    parameters={"path": "main.py", "content": cli_code, "overwrite": True},
                ),
                DecomposedStep(
                    step_id=6,
                    title="Apply Automated Test Suite",
                    description="Create test_tasks.py for Pytest CRUD verification.",
                    dependencies=[5],
                    expected_outcomes=["test_tasks.py test suite created on disk."],
                    required_capabilities=["WRITE", "ATOMIC_FILE_WRITE"],
                    risk_level=RiskLevel.MEDIUM.value,
                    approval_required=True,
                    permission_level=PermissionLevel.WRITE.value,
                    tool="write_file",
                    parameters={"path": "test_tasks.py", "content": test_code, "overwrite": True},
                ),
                DecomposedStep(
                    step_id=7,
                    title="Read Back & Verify File Integrity",
                    description="Read back modified files from disk, verify SHA-256 hashes and syntax.",
                    dependencies=[6],
                    expected_outcomes=["All written files read back from disk and verified non-empty."],
                    required_capabilities=["READ", "INTEGRITY_VERIFICATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool="read_file",
                    parameters={"path": "task_manager.py"},
                ),
                DecomposedStep(
                    step_id=8,
                    title="Evaluate Results & Safety Compliance",
                    description="Verify all CRUD requirements, permissions, and non-destructive checks.",
                    dependencies=[7],
                    expected_outcomes=["All acceptance criteria verified against security policies."],
                    required_capabilities=["EVALUATION"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
                DecomposedStep(
                    step_id=9,
                    title="Prepare Final Delivery Report",
                    description="Synthesize file manifests, hashes, and implementation summary.",
                    dependencies=[8],
                    expected_outcomes=["Final verified completion report published."],
                    required_capabilities=["REPORTING"],
                    risk_level=RiskLevel.LOW.value,
                    approval_required=False,
                    permission_level=PermissionLevel.READ.value,
                    tool=None,
                    parameters={},
                ),
            ]

        # Standard 9-Stage Autonomous Lifecycle Decomposition (Phase 3 Spec)
        steps = [
            DecomposedStep(
                step_id=1,
                title="Analyze Requirements & Constraints",
                description=f"Inspect project specifications, objectives, and dependencies ({tech_str}).",
                dependencies=[],
                expected_outcomes=[
                    "Formal technical specification documented.",
                    "Identified dependencies and runtime constraints."
                ],
                required_capabilities=["READ", "REQUIREMENTS_ANALYSIS"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool="list_workspace_files",
                parameters={"subpath": "", "depth": 2},
            ),
            DecomposedStep(
                step_id=2,
                title="Identify Application Architecture",
                description=f"Design modular service architecture, components, and data flow for {tech_str}.",
                dependencies=[1],
                expected_outcomes=[
                    "Architectural blueprints and component hierarchy established.",
                    "API contracts and REST route schema planned."
                ],
                required_capabilities=["ARCHITECTURE_PLANNING"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=3,
                title="Prepare Project Structure & Scaffolding Plan",
                description="Formulate directory structure and file layout for frontend, backend, and database.",
                dependencies=[2],
                expected_outcomes=[
                    "Clean directory hierarchy mapped out.",
                    "Scaffolding configuration validated."
                ],
                required_capabilities=["WRITE", "SCAFFOLDING_DESIGN"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=4,
                title="Design Frontend Components",
                description=f"Structure UI layout, state management, and user interaction components ({', '.join([t for t in tech_stack if t in ['react', 'next.js', 'vue', 'tailwind']]) or 'React'}).",
                dependencies=[3],
                expected_outcomes=[
                    "Frontend component tree and props interface designed.",
                    "State management and API consumption hooks mapped."
                ],
                required_capabilities=["UI_DESIGN", "CODE_STRUCTURE_DESIGN"],
                risk_level=RiskLevel.MEDIUM.value,
                approval_required=True,  # Phase 3 approval gate demonstration
                permission_level=PermissionLevel.WRITE.value,
                tool="write_file",
                parameters={"path": "frontend_plan.json", "simulated": True},
            ),
            DecomposedStep(
                step_id=5,
                title="Design Backend API & Business Logic",
                description=f"Plan REST API endpoints, Pydantic validation schemas, and service logic ({', '.join([t for t in tech_stack if t in ['fastapi', 'python', 'flask']]) or 'FastAPI'}).",
                dependencies=[4],
                expected_outcomes=[
                    "API routes, CRUD operations, and error handlers modeled.",
                    "Input validation models formalized."
                ],
                required_capabilities=["API_DESIGN", "CODE_STRUCTURE_DESIGN"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=6,
                title="Integrate Database Schema & Repositories",
                description=f"Formulate database schemas, indexes, and persistence queries ({', '.join([t for t in tech_stack if t in ['mongodb', 'postgres', 'sqlite']]) or 'MongoDB'}).",
                dependencies=[5],
                expected_outcomes=[
                    "Collections, documents, and relationship schemas planned.",
                    "Database connection and fallback mechanisms structured."
                ],
                required_capabilities=["SCHEMA_DESIGN"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=7,
                title="Formulate Test & Verification Strategy",
                description="Specify automated test suites (unit, integration, and E2E verification).",
                dependencies=[6],
                expected_outcomes=[
                    "Pytest test cases and acceptance criteria defined.",
                    "Verification checkpoints and assertions prepared."
                ],
                required_capabilities=["TEST_DESIGN", "SIMULATION_VERIFICATION"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=8,
                title="Evaluate Results & Safety Compliance",
                description="Perform automated safety audit, verify permission compliance, and evaluate completeness.",
                dependencies=[7],
                expected_outcomes=[
                    "All plan constraints verified against security rules.",
                    "Verification score evaluated."
                ],
                required_capabilities=["EVALUATION", "SECURITY_AUDIT"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
            DecomposedStep(
                step_id=9,
                title="Prepare Final Delivery Report",
                description="Synthesize technical architecture, verified artifacts, and implementation summary.",
                dependencies=[8],
                expected_outcomes=[
                    "Comprehensive task completion report generated.",
                    "Ready for user review and Phase 4 execution approval."
                ],
                required_capabilities=["REPORTING"],
                risk_level=RiskLevel.LOW.value,
                approval_required=False,
                permission_level=PermissionLevel.READ.value,
                tool=None,
                parameters={},
            ),
        ]

        return steps


task_decomposer = TaskDecomposer()
