"""Unit tests for CodeExtractor, ResponseParser, and ReviewExecutor.

Tests cover code extraction from local paths, LLM response parsing
(JSON and markdown fallback), and the end-to-end review execution flow.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.llm.base_client import LLMResponse
from src.workers.swarm.executor import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_TOTAL_LINES,
    REVIEW_JSON_SCHEMA,
    CodeContext,
    CodeExtractor,
    CodeFile,
    ResponseParser,
    ReviewExecutor,
)
from src.workers.swarm.models import ReviewerResult, ReviewFinding, Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class MockReviewer:
    """Minimal implementation satisfying the SpecializedReviewer protocol."""

    def __init__(
        self,
        reviewer_type: str = "security",
        focus_areas: list[str] | None = None,
        severity_weights: dict[str, float] | None = None,
        system_prompt: str = "You are a security reviewer.",
        checklist: list[str] | None = None,
    ) -> None:
        self.reviewer_type = reviewer_type
        self.focus_areas = focus_areas or ["injection", "auth"]
        self.severity_weights = severity_weights or {"injection": 1.0, "auth": 0.8}
        self._system_prompt = system_prompt
        self._checklist = checklist or ["Check SQL injection", "Check auth bypass"]

    def get_system_prompt(self) -> str:
        """Return the system prompt."""
        return self._system_prompt

    def get_checklist(self) -> list[str]:
        """Return the review checklist."""
        return list(self._checklist)


def _make_finding_dict(
    *,
    severity: str = "HIGH",
    category: str = "security",
    title: str = "SQL Injection",
    description: str = "Unsanitized user input in query",
    file_path: str = "src/app.py",
    line_start: int = 42,
    line_end: int | None = 45,
    code_snippet: str | None = "cursor.execute(query)",
    recommendation: str = "Use parameterized queries",
    confidence: float = 0.9,
) -> dict:
    """Build a finding dict suitable for JSON serialisation."""
    return {
        "severity": severity,
        "category": category,
        "title": title,
        "description": description,
        "file_path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "code_snippet": code_snippet,
        "recommendation": recommendation,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# TestCodeExtractor
# ---------------------------------------------------------------------------


class TestCodeExtractor:
    """Tests for the CodeExtractor class."""

    @pytest.mark.asyncio
    async def test_extract_local_single_python_file(self, tmp_path: Path) -> None:
        """Extract a single .py file and verify CodeContext contents."""
        py_file = tmp_path / "hello.py"
        py_file.write_text("print('hello')\n", encoding="utf-8")

        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract("hello.py")

        assert len(ctx.files) == 1
        assert ctx.files[0].content == "print('hello')\n"
        assert ctx.files[0].lines == 1
        assert ctx.total_lines == 1
        assert ctx.extraction_errors == []

    @pytest.mark.asyncio
    async def test_extract_local_directory_with_mixed_files(
        self, tmp_path: Path
    ) -> None:
        """Only files with allowed extensions are extracted."""
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "index.ts").write_text("const a = 1;\n", encoding="utf-8")
        (tmp_path / "readme.txt").write_text("hello\n", encoding="utf-8")
        (tmp_path / "notes.md").write_text("# Notes\n", encoding="utf-8")

        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract(".")

        extracted_suffixes = {Path(f.path).suffix for f in ctx.files}
        assert ".py" in extracted_suffixes
        assert ".ts" in extracted_suffixes
        assert ".txt" not in extracted_suffixes
        assert ".md" not in extracted_suffixes
        assert len(ctx.files) == 2

    @pytest.mark.asyncio
    async def test_extract_local_skips_large_files(self, tmp_path: Path) -> None:
        """Files exceeding MAX_FILE_SIZE_BYTES are skipped with an error."""
        large_file = tmp_path / "big.py"
        large_file.write_text("x" * (MAX_FILE_SIZE_BYTES + 1), encoding="utf-8")

        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract("big.py")

        assert len(ctx.files) == 0
        assert len(ctx.extraction_errors) == 1
        assert "exceeds" in ctx.extraction_errors[0]

    @pytest.mark.asyncio
    async def test_extract_local_respects_max_total_lines(
        self, tmp_path: Path
    ) -> None:
        """Total lines across all extracted files must not exceed MAX_TOTAL_LINES."""
        subdir = tmp_path / "src"
        subdir.mkdir()

        # Create files whose total lines exceed the limit.
        lines_per_file = 1000
        num_files = (MAX_TOTAL_LINES // lines_per_file) + 2  # ensure overflow
        for i in range(num_files):
            file_path = subdir / f"mod_{i:03d}.py"
            file_path.write_text(
                "\n".join(f"line_{j}" for j in range(lines_per_file)) + "\n",
                encoding="utf-8",
            )

        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract("src")

        assert ctx.total_lines <= MAX_TOTAL_LINES

    @pytest.mark.asyncio
    async def test_extract_local_nonexistent_path(self, tmp_path: Path) -> None:
        """Extracting a path that does not exist returns errors."""
        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract("does_not_exist")

        assert len(ctx.files) == 0
        assert len(ctx.extraction_errors) >= 1
        assert "does not exist" in ctx.extraction_errors[0]

    @pytest.mark.asyncio
    async def test_extract_local_empty_directory(self, tmp_path: Path) -> None:
        """An empty directory returns an empty CodeContext."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        extractor = CodeExtractor(workspace_root=str(tmp_path))
        ctx = await extractor.extract("empty")

        assert len(ctx.files) == 0
        assert ctx.total_lines == 0
        assert ctx.extraction_errors == []

    def test_parse_github_url_standard(self) -> None:
        """Standard GitHub URLs are parsed into (owner, repo)."""
        owner, repo = CodeExtractor._parse_github_url(
            "https://github.com/owner/repo"
        )
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_tree(self) -> None:
        """URLs with /tree/main suffix still return (owner, repo)."""
        owner, repo = CodeExtractor._parse_github_url(
            "https://github.com/owner/repo/tree/main"
        )
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_too_few_parts(self) -> None:
        """URLs with fewer than 5 slash-separated parts return empty strings."""
        owner, repo = CodeExtractor._parse_github_url(
            "https://github.com/owner"
        )
        assert owner == ""
        assert repo == ""

    @pytest.mark.asyncio
    async def test_extract_github_dispatches_correctly(self) -> None:
        """A github.com URL triggers the GitHub extraction path."""
        extractor = CodeExtractor(workspace_root="/tmp")

        with patch.object(
            extractor, "_extract_github", new_callable=AsyncMock
        ) as mock_gh:
            mock_gh.return_value = CodeContext()
            await extractor.extract("https://github.com/owner/repo")

            mock_gh.assert_awaited_once_with("https://github.com/owner/repo")


