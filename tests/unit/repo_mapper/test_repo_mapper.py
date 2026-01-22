"""Tests for RepoMapper main class."""
from pathlib import Path
import json
import pytest
from src.workers.repo_mapper.mapper import RepoMapper
from src.core.models import ContextPack, AgentRole


@pytest.fixture
def simple_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "test_repo"
    repo.mkdir()
    (repo / "main.py").write_text('def main():\n    print("Hello")\n')
    return repo


class TestRepoMapperInit:
    def test_init_with_repo_path(self, simple_repo: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        assert mapper.repo_path == simple_repo.resolve()
        assert mapper.config is not None


class TestRefreshASTContext:
    def test_refresh_parses_repository(self, simple_repo: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        context = mapper.refresh_ast_context()
        assert context is not None
        assert len(context.files) > 0


class TestGenerateContextPack:
    def test_generate_basic_context_pack(self, simple_repo: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        result = mapper.generate_context_pack(
            task_description="Implement main function",
            target_files=["main.py"],
            role=AgentRole.CODING,
            token_budget=10000,
        )
        assert isinstance(result, ContextPack)
        assert result.task_description == "Implement main function"
        assert len(result.files) > 0

    def test_generate_respects_token_budget(self, simple_repo: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        result = mapper.generate_context_pack(
            task_description="Test",
            target_files=["main.py"],
            role=AgentRole.CODING,
            token_budget=500,
        )
        assert result.token_count <= 500


class TestSaveContextPack:
    def test_save_writes_json_file(self, simple_repo: Path, tmp_path: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        context_pack = mapper.generate_context_pack(
            task_description="Test save operation",
            target_files=["main.py"],
            role=AgentRole.CODING,
            token_budget=10000,
        )
        output_path = tmp_path / "context_pack.json"
        mapper.save_context_pack(context_pack, str(output_path))
        assert output_path.exists()
        with open(output_path) as f:
            data = json.load(f)
        assert data["task_description"] == "Test save operation"

    def test_save_creates_parent_directories(self, simple_repo: Path, tmp_path: Path) -> None:
        mapper = RepoMapper(repo_path=str(simple_repo))
        context_pack = mapper.generate_context_pack(
            task_description="Test directory creation",
            target_files=["main.py"],
            role=AgentRole.CODING,
            token_budget=10000,
        )
        output_path = tmp_path / "nested" / "dir" / "pack.json"
        mapper.save_context_pack(context_pack, str(output_path))
        assert output_path.exists()
