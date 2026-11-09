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