# ---------------------------------------------------------------------------
# TestResponseParser
# ---------------------------------------------------------------------------


class TestResponseParser:
    """Tests for the ResponseParser class."""

    def test_parse_valid_json_findings(self) -> None:
        """A well-formed JSON response with two findings is parsed correctly."""
        findings_data = {
            "findings": [
                _make_finding_dict(severity="HIGH", title="Finding A"),
                _make_finding_dict(severity="MEDIUM", title="Finding B"),
            ]
        }
        raw = json.dumps(findings_data)

        results = ResponseParser.parse(raw, "security")

        assert len(results) == 2
        assert results[0].title == "Finding A"
        assert results[0].severity == Severity.HIGH
        assert results[1].title == "Finding B"
        assert results[1].severity == Severity.MEDIUM
        for r in results:
            assert r.reviewer_type == "security"

    def test_parse_json_with_code_fences(self) -> None:
        """JSON wrapped in markdown code fences is parsed correctly."""
        findings_data = {
            "findings": [_make_finding_dict(severity="LOW", title="Fenced")]
        }
        raw = f"```json\n{json.dumps(findings_data)}\n```"

        results = ResponseParser.parse(raw, "style")

        assert len(results) == 1
        assert results[0].title == "Fenced"

    def test_parse_json_bare_list(self) -> None:
        """A bare JSON array (no 'findings' wrapper) is parsed correctly."""
        raw = json.dumps([
            _make_finding_dict(title="Bare 1"),
            _make_finding_dict(title="Bare 2"),
        ])

        results = ResponseParser.parse(raw, "perf")

        assert len(results) == 2
        assert results[0].title == "Bare 1"
        assert results[1].title == "Bare 2"

    def test_parse_skips_invalid_findings(self) -> None:
        """Findings missing required fields are skipped; valid ones survive."""
        findings_data = {
            "findings": [
                _make_finding_dict(title="Valid 1"),
                # Missing 'severity' -- should be skipped
                {
                    "category": "bug",
                    "title": "Invalid",
                    "description": "no severity",
                    "recommendation": "fix it",
                    "confidence": 0.5,
                },
                _make_finding_dict(title="Valid 2"),
            ]
        }
        raw = json.dumps(findings_data)

        results = ResponseParser.parse(raw, "security")

        assert len(results) == 2
        titles = {r.title for r in results}
        assert "Valid 1" in titles
        assert "Valid 2" in titles

    def test_parse_normalizes_severity_to_uppercase(self) -> None:
        """Lowercase severity values are normalised to uppercase."""
        raw = json.dumps({
            "findings": [_make_finding_dict(severity="high")]
        })

        results = ResponseParser.parse(raw, "security")

        assert len(results) == 1
        assert results[0].severity == Severity.HIGH

    def test_parse_clamps_confidence(self) -> None:
        """Confidence values outside [0.0, 1.0] are clamped."""
        raw = json.dumps({
            "findings": [
                _make_finding_dict(confidence=1.5, title="Over"),
                _make_finding_dict(confidence=-0.5, title="Under"),
            ]
        })

        results = ResponseParser.parse(raw, "security")

        assert len(results) == 2
        by_title = {r.title: r for r in results}
        assert by_title["Over"].confidence == 1.0
        assert by_title["Under"].confidence == 0.0

    def test_parse_generates_unique_ids(self) -> None:
        """Each parsed finding receives a unique id starting with 'finding-'."""
        raw = json.dumps({
            "findings": [
                _make_finding_dict(title="A"),
                _make_finding_dict(title="B"),
                _make_finding_dict(title="C"),
            ]
        })

        results = ResponseParser.parse(raw, "security")

        ids = [r.id for r in results]
        assert len(ids) == 3
        assert len(set(ids)) == 3, "IDs must be unique"
        for fid in ids:
            assert fid.startswith("finding-")

    def test_parse_sets_default_fields(self) -> None:
        """Missing optional fields receive appropriate defaults."""
        finding_dict = {
            "severity": "MEDIUM",
            "category": "style",
            "title": "Defaults test",
            "description": "Testing default fields",
            "recommendation": "Use defaults",
            "confidence": 0.7,
            # file_path, line_start, line_end, code_snippet intentionally absent
        }
        raw = json.dumps({"findings": [finding_dict]})

        results = ResponseParser.parse(raw, "style")

        assert len(results) == 1
        f = results[0]
        assert f.file_path == ""
        assert f.line_start == 0
        assert f.line_end is None
        assert f.code_snippet is None

    def test_parse_markdown_fallback(self) -> None:
        """Non-JSON text with severity markers is parsed via markdown fallback."""
        raw = (
            "Some preamble text.\n"
            "**HIGH** SQL Injection Risk\n"
            "User input is concatenated directly into SQL query.\n"
            "**MEDIUM** Missing input validation\n"
            "No validation on the email field.\n"
        )

        results = ResponseParser.parse(raw, "security")

        assert len(results) >= 1
        severities = {r.severity for r in results}
        assert Severity.HIGH in severities or Severity.MEDIUM in severities

    def test_parse_empty_response(self) -> None:
        """An empty string returns an empty list."""
        results = ResponseParser.parse("", "security")

        assert results == []

    def test_parse_invalid_severity_skipped(self) -> None:
        """Findings with an unrecognised severity value are skipped."""
        raw = json.dumps({
            "findings": [_make_finding_dict(severity="UNKNOWN")]
        })

        results = ResponseParser.parse(raw, "security")

        assert len(results) == 0


