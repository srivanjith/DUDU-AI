"""
DODO Intent Classifier
Classifies incoming user prompts into high-level operational intents.
Preserves local-first privacy with rule-based heuristics and local model routing.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class UserIntent(str, Enum):
    GENERAL_CONVERSATION = "general_conversation"
    CODING_ASSISTANCE = "coding_assistance"
    PROJECT_CREATION = "project_creation"
    PROJECT_MODIFICATION = "project_modification"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    FILE_RELATED = "file_related"
    MULTI_STEP_AUTONOMOUS = "multi_step_autonomous"


class IntentClassificationResult(BaseModel):
    intent: UserIntent
    confidence: float
    is_autonomous_task: bool
    requires_planning: bool
    detected_keywords: List[str]
    suggested_mode: str  # "assistant" | "developer" | "browser"
    reasoning: str


class IntentClassifier:
    """
    Classifies user requests into structured intents to route between
    conversational assistance, code generation, and multi-step autonomous planning.
    """

    # Keyword indicators for deterministic, zero-latency classification
    AUTONOMOUS_KEYWORDS = [
        "build a", "create a", "develop a", "implement a", "scaffold a",
        "full-stack", "full stack", "end to end", "end-to-end", "architecture",
        "plan a", "plan and build", "multi-step", "autonomous", "pipeline"
    ]

    PROJECT_CREATION_KEYWORDS = [
        "new project", "create project", "initialize project", "scaffold",
        "start a project", "setup app", "setup application", "boilerplate"
    ]

    PROJECT_MODIFICATION_KEYWORDS = [
        "add feature", "refactor", "modify", "update project", "integrate",
        "upgrade dependency", "change architecture", "migrate"
    ]

    DEBUGGING_KEYWORDS = [
        "error", "bug", "traceback", "exception", "failed", "fix this",
        "debug", "crash", "syntaxerror", "typeerror", "connection refused",
        "issue", "not working", "broken"
    ]

    CODING_KEYWORDS = [
        "write code", "function", "class", "algorithm", "python", "typescript",
        "javascript", "react", "fastapi", "html", "css", "sql", "regex",
        "snippet", "how to write", "how to implement", "generate code"
    ]

    FILE_KEYWORDS = [
        "read file", "write file", "save file", "list directory", "delete file",
        "edit file", "file structure", "folder", "directory", "inspect file"
    ]

    RESEARCH_KEYWORDS = [
        "search", "what is", "explain", "compare", "pros and cons", "difference",
        "documentation", "how does", "why does", "best practices", "benchmark"
    ]

    def classify(self, prompt: str) -> IntentClassificationResult:
        """
        Classifies user prompt using deterministic semantic matching.
        """
        prompt_lower = prompt.lower().strip()
        words = set(prompt_lower.split())

        detected_autonomous = [k for k in self.AUTONOMOUS_KEYWORDS if k in prompt_lower]
        detected_creation = [k for k in self.PROJECT_CREATION_KEYWORDS if k in prompt_lower]
        detected_mod = [k for k in self.PROJECT_MODIFICATION_KEYWORDS if k in prompt_lower]
        detected_debug = [k for k in self.DEBUGGING_KEYWORDS if k in prompt_lower]
        detected_coding = [k for k in self.CODING_KEYWORDS if k in prompt_lower]
        detected_files = [k for k in self.FILE_KEYWORDS if k in prompt_lower]
        detected_research = [k for k in self.RESEARCH_KEYWORDS if k in prompt_lower]

        # Multi-step autonomous task check (e.g. "Build a task management app with React, FastAPI, MongoDB")
        has_framework_combo = sum(1 for f in ["react", "fastapi", "mongodb", "next.js", "docker", "postgres", "vue", "django"] if f in prompt_lower) >= 2
        is_plan_request = any(k in prompt_lower for k in ["plan a", "plan and build", "plan the", "design a"])

        if (detected_autonomous and (has_framework_combo or len(detected_autonomous) >= 1)) or is_plan_request:
            return IntentClassificationResult(
                intent=UserIntent.MULTI_STEP_AUTONOMOUS,
                confidence=0.95,
                is_autonomous_task=True,
                requires_planning=True,
                detected_keywords=detected_autonomous or ["plan_request"],
                suggested_mode="developer",
                reasoning="Request specifies a multi-step objective or full-stack architectural goal requiring autonomous planning."
            )

        if detected_creation:
            return IntentClassificationResult(
                intent=UserIntent.PROJECT_CREATION,
                confidence=0.90,
                is_autonomous_task=True,
                requires_planning=True,
                detected_keywords=detected_creation,
                suggested_mode="developer",
                reasoning="Request is aimed at initializing or scaffolding a new project."
            )

        if detected_debug:
            return IntentClassificationResult(
                intent=UserIntent.DEBUGGING,
                confidence=0.88,
                is_autonomous_task=False,
                requires_planning=False,
                detected_keywords=detected_debug,
                suggested_mode="assistant",
                reasoning="Request contains debugging indicators, stack traces, or error diagnostics."
            )

        if detected_mod:
            return IntentClassificationResult(
                intent=UserIntent.PROJECT_MODIFICATION,
                confidence=0.85,
                is_autonomous_task=True,
                requires_planning=True,
                detected_keywords=detected_mod,
                suggested_mode="developer",
                reasoning="Request asks for modifications or refactoring across existing project components."
            )

        if detected_files:
            return IntentClassificationResult(
                intent=UserIntent.FILE_RELATED,
                confidence=0.82,
                is_autonomous_task=False,
                requires_planning=False,
                detected_keywords=detected_files,
                suggested_mode="editor",
                reasoning="Request focuses on inspecting or manipulating specific files or directories."
            )

        if detected_coding:
            return IntentClassificationResult(
                intent=UserIntent.CODING_ASSISTANCE,
                confidence=0.85,
                is_autonomous_task=False,
                requires_planning=False,
                detected_keywords=detected_coding,
                suggested_mode="assistant",
                reasoning="Request asks for code snippets, programming explanations, or algorithmic assistance."
            )

        if detected_research:
            return IntentClassificationResult(
                intent=UserIntent.RESEARCH,
                confidence=0.80,
                is_autonomous_task=False,
                requires_planning=False,
                detected_keywords=detected_research,
                suggested_mode="assistant",
                reasoning="Request asks for research, concepts, or technical explanations."
            )

        # Default fallback: General conversation
        return IntentClassificationResult(
            intent=UserIntent.GENERAL_CONVERSATION,
            confidence=0.75,
            is_autonomous_task=False,
            requires_planning=False,
            detected_keywords=[],
            suggested_mode="assistant",
            reasoning="General conversational inquiry or assistant query."
        )


intent_classifier = IntentClassifier()

