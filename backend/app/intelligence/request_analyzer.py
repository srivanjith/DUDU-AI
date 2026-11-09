"""
DODO Request Analyzer
Inspects incoming autonomous task requests, extracts architecture requirements,
detects missing dependencies, and evaluates operational risk and complexity.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzedRequirement(BaseModel):
    category: str  # "frontend" | "backend" | "database" | "testing" | "infrastructure"
    technology: str
    description: str
    is_explicit: bool = True


class RequestAnalysisResult(BaseModel):
    prompt: str
    objective: str
    domain: str  # e.g., "web_application", "cli_tool", "api_service", "script"
    tech_stack: List[str] = Field(default_factory=list)
    requirements: List[AnalyzedRequirement] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    complexity_score: int = 1  # 1 (simple) to 5 (enterprise complex)
    risk_level: str = "low"  # low, medium, high, critical
    approval_required: bool = False
    estimated_steps: int = 5
    summary: str


class RequestAnalyzer:
    """
    Performs deterministic and structured decomposition of user project requirements.
    Identifies architectural components, missing requirements, and risk factors.
    """

    TECH_PATTERNS = {
        "frontend": ["react", "next.js", "vue", "svelte", "tailwind", "html", "css", "vite", "typescript"],
        "backend": ["fastapi", "python", "flask", "django", "express", "node.js", "go", "rust"],
        "database": ["mongodb", "postgresql", "postgres", "sqlite", "redis", "mysql"],
        "testing": ["pytest", "jest", "vitest", "playwright", "unittest"],
    }

    RISK_PATTERNS = {
        "high": ["delete", "drop database", "rm -rf", "format", "overwrite everything", "production deploy"],
        "medium": ["execute", "install", "terminal", "migration", "npm install", "pip install"],
        "low": ["plan", "analyze", "inspect", "read", "design", "scaffold", "structure"]
    }

    def analyze(self, prompt: str) -> RequestAnalysisResult:
        prompt_lower = prompt.lower()

        # 1. Detect Technologies
        detected_tech = []
        requirements = []

        for category, keywords in self.TECH_PATTERNS.items():
            for kw in keywords:
                if kw in prompt_lower:
                    detected_tech.append(kw)
                    requirements.append(
                        AnalyzedRequirement(
                            category=category,
                            technology=kw,
                            description=f"Include {kw} for {category} architecture.",
                            is_explicit=True
                        )
                    )

        # 2. Detect Implied Missing Requirements
        missing = []
        has_frontend = any(r.category == "frontend" for r in requirements)
        has_backend = any(r.category == "backend" for r in requirements)
        has_db = any(r.category == "database" for r in requirements)
        has_tests = any(r.category == "testing" for r in requirements)

        if has_frontend and not has_backend:
            missing.append("No backend API technology explicitly specified (implied: FastAPI or Node.js).")
        if (has_frontend or has_backend) and not has_db:
            missing.append("No persistence database layer explicitly specified (implied: MongoDB or SQLite).")
        if not has_tests:
            missing.append("Test verification framework not specified (recommended: pytest for backend, Playwright for E2E).")

        # 3. Required Capabilities
        capabilities = ["READ"]
        if "plan" in prompt_lower or "design" in prompt_lower:
            capabilities.append("ARCHITECTURE_PLANNING")
        if has_frontend or has_backend:
            capabilities.append("CODE_STRUCTURE_DESIGN")
        if has_db:
            capabilities.append("SCHEMA_DESIGN")
        capabilities.append("SIMULATION_VERIFICATION")

        # 4. Complexity & Risk Evaluation
        complexity = min(5, max(1, len(detected_tech) + (2 if has_db else 0)))

        risk = "low"
        approval = False
        if any(h in prompt_lower for h in self.RISK_PATTERNS["high"]):
            risk = "critical"
            approval = True
        elif any(m in prompt_lower for m in self.RISK_PATTERNS["medium"]):
            risk = "medium"
            approval = True
        elif complexity >= 4:
            risk = "medium"

        # 5. Objective Extraction
        objective = prompt.strip()
        if len(objective) > 120:
            objective = objective[:117] + "..."

        domain = "web_application" if (has_frontend or has_backend) else "general_software"

        summary = (
            f"Objective: '{objective}'. Detected {len(detected_tech)} stack technologies "
            f"({', '.join(detected_tech) if detected_tech else 'standard'}). "
            f"Complexity level: {complexity}/5. Risk: {risk.upper()}."
        )

        return RequestAnalysisResult(
            prompt=prompt,
            objective=objective,
            domain=domain,
            tech_stack=list(set(detected_tech)),
            requirements=requirements,
            missing_requirements=missing,
            required_capabilities=capabilities,
            complexity_score=complexity,
            risk_level=risk,
            approval_required=approval,
            estimated_steps=max(5, complexity * 2),
            summary=summary,
        )


request_analyzer = RequestAnalyzer()