# ---------------------------------------------------------------------------
# TestReviewExecutor
# ---------------------------------------------------------------------------


class TestReviewExecutor:
    """Tests for the ReviewExecutor class."""

    @pytest.fixture
    def mock_factory(self) -> AsyncMock:
        """Create a mock LLMClientFactory."""
        factory = AsyncMock()
        return factory

    @pytest.fixture
    def mock_client(self) -> AsyncMock:
        """Create a mock BaseLLMClient."""
        client = AsyncMock()
        return client

    @pytest.fixture
    def reviewer(self) -> MockReviewer:
        """Create a mock SpecializedReviewer."""
        return MockReviewer(
            reviewer_type="security",
            system_prompt="You are a security reviewer.",
            checklist=["Check SQL injection", "Check auth bypass"],
        )

    @pytest.mark.asyncio
    async def test_execute_review_success(
        self,
        tmp_path: Path,
        mock_factory: AsyncMock,
        mock_client: AsyncMock,
        reviewer: MockReviewer,
    ) -> None:
        """Successful review returns status='success' with findings and files."""
        # Create a source file to review.
        src_file = tmp_path / "app.py"
        src_file.write_text("x = 1\n", encoding="utf-8")

        findings_json = json.dumps({
            "findings": [
                _make_finding_dict(title="Test finding"),
            ]
        })
        mock_client.generate.return_value = LLMResponse(
            content=findings_json, model="test-model"
        )
        mock_factory.get_client.return_value = mock_client

        executor = ReviewExecutor(
            factory=mock_factory, workspace_root=str(tmp_path)
        )
        result = await executor.execute_review("swarm-001", "app.py", reviewer)

        assert isinstance(result, ReviewerResult)
        assert result.status == "success"
        assert len(result.findings) == 1
        assert result.findings[0].title == "Test finding"
        assert len(result.files_reviewed) == 1
        assert result.error_message is None
        assert result.duration_seconds >= 0

    @pytest.mark.asyncio
    async def test_execute_review_no_files_found(
        self,
        tmp_path: Path,
        mock_factory: AsyncMock,
        reviewer: MockReviewer,
    ) -> None:
        """When no files are found, result is success with empty lists."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        executor = ReviewExecutor(
            factory=mock_factory, workspace_root=str(tmp_path)
        )
        result = await executor.execute_review("swarm-002", "empty", reviewer)

        assert result.status == "success"
        assert result.findings == []
        assert result.files_reviewed == []
        # Factory should not have been called since there are no files.
        mock_factory.get_client.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_execute_review_llm_error_returns_failed(
        self,
        tmp_path: Path,
        mock_factory: AsyncMock,
        mock_client: AsyncMock,
        reviewer: MockReviewer,
    ) -> None:
        """LLM errors result in status='failed' with an error message, never raising."""
        src_file = tmp_path / "app.py"
        src_file.write_text("x = 1\n", encoding="utf-8")

        mock_client.generate.side_effect = RuntimeError("LLM service unavailable")
        mock_factory.get_client.return_value = mock_client

        executor = ReviewExecutor(
            factory=mock_factory, workspace_root=str(tmp_path)
        )
        result = await executor.execute_review("swarm-003", "app.py", reviewer)

        assert result.status == "failed"
        assert result.error_message is not None
        assert "LLM service unavailable" in result.error_message
        assert result.findings == []

    @pytest.mark.asyncio
    async def test_execute_review_builds_system_prompt_with_schema(
        self,
        tmp_path: Path,
        mock_factory: AsyncMock,
        mock_client: AsyncMock,
        reviewer: MockReviewer,
    ) -> None:
        """The system prompt includes the reviewer prompt, JSON schema, and severity guidelines."""
        src_file = tmp_path / "app.py"
        src_file.write_text("x = 1\n", encoding="utf-8")

        mock_client.generate.return_value = LLMResponse(
            content='{"findings": []}', model="test-model"
        )
        mock_factory.get_client.return_value = mock_client

        executor = ReviewExecutor(
            factory=mock_factory, workspace_root=str(tmp_path)
        )
        await executor.execute_review("swarm-004", "app.py", reviewer)

        # Inspect the system prompt passed to generate().
        call_kwargs = mock_client.generate.call_args
        system_prompt = call_kwargs.kwargs.get("system") or call_kwargs[1].get("system", "")

        assert reviewer.get_system_prompt() in system_prompt
        assert "findings" in system_prompt  # JSON schema snippet
        assert "CRITICAL" in system_prompt
        assert "HIGH" in system_prompt
        assert "MEDIUM" in system_prompt
        assert "LOW" in system_prompt
        assert "INFO" in system_prompt
        assert "confidence" in system_prompt

    @pytest.mark.asyncio
    async def test_execute_review_builds_user_prompt_with_code_and_checklist(
        self,
        tmp_path: Path,
        mock_factory: AsyncMock,
        mock_client: AsyncMock,
        reviewer: MockReviewer,
    ) -> None:
        """The user prompt includes file contents and each checklist item."""
        src_file = tmp_path / "app.py"
        src_file.write_text("import os\nprint(os.getcwd())\n", encoding="utf-8")

        mock_client.generate.return_value = LLMResponse(
            content='{"findings": []}', model="test-model"
        )
        mock_factory.get_client.return_value = mock_client

        executor = ReviewExecutor(
            factory=mock_factory, workspace_root=str(tmp_path)
        )
        await executor.execute_review("swarm-005", "app.py", reviewer)

        call_kwargs = mock_client.generate.call_args
        user_prompt = call_kwargs.kwargs.get("prompt") or call_kwargs[0][0] if call_kwargs[0] else ""
        # If passed as keyword
        if not user_prompt and call_kwargs.kwargs:
            user_prompt = call_kwargs.kwargs.get("prompt", "")

        # File content must appear
        assert "import os" in user_prompt
        assert "print(os.getcwd())" in user_prompt

        # Checklist items must appear
        for item in reviewer.get_checklist():
            assert item in user_prompt
