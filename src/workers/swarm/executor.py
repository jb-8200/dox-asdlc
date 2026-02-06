"""Review executor for Parallel Review Swarm.

This module provides the real LLM-based review executor that replaces the
stub ``_default_executor`` in :class:`SwarmDispatcher`.  It contains three
public classes:

* :class:`CodeExtractor` -- extracts source files from local paths or GitHub
  repositories, applying extension filters and size limits.
* :class:`ResponseParser` -- parses LLM responses (JSON or markdown fallback)
  into :class:`ReviewFinding` instances.
* :class:`ReviewExecutor` -- orchestrates extraction, LLM invocation, and
  response parsing to produce a :class:`ReviewerResult`.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.orchestrator.api.models.llm_config import AgentRole
from src.workers.swarm.models import ReviewFinding, ReviewerResult, Severity

if TYPE_CHECKING:
    from src.infrastructure.llm.factory import LLMClientFactory
    from src.workers.swarm.reviewers.base import SpecializedReviewer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_EXTENSIONS: frozenset[str] = frozenset(
    {".py", ".ts", ".js", ".tsx", ".jsx", ".go", ".rs", ".java"}
)

MAX_FILE_SIZE_BYTES: int = 500 * 1024  # 500 KB
MAX_TOTAL_LINES: int = 5000

REVIEW_JSON_SCHEMA: str = """{
  "findings": [
    {
      "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
      "category": "string",
      "title": "string",
      "description": "string",
      "file_path": "string",
      "line_start": number_or_null,
      "line_end": number_or_null,
      "code_snippet": "string_or_null",
      "recommendation": "string",
      "confidence": 0.0-1.0
    }
  ]
}"""

_SEVERITY_VALUES: frozenset[str] = frozenset(
    {s.value for s in Severity}
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class CodeFile:
    """A single source file extracted for review.

    Attributes:
        path: Relative or absolute path of the file.
        content: Full text content of the file.
        lines: Number of lines in the file.
    """

    path: str
    content: str
    lines: int


@dataclass
class CodeContext:
    """Aggregated context of all source files extracted for a review.

    Attributes:
        files: List of extracted source files.
        total_lines: Sum of line counts across all files.
        extraction_errors: Any non-fatal errors encountered during extraction.
    """

    files: list[CodeFile] = field(default_factory=list)
    total_lines: int = 0
    extraction_errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# CodeExtractor
# ---------------------------------------------------------------------------


class CodeExtractor:
    """Extracts source code files from local paths or GitHub repositories.

    Applies extension filtering, file-size limits, and a total-line cap to
    prevent excessive LLM costs.

    Args:
        workspace_root: Root directory prepended to local ``target_path``
            values.  Defaults to ``"/app/workspace"``.
    """

    def __init__(self, workspace_root: str = "/app/workspace") -> None:
        self._workspace_root = workspace_root

    # -- public API ---------------------------------------------------------

    async def extract(self, target_path: str) -> CodeContext:
        """Extract source files for the given *target_path*.

        If *target_path* starts with ``https://github.com/`` the files are
        fetched from the GitHub API; otherwise the local filesystem is used.

        Args:
            target_path: A local path (relative to *workspace_root*) or a
                GitHub repository URL.

        Returns:
            A :class:`CodeContext` containing the extracted files.
        """
        if target_path.startswith("https://github.com/"):
            return await self._extract_github(target_path)
        return await self._extract_local(target_path)

    # -- local extraction ---------------------------------------------------

    async def _extract_local(self, target_path: str) -> CodeContext:
        """Extract files from the local filesystem.

        Args:
            target_path: Path relative to the workspace root.

        Returns:
            A :class:`CodeContext` with extracted files.
        """
        context = CodeContext()
        full_path = Path(self._workspace_root) / target_path

        if not full_path.exists():
            context.extraction_errors.append(
                f"Path does not exist: {full_path}"
            )
            return context

        if full_path.is_file():
            self._add_local_file(full_path, context)
            return context

        # Walk directory tree
        for root, _dirs, filenames in os.walk(full_path):
            if context.total_lines >= MAX_TOTAL_LINES:
                break
            for fname in sorted(filenames):
                if context.total_lines >= MAX_TOTAL_LINES:
                    break
                file_path = Path(root) / fname
                self._add_local_file(file_path, context)

        return context

    def _add_local_file(self, file_path: Path, context: CodeContext) -> None:
        """Try to add a single local file to *context*.

        Args:
            file_path: Absolute path to the file.
            context: The :class:`CodeContext` to populate.
        """
        if file_path.suffix not in ALLOWED_EXTENSIONS:
            return

        try:
            size = file_path.stat().st_size
        except OSError as exc:
            context.extraction_errors.append(
                f"Could not stat {file_path}: {exc}"
            )
            return

        if size > MAX_FILE_SIZE_BYTES:
            context.extraction_errors.append(
                f"Skipped {file_path}: exceeds {MAX_FILE_SIZE_BYTES} bytes"
            )
            return

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            context.extraction_errors.append(
                f"Could not read {file_path}: {exc}"
            )
            return

        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
        if context.total_lines + line_count > MAX_TOTAL_LINES:
            return

        context.files.append(
            CodeFile(path=str(file_path), content=content, lines=line_count)
        )
        context.total_lines += line_count

    # -- GitHub extraction --------------------------------------------------

    async def _extract_github(self, url: str) -> CodeContext:
        """Extract files from a public GitHub repository.

        Args:
            url: A ``https://github.com/{owner}/{repo}`` URL.

        Returns:
            A :class:`CodeContext` with extracted files.
        """
        import httpx

        context = CodeContext()
        owner, repo = self._parse_github_url(url)
        if not owner or not repo:
            context.extraction_errors.append(
                f"Could not parse GitHub owner/repo from URL: {url}"
            )
            return context

        tree_url = (
            f"https://api.github.com/repos/{owner}/{repo}"
            f"/git/trees/HEAD?recursive=1"
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(tree_url)
                resp.raise_for_status()
                tree_data = resp.json()
        except httpx.HTTPError as exc:
            context.extraction_errors.append(
                f"GitHub tree fetch failed: {exc}"
            )
            logger.warning("GitHub tree fetch failed for %s: %s", url, exc)
            return context

        tree_entries = tree_data.get("tree", [])
        blob_paths = [
            entry["path"]
            for entry in tree_entries
            if entry.get("type") == "blob"
            and Path(entry["path"]).suffix in ALLOWED_EXTENSIONS
            and entry.get("size", 0) <= MAX_FILE_SIZE_BYTES
        ]

        for blob_path in blob_paths:
            if context.total_lines >= MAX_TOTAL_LINES:
                break

            raw_url = (
                f"https://raw.githubusercontent.com/{owner}/{repo}"
                f"/HEAD/{blob_path}"
            )
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(raw_url)
                    resp.raise_for_status()
                    content = resp.text
            except httpx.HTTPError as exc:
                context.extraction_errors.append(
                    f"Failed to fetch {blob_path}: {exc}"
                )
                logger.warning(
                    "Failed to fetch %s from GitHub: %s", blob_path, exc
                )
                continue

            line_count = content.count("\n") + (
                1 if content and not content.endswith("\n") else 0
            )
            if context.total_lines + line_count > MAX_TOTAL_LINES:
                break

            context.files.append(
                CodeFile(path=blob_path, content=content, lines=line_count)
            )
            context.total_lines += line_count

        return context

    @staticmethod
    def _parse_github_url(url: str) -> tuple[str, str]:
        """Extract owner and repo from a GitHub URL.

        Args:
            url: A GitHub URL such as
                ``https://github.com/owner/repo`` or
                ``https://github.com/owner/repo/tree/main``.

        Returns:
            A ``(owner, repo)`` tuple.  Both elements are empty strings if
            parsing fails.
        """
        # Strip trailing slashes and optional segments after repo name
        parts = url.rstrip("/").split("/")
        # Expected: ['https:', '', 'github.com', owner, repo, ...]
        if len(parts) >= 5:
            return parts[3], parts[4]
        return "", ""


# ---------------------------------------------------------------------------
# ResponseParser
# ---------------------------------------------------------------------------


class ResponseParser:
    """Parses raw LLM response text into :class:`ReviewFinding` objects.

    This is a static utility class -- all methods are class methods and no
    instance state is needed.

    Two parsing strategies are attempted in order:

    1. **JSON** -- the response is parsed as JSON (after stripping optional
       markdown code fences).  The top-level object is expected to contain a
       ``"findings"`` key whose value is a list of finding dicts.
    2. **Markdown fallback** -- if JSON parsing fails, a best-effort regex
       extraction is performed looking for severity markers and surrounding
       text.
    """

    _CODE_FENCE_RE = re.compile(
        r"```(?:json)?\s*\n?(.*?)\n?\s*```", re.DOTALL
    )
    _SEVERITY_RE = re.compile(
        r"\*\*(CRITICAL|HIGH|MEDIUM|LOW|INFO)\*\*", re.IGNORECASE
    )

    @classmethod
    def parse(
        cls, raw_response: str, reviewer_type: str
    ) -> list[ReviewFinding]:
        """Parse *raw_response* into a list of findings.

        Args:
            raw_response: The raw text returned by the LLM.
            reviewer_type: The reviewer type to stamp on each finding.

        Returns:
            A list of validated :class:`ReviewFinding` instances.
        """
        findings = cls._try_json_parse(raw_response, reviewer_type)
        if findings is not None:
            return findings

        logger.warning(
            "JSON parse failed for reviewer %s; falling back to markdown "
            "extraction",
            reviewer_type,
        )
        return cls._try_markdown_parse(raw_response, reviewer_type)

    # -- JSON strategy ------------------------------------------------------

    @classmethod
    def _try_json_parse(
        cls, raw: str, reviewer_type: str
    ) -> list[ReviewFinding] | None:
        """Attempt to parse the response as JSON.

        Args:
            raw: Raw LLM response text.
            reviewer_type: Reviewer type for each finding.

        Returns:
            A list of findings if JSON parsing succeeds, else ``None``.
        """
        text = raw.strip()

        # Strategy 1: Strip markdown code fences if present
        fence_match = cls._CODE_FENCE_RE.search(text)
        if fence_match:
            text = fence_match.group(1).strip()

        # Strategy 2: If code fence didn't help, try extracting JSON
        # object or array from surrounding prose text
        data = None
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            # Try to find outermost { ... } or [ ... ]
            for open_char, close_char in [("{", "}"), ("[", "]")]:
                start = text.find(open_char)
                if start == -1:
                    continue
                end = text.rfind(close_char)
                if end <= start:
                    continue
                try:
                    data = json.loads(text[start : end + 1])
                    break
                except (json.JSONDecodeError, ValueError):
                    continue

        if data is None:
            return None

        raw_findings: list[dict[str, Any]]
        if isinstance(data, dict) and "findings" in data:
            raw_findings = data["findings"]
        elif isinstance(data, list):
            raw_findings = data
        else:
            return None

        if not isinstance(raw_findings, list):
            return None

        results: list[ReviewFinding] = []
        for item in raw_findings:
            finding = cls._dict_to_finding(item, reviewer_type)
            if finding is not None:
                results.append(finding)

        return results

    # -- Markdown fallback --------------------------------------------------

    @classmethod
    def _try_markdown_parse(
        cls, raw: str, reviewer_type: str
    ) -> list[ReviewFinding]:
        """Best-effort extraction of findings from markdown text.

        Args:
            raw: Raw LLM response text.
            reviewer_type: Reviewer type for each finding.

        Returns:
            A list of findings extracted from markdown.
        """
        results: list[ReviewFinding] = []

        # Split on severity markers
        parts = cls._SEVERITY_RE.split(raw)
        # parts alternates: [preamble, severity1, text1, severity2, text2, ...]
        if len(parts) < 3:
            return results

        for i in range(1, len(parts) - 1, 2):
            severity_str = parts[i].upper()
            body = parts[i + 1].strip()

            # Extract title from the first line
            lines = body.splitlines()
            title = lines[0].strip().strip(":").strip() if lines else "Untitled"
            description = "\n".join(lines[1:]).strip() if len(lines) > 1 else title

            if severity_str not in _SEVERITY_VALUES:
                continue

            finding_id = f"finding-{uuid.uuid4().hex[:8]}"
            try:
                results.append(
                    ReviewFinding(
                        id=finding_id,
                        reviewer_type=reviewer_type,
                        severity=Severity(severity_str),
                        category="general",
                        title=title[:200],
                        description=description[:2000],
                        file_path="",
                        line_start=0,
                        line_end=None,
                        code_snippet=None,
                        recommendation="See description for details.",
                        confidence=0.5,
                    )
                )
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "Skipped markdown finding (severity=%s): %s",
                    severity_str,
                    exc,
                )

        return results

    # -- Helpers ------------------------------------------------------------

    @classmethod
    def _dict_to_finding(
        cls, item: dict[str, Any], reviewer_type: str
    ) -> ReviewFinding | None:
        """Convert a single JSON dict to a :class:`ReviewFinding`.

        Args:
            item: A dictionary parsed from the LLM's JSON response.
            reviewer_type: Reviewer type to stamp on the finding.

        Returns:
            A validated :class:`ReviewFinding`, or ``None`` if the dict is
            invalid.
        """
        if not isinstance(item, dict):
            logger.warning("Skipped non-dict finding: %s", type(item))
            return None

        required = {"severity", "category", "title", "description",
                     "recommendation", "confidence"}
        missing = required - item.keys()
        if missing:
            logger.warning("Skipped finding missing fields %s: %s", missing, item)
            return None

        severity_raw = str(item["severity"]).upper()
        if severity_raw not in _SEVERITY_VALUES:
            logger.warning("Skipped finding with invalid severity: %s", severity_raw)
            return None

        try:
            confidence = float(item["confidence"])
        except (ValueError, TypeError):
            logger.warning(
                "Skipped finding with non-numeric confidence: %s",
                item["confidence"],
            )
            return None

        confidence = max(0.0, min(1.0, confidence))
        finding_id = f"finding-{uuid.uuid4().hex[:8]}"

        try:
            return ReviewFinding(
                id=finding_id,
                reviewer_type=reviewer_type,
                severity=Severity(severity_raw),
                category=str(item["category"]),
                title=str(item["title"]),
                description=str(item["description"]),
                file_path=str(item.get("file_path", "")),
                line_start=int(item.get("line_start") or 0),
                line_end=item.get("line_end"),
                code_snippet=item.get("code_snippet"),
                recommendation=str(item["recommendation"]),
                confidence=confidence,
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Failed to construct ReviewFinding: %s", exc)
            return None


# ---------------------------------------------------------------------------
# ReviewExecutor
# ---------------------------------------------------------------------------


class ReviewExecutor:
    """Executes a code review using an LLM client and a specialized reviewer.

    This executor is the real replacement for the stub
    ``SwarmDispatcher._default_executor``.  Its :meth:`execute_review` method
    has the same signature expected by :class:`SwarmDispatcher`.

    Args:
        factory: An :class:`LLMClientFactory` used to obtain LLM clients.
        workspace_root: Root directory for local code extraction.  Defaults to
            ``"/app/workspace"``.
    """

    def __init__(
        self,
        factory: LLMClientFactory,
        workspace_root: str = "/app/workspace",
    ) -> None:
        self._factory = factory
        self._extractor = CodeExtractor(workspace_root)

    async def execute_review(
        self,
        session_id: str,
        target_path: str,
        reviewer: SpecializedReviewer,
    ) -> ReviewerResult:
        """Execute a single reviewer's analysis on *target_path*.

        This method never raises.  Any unexpected error is caught and
        returned as a :class:`ReviewerResult` with ``status="failed"``.

        Args:
            session_id: The swarm session ID (for logging/tracing).
            target_path: Local path or GitHub URL to review.
            reviewer: The specialized reviewer providing prompts and checklist.

        Returns:
            A :class:`ReviewerResult` describing the outcome.
        """
        start = time.monotonic()
        try:
            return await self._do_review(
                session_id, target_path, reviewer, start
            )
        except Exception as exc:  # noqa: BLE001 -- intentional catch-all
            duration = time.monotonic() - start
            logger.error(
                "Review failed for session=%s reviewer=%s: %s",
                session_id,
                reviewer.reviewer_type,
                exc,
                exc_info=True,
            )
            return ReviewerResult(
                reviewer_type=reviewer.reviewer_type,
                status="failed",
                findings=[],
                duration_seconds=round(duration, 3),
                files_reviewed=[],
                error_message=str(exc),
            )

    # -- internals ----------------------------------------------------------

    async def _do_review(
        self,
        session_id: str,
        target_path: str,
        reviewer: SpecializedReviewer,
        start: float,
    ) -> ReviewerResult:
        """Core review logic, separated so the outer method can catch all errors.

        Args:
            session_id: The swarm session ID.
            target_path: Target path for code extraction.
            reviewer: The specialized reviewer.
            start: Monotonic timestamp when the review started.

        Returns:
            A :class:`ReviewerResult`.
        """
        # 1. Extract code
        code_context = await self._extractor.extract(target_path)

        if not code_context.files:
            duration = time.monotonic() - start
            logger.info(
                "No files found for session=%s target=%s reviewer=%s",
                session_id,
                target_path,
                reviewer.reviewer_type,
            )
            return ReviewerResult(
                reviewer_type=reviewer.reviewer_type,
                status="success",
                findings=[],
                duration_seconds=round(duration, 3),
                files_reviewed=[],
                error_message=None,
            )

        # 2. Build prompts
        system_prompt = self._build_system_prompt(reviewer)
        user_prompt = self._build_user_prompt(code_context, reviewer)

        # 3. Invoke LLM
        client = await self._factory.get_client(AgentRole.REVIEWER)
        response = await client.generate(
            prompt=user_prompt, system=system_prompt
        )

        # 4. Parse response
        logger.info(
            "LLM response for session=%s reviewer=%s: %d chars",
            session_id,
            reviewer.reviewer_type,
            len(response.content),
        )
        findings = ResponseParser.parse(
            response.content, reviewer.reviewer_type
        )

        duration = time.monotonic() - start
        return ReviewerResult(
            reviewer_type=reviewer.reviewer_type,
            status="success",
            findings=findings,
            duration_seconds=round(duration, 3),
            files_reviewed=[f.path for f in code_context.files],
            error_message=None,
        )

    @staticmethod
    def _build_system_prompt(reviewer: SpecializedReviewer) -> str:
        """Build the system prompt for the LLM call.

        Args:
            reviewer: The specialized reviewer providing the base prompt.

        Returns:
            The full system prompt string.
        """
        return (
            f"{reviewer.get_system_prompt()}\n\n"
            f"You MUST respond with valid JSON in the following format:\n"
            f"{REVIEW_JSON_SCHEMA}\n\n"
            f"Severity guidelines:\n"
            f"- CRITICAL: Security vulnerabilities, data loss, crashes\n"
            f"- HIGH: Major bugs, security issues, significant performance "
            f"problems\n"
            f"- MEDIUM: Moderate issues, code smells, maintainability "
            f"concerns\n"
            f"- LOW: Minor style issues, small improvements\n"
            f"- INFO: Suggestions, notes, best practice recommendations\n\n"
            f"confidence should be 0.0-1.0 indicating your confidence "
            f"in the finding."
        )

    @staticmethod
    def _build_user_prompt(
        code_context: CodeContext, reviewer: SpecializedReviewer
    ) -> str:
        """Build the user prompt containing the code and checklist.

        Args:
            code_context: The extracted code files.
            reviewer: The specialized reviewer providing the checklist.

        Returns:
            The full user prompt string.
        """
        parts: list[str] = ["Review the following code files:\n"]

        for code_file in code_context.files:
            parts.append(f"--- File: {code_file.path} ---")
            parts.append(code_file.content)
            parts.append("")

        parts.append("Checklist:")
        for item in reviewer.get_checklist():
            parts.append(f"- {item}")

        return "\n".join(parts)
