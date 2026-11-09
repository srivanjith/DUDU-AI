"""
DODO Project Intelligence Scanner
Inspects authorized project workspaces, detects languages, frameworks,
dependencies, entry points, configuration files, and test suites.
Never invents files or dependencies; extracts factual architecture from disk.
"""
import os
from pathlib import Path
import json
import re
import subprocess
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ProjectScanResult(BaseModel):
    workspace_path: str
    project_name: str
    is_git_repo: bool = False
    git_branch: Optional[str] = None
    git_status: Optional[str] = None
    languages: Dict[str, int] = Field(default_factory=dict)  # language -> file_count
    primary_language: str = "Unknown"
    frameworks: List[str] = Field(default_factory=list)
    package_managers: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    config_files: List[str] = Field(default_factory=list)
    test_files: List[str] = Field(default_factory=list)
    total_files: int = 0
    total_size_bytes: int = 0
    source_directories: List[str] = Field(default_factory=list)
    summary: str = ""


class ProjectScanner:
    """
    Comprehensive filesystem scanner for project intelligence.
    Excludes sensitive files, node_modules, and virtual environments.
    """

    EXCLUDED_DIRS: Set[str] = {
        ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
        ".next", "dist", "build", "target", ".pytest_cache", ".dodo_checkpoints",
        ".idea", ".vscode"
    }

    SECRET_FILE_PATTERNS = [
        r"^\.env(\..+)?$",
        r".*id_rsa.*",
        r".*\.pem$",
        r".*\.key$",
        r".*credentials.*",
        r".*secret.*"
    ]

    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript (React)",
        ".js": "JavaScript",
        ".jsx": "JavaScript (React)",
        ".html": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".c": "C",
        ".h": "C/C++ Header",
        ".cpp": "C++",
        ".hpp": "C++ Header",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".sql": "SQL",
        ".sh": "Shell",
        ".ps1": "PowerShell",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".md": "Markdown",
    }

    ENTRYPOINT_NAMES = {
        "main.py", "app.py", "server.py", "index.ts", "index.js",
        "main.ts", "main.js", "manage.py", "wsgi.py", "asgi.py",
        "app.ts", "server.js", "page.tsx", "App.tsx", "App.js"
    }

    CONFIG_NAMES = {
        "package.json", "tsconfig.json", "requirements.txt", "pyproject.toml",
        "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
        "tailwind.config.js", "tailwind.config.ts", "vite.config.ts",
        "vite.config.js", "next.config.js", "next.config.mjs",
        "Cargo.toml", "pom.xml", "build.gradle", "Makefile", "CMakeLists.txt"
    }

    def is_secret_file(self, filename: str) -> bool:
        for pat in self.SECRET_FILE_PATTERNS:
            if re.match(pat, filename, re.IGNORECASE):
                return True
        return False

    def scan(self, workspace_path: str) -> ProjectScanResult:
        root = Path(workspace_path).resolve()
        if not root.exists() or not root.is_dir():
            return ProjectScanResult(
                workspace_path=str(root),
                project_name=root.name,
                summary=f"Workspace path '{root}' does not exist or is not a directory."
            )

        languages_count: Dict[str, int] = {}
        entry_points: List[str] = []
        config_files: List[str] = []
        test_files: List[str] = []
        source_dirs: Set[str] = set()
        dependencies: List[str] = []
        frameworks: Set[str] = set()
        package_managers: Set[str] = set()
        total_files = 0
        total_size = 0

        # Read .gitignore if present to honor project exclusions
        gitignore_patterns = set()
        gitignore_file = root / ".gitignore"
        if gitignore_file.exists():
            try:
                for line in gitignore_file.read_text(encoding="utf-8", errors="replace").splitlines():
                    clean = line.strip()
                    if clean and not clean.startswith("#"):
                        gitignore_patterns.add(clean.rstrip("/"))
            except Exception:
                pass

        # Traversal
        for current_dir, dirnames, filenames in os.walk(root):
            # Prune excluded directories in-place
            dirnames[:] = [
                d for d in dirnames
                if d not in self.EXCLUDED_DIRS and d not in gitignore_patterns
            ]

            rel_dir = Path(current_dir).relative_to(root)
            if str(rel_dir) != ".":
                top_part = rel_dir.parts[0]
                if top_part in {"src", "app", "backend", "frontend", "lib", "components", "pages", "api"}:
                    source_dirs.add(top_part)

            for f in filenames:
                if self.is_secret_file(f):
                    continue  # Do not index secret files

                file_path = Path(current_dir) / f
                try:
                    size = file_path.stat().st_size
                except Exception:
                    size = 0

                total_files += 1
                total_size += size

                rel_file = str(file_path.relative_to(root)).replace("\\", "/")
                ext = file_path.suffix.lower()

                # Language detection
                lang = self.LANGUAGE_EXTENSIONS.get(ext)
                if lang:
                    languages_count[lang] = languages_count.get(lang, 0) + 1

                # Entry point detection
                if f in self.ENTRYPOINT_NAMES:
                    entry_points.append(rel_file)

                # Config files detection
                if f in self.CONFIG_NAMES:
                    config_files.append(rel_file)

                # Test files detection
                if "test" in f.lower() or "spec" in f.lower() or "tests" in rel_file.split("/"):
                    test_files.append(rel_file)

        # Parse Package Managers & Dependencies from discovered configs
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="replace"))
                deps = list(data.get("dependencies", {}).keys()) + list(data.get("devDependencies", {}).keys())
                dependencies.extend(deps[:30])

                if "react" in deps:
                    frameworks.add("React")
                if "next" in deps:
                    frameworks.add("Next.js")
                if "vue" in deps:
                    frameworks.add("Vue")
                if "express" in deps:
                    frameworks.add("Express")
                if "tailwindcss" in deps:
                    frameworks.add("Tailwind CSS")

                if (root / "pnpm-lock.yaml").exists():
                    package_managers.add("pnpm")
                elif (root / "yarn.lock").exists():
                    package_managers.add("yarn")
                else:
                    package_managers.add("npm")
            except Exception:
                pass

        req_txt = root / "requirements.txt"
        if req_txt.exists():
            package_managers.add("pip")
            try:
                lines = req_txt.read_text(encoding="utf-8", errors="replace").splitlines()
                for line in lines:
                    dep = line.strip().split("==")[0].split(">=")[0].split("<=")[0].strip()
                    if dep and not dep.startswith("#"):
                        dependencies.append(dep)
                        if dep.lower() in ["fastapi", "uvicorn"]:
                            frameworks.add("FastAPI")
                        elif dep.lower() == "flask":
                            frameworks.add("Flask")
                        elif dep.lower() == "django":
                            frameworks.add("Django")
                        elif dep.lower() in ["pymongo", "mongomock"]:
                            frameworks.add("MongoDB")
            except Exception:
                pass

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            package_managers.add("poetry/pip")

        # Git inspection
        is_git = (root / ".git").exists()
        git_branch = None
        git_status_str = None
        if is_git:
            try:
                b_res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(root), capture_output=True, text=True, timeout=2)
                if b_res.returncode == 0:
                    git_branch = b_res.stdout.strip()
                s_res = subprocess.run(["git", "status", "--short"], cwd=str(root), capture_output=True, text=True, timeout=2)
                if s_res.returncode == 0:
                    git_status_str = "clean" if not s_res.stdout.strip() else f"{len(s_res.stdout.strip().splitlines())} modified file(s)"
            except Exception:
                pass

        # Determine Primary Language
        primary_lang = "Unknown"
        if languages_count:
            primary_lang = max(languages_count.items(), key=lambda x: x[1])[0]

        summary = (
            f"Project '{root.name}' ({primary_lang}). Discovered {total_files} files "
            f"({round(total_size / 1024, 1)} KB). "
            f"Frameworks: {', '.join(sorted(frameworks)) if frameworks else 'Standard Library'}. "
            f"Package Managers: {', '.join(sorted(package_managers)) if package_managers else 'None'}. "
            f"Entry Points: {len(entry_points)}. Test Files: {len(test_files)}."
        )

        return ProjectScanResult(
            workspace_path=str(root),
            project_name=root.name,
            is_git_repo=is_git,
            git_branch=git_branch,
            git_status=git_status_str,
            languages=languages_count,
            primary_language=primary_lang,
            frameworks=sorted(list(frameworks)),
            package_managers=sorted(list(package_managers)),
            entry_points=entry_points[:15],
            dependencies=dependencies[:40],
            config_files=config_files[:15],
            test_files=test_files[:20],
            total_files=total_files,
            total_size_bytes=total_size,
            source_directories=sorted(list(source_dirs)),
            summary=summary,
        )


project_scanner = ProjectScanner()
