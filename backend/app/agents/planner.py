"""
DODO Task Planner
Converts complex user development requests into structured, actionable plans.
Leverages RequestAnalyzer and TaskDecomposer to produce dependency-mapped,
permission-tagged execution steps.
"""
from typing import Any, Dict, List, Optional
from backend.app.agents.task_decomposer import task_decomposer
from backend.app.intelligence.context_manager import context_manager
from backend.app.intelligence.request_analyzer import request_analyzer
from backend.app.models.schemas import TaskPlan, TaskStep


class TaskPlanner:
    """
    Intelligent planner that breaks high-level development requests
    into discrete, ordered, capability-tagged steps.
    Never exposes hidden chain-of-thought; outputs concise actionable plans only.
    """

    def generate_plan(
        self,
        prompt: str,
        workspace_path: str,
        task_id: Optional[str] = None
    ) -> TaskPlan:
        # 1. Sanitize & Analyze Request
        clean_prompt = context_manager.sanitize_input(prompt)
        analysis = request_analyzer.analyze(clean_prompt)

        # 2. Decompose into structured steps
        decomposed = task_decomposer.decompose(clean_prompt, analysis)

        # Convert to TaskStep schemas
        plan_steps = [
            TaskStep(
                step_id=s.step_id,
                title=s.title,
                description=s.description,
                tool=s.tool,
                parameters=s.parameters,
                dependencies=s.dependencies,
                expected_outcomes=s.expected_outcomes,
                required_capabilities=s.required_capabilities,
                risk_level=s.risk_level,
                approval_required=s.approval_required,
                permission_level=s.permission_level,
            )
            for s in decomposed
        ]

        # 3. Assemble Structured Plan
        plan = TaskPlan(
            task_id=task_id,
            user_request=clean_prompt,
            objective=analysis.objective,
            analysis=analysis.summary,
            tech_stack=analysis.tech_stack,
            complexity_score=analysis.complexity_score,
            risk_level=analysis.risk_level,
            approval_required=analysis.approval_required or any(s.approval_required for s in plan_steps),
            required_capabilities=analysis.required_capabilities,
            estimated_steps=len(plan_steps),
            steps=plan_steps,
        )

        return plan


task_planner = TaskPlanner()
