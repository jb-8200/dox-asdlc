"""Unit tests for discovery models."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.workers.agents.discovery.models import (
    Requirement,
    RequirementPriority,
    RequirementType,
    PRDSection,
    PRDDocument,
    AcceptanceCriterion,
    AcceptanceCriteria,
    CoverageEntry,
    DiscoveryResult,
)


class TestRequirement:
    """Tests for Requirement model."""

    def test_requirement_creation(self) -> None:
        """Test that requirement can be created with required fields."""
        req = Requirement(
            id="REQ-001",
            description="User can login with email and password",
        )

        assert req.id == "REQ-001"
        assert req.description == "User can login with email and password"
        assert req.priority == RequirementPriority.SHOULD_HAVE
        assert req.type == RequirementType.FUNCTIONAL

    def test_requirement_to_dict(self) -> None:
        """Test that requirement serializes to dictionary."""
        req = Requirement(
            id="REQ-001",
            description="Test requirement",
            priority=RequirementPriority.MUST_HAVE,
            type=RequirementType.NON_FUNCTIONAL,
            rationale="For testing",
            source="Unit test",
        )

        result = req.to_dict()

        assert result["id"] == "REQ-001"
        assert result["description"] == "Test requirement"
        assert result["priority"] == "must_have"
        assert result["type"] == "non_functional"
        assert result["rationale"] == "For testing"
        assert result["source"] == "Unit test"

    def test_requirement_from_dict(self) -> None:
        """Test that requirement deserializes from dictionary."""
        data = {
            "id": "REQ-002",
            "description": "From dict test",
            "priority": "could_have",
            "type": "constraint",
            "rationale": "Test rationale",
            "source": "Test source",
        }

        req = Requirement.from_dict(data)

        assert req.id == "REQ-002"
        assert req.description == "From dict test"
        assert req.priority == RequirementPriority.COULD_HAVE
        assert req.type == RequirementType.CONSTRAINT

    def test_requirement_to_markdown(self) -> None:
        """Test that requirement formats as markdown."""
        req = Requirement(
            id="REQ-001",
            description="Test requirement with rationale",
            priority=RequirementPriority.MUST_HAVE,
            rationale="This is important",
        )

        md = req.to_markdown()

        assert "### REQ-001:" in md
        assert "**Priority:** Must Have" in md
        assert "Test requirement with rationale" in md
        assert "**Rationale:** This is important" in md


class TestPRDSection:
    """Tests for PRDSection model."""

    def test_section_creation(self) -> None:
        """Test that section can be created."""
        section = PRDSection(
            title="Functional Requirements",
            content="This section describes functional requirements.",
        )

        assert section.title == "Functional Requirements"
        assert section.content == "This section describes functional requirements."
        assert section.requirements == []
        assert section.subsections == []

    def test_section_with_requirements(self) -> None:
        """Test that section can contain requirements."""
        reqs = [
            Requirement(id="REQ-001", description="First requirement"),
            Requirement(id="REQ-002", description="Second requirement"),
        ]

        section = PRDSection(
            title="Requirements",
            content="Section content",
            requirements=reqs,
        )

        assert len(section.requirements) == 2
        assert section.requirements[0].id == "REQ-001"

    def test_section_to_dict(self) -> None:
        """Test that section serializes to dictionary."""
        req = Requirement(id="REQ-001", description="Test")
        section = PRDSection(
            title="Test Section",
            content="Content",
            requirements=[req],
        )

        result = section.to_dict()

        assert result["title"] == "Test Section"
        assert result["content"] == "Content"
        assert len(result["requirements"]) == 1

    def test_section_from_dict(self) -> None:
        """Test that section deserializes from dictionary."""
        data = {
            "title": "From Dict",
            "content": "Test content",
            "requirements": [{"id": "REQ-001", "description": "Test"}],
            "subsections": [],
        }

        section = PRDSection.from_dict(data)

        assert section.title == "From Dict"
        assert len(section.requirements) == 1


class TestPRDDocument:
    """Tests for PRDDocument model."""

    def test_prd_document_create(self) -> None:
        """Test that PRD document can be created with factory method."""
        objectives = PRDSection(title="Objectives", content="Project objectives")
        scope = PRDSection(title="Scope", content="Project scope")
        sections = [
            PRDSection(
                title="Functional Requirements",
                content="Functional requirements",
                requirements=[Requirement(id="REQ-001", description="Test")],
            )
        ]

        prd = PRDDocument.create(
            title="Test PRD",
            executive_summary="Test summary",
            objectives=objectives,
            scope=scope,
            sections=sections,
        )

        assert prd.title == "Test PRD"
        assert prd.version == "1.0.0"
        assert prd.executive_summary == "Test summary"
        assert len(prd.all_requirements) == 1

    def test_prd_document_collects_all_requirements(self) -> None:
        """Test that PRD document collects requirements from all sections."""
        objectives = PRDSection(
            title="Objectives",
            content="Objectives",
            requirements=[Requirement(id="REQ-001", description="Objective req")],
        )
        scope = PRDSection(
            title="Scope",
            content="Scope",
            requirements=[Requirement(id="REQ-002", description="Scope req")],
        )
        sections = [
            PRDSection(
                title="Functional",
                content="Functional",
                requirements=[Requirement(id="REQ-003", description="Func req")],
            )
        ]

        prd = PRDDocument.create(
            title="Test",
            executive_summary="Summary",
            objectives=objectives,
            scope=scope,
            sections=sections,
        )

        assert len(prd.all_requirements) == 3

    def test_prd_document_to_json(self) -> None:
        """Test that PRD document serializes to JSON."""
        prd = PRDDocument.create(
            title="Test PRD",
            executive_summary="Summary",
            objectives=PRDSection(title="Objectives", content=""),
            scope=PRDSection(title="Scope", content=""),
            sections=[],
        )

        json_str = prd.to_json()
        data = json.loads(json_str)

        assert data["title"] == "Test PRD"
        assert "version" in data
        assert "created_at" in data

    def test_prd_document_from_json(self) -> None:
        """Test that PRD document deserializes from JSON."""
        json_str = json.dumps({
            "title": "From JSON",
            "version": "2.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "executive_summary": "Summary",
            "objectives": {"title": "Objectives", "content": "", "requirements": []},
            "scope": {"title": "Scope", "content": "", "requirements": []},
            "sections": [],
            "all_requirements": [],
        })

        prd = PRDDocument.from_json(json_str)

        assert prd.title == "From JSON"
        assert prd.version == "2.0.0"

    def test_prd_document_to_markdown(self) -> None:
        """Test that PRD document formats as markdown."""
        prd = PRDDocument.create(
            title="Test PRD",
            executive_summary="Executive summary content",
            objectives=PRDSection(title="Objectives", content="Objectives content"),
            scope=PRDSection(title="Scope", content="Scope content"),
            sections=[
                PRDSection(
                    title="Functional Requirements",
                    content="Functional content",
                    requirements=[
                        Requirement(
                            id="REQ-001",
                            description="Test requirement",
                            priority=RequirementPriority.MUST_HAVE,
                        )
                    ],
                )
            ],
        )

        md = prd.to_markdown()

        assert "# Test PRD" in md
        assert "## Executive Summary" in md
        assert "Executive summary content" in md
        assert "## Requirements Summary" in md
        assert "REQ-001" in md

    def test_prd_document_get_requirement_by_id(self) -> None:
        """Test that requirement can be retrieved by ID."""
        prd = PRDDocument.create(
            title="Test",
            executive_summary="",
            objectives=PRDSection(title="Objectives", content=""),
            scope=PRDSection(title="Scope", content=""),
            sections=[
                PRDSection(
                    title="Requirements",
                    content="",
                    requirements=[
                        Requirement(id="REQ-001", description="First"),
                        Requirement(id="REQ-002", description="Second"),
                    ],
                )
            ],
        )

        req = prd.get_requirement_by_id("REQ-002")
        assert req is not None
        assert req.description == "Second"

        missing = prd.get_requirement_by_id("REQ-999")
        assert missing is None


class TestAcceptanceCriterion:
    """Tests for AcceptanceCriterion model."""

    def test_criterion_creation(self) -> None:
        """Test that criterion can be created."""
        criterion = AcceptanceCriterion(
            id="AC-001",
            requirement_ids=["REQ-001"],
            given="a registered user",
            when="the user logs in with valid credentials",
            then="the user is authenticated and redirected to dashboard",
        )

        assert criterion.id == "AC-001"
        assert criterion.requirement_ids == ["REQ-001"]
        assert criterion.given == "a registered user"
        assert criterion.when == "the user logs in with valid credentials"
        assert criterion.then == "the user is authenticated and redirected to dashboard"

    def test_criterion_to_dict(self) -> None:
        """Test that criterion serializes to dictionary."""
        criterion = AcceptanceCriterion(
            id="AC-001",
            requirement_ids=["REQ-001", "REQ-002"],
            given="Given state",
            when="Action occurs",
            then="Expected outcome",
            notes="Some notes",
        )

        result = criterion.to_dict()

        assert result["id"] == "AC-001"
        assert result["requirement_ids"] == ["REQ-001", "REQ-002"]
        assert result["notes"] == "Some notes"

    def test_criterion_from_dict(self) -> None:
        """Test that criterion deserializes from dictionary."""
        data = {
            "id": "AC-002",
            "requirement_ids": ["REQ-001"],
            "given": "State",
            "when": "Action",
            "then": "Result",
            "notes": "",
        }

        criterion = AcceptanceCriterion.from_dict(data)

        assert criterion.id == "AC-002"

    def test_criterion_to_markdown(self) -> None:
        """Test that criterion formats as markdown."""
        criterion = AcceptanceCriterion(
            id="AC-001",
            requirement_ids=["REQ-001"],
            given="a registered user",
            when="the user logs in",
            then="the user is authenticated",
            notes="Important note",
        )

        md = criterion.to_markdown()

        assert "### AC-001" in md
        assert "**Given** a registered user" in md
        assert "**When** the user logs in" in md
        assert "**Then** the user is authenticated" in md
        assert "**Notes:** Important note" in md


class TestAcceptanceCriteria:
    """Tests for AcceptanceCriteria model."""

    def test_acceptance_criteria_create(self) -> None:
        """Test that acceptance criteria can be created with factory method."""
        criteria = [
            AcceptanceCriterion(
                id="AC-001",
                requirement_ids=["REQ-001"],
                given="Given",
                when="When",
                then="Then",
            ),
            AcceptanceCriterion(
                id="AC-002",
                requirement_ids=["REQ-001", "REQ-002"],
                given="Given",
                when="When",
                then="Then",
            ),
        ]

        doc = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=criteria,
            requirement_ids=["REQ-001", "REQ-002", "REQ-003"],
        )

        assert doc.prd_version == "1.0.0"
        assert len(doc.criteria) == 2
        assert len(doc.coverage_matrix) == 3

    def test_acceptance_criteria_coverage_levels(self) -> None:
        """Test that coverage levels are calculated correctly."""
        criteria = [
            AcceptanceCriterion(
                id="AC-001",
                requirement_ids=["REQ-001"],
                given="G",
                when="W",
                then="T",
            ),
            AcceptanceCriterion(
                id="AC-002",
                requirement_ids=["REQ-001"],
                given="G",
                when="W",
                then="T",
            ),
            AcceptanceCriterion(
                id="AC-003",
                requirement_ids=["REQ-002"],
                given="G",
                when="W",
                then="T",
            ),
        ]

        doc = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=criteria,
            requirement_ids=["REQ-001", "REQ-002", "REQ-003"],
        )

        # REQ-001 has 2 criteria = full coverage
        # REQ-002 has 1 criterion = partial coverage
        # REQ-003 has 0 criteria = no coverage
        coverage = {e.requirement_id: e.coverage_level for e in doc.coverage_matrix}

        assert coverage["REQ-001"] == "full"
        assert coverage["REQ-002"] == "partial"
        assert coverage["REQ-003"] == "none"

    def test_acceptance_criteria_get_uncovered_requirements(self) -> None:
        """Test that uncovered requirements are identified."""
        criteria = [
            AcceptanceCriterion(
                id="AC-001",
                requirement_ids=["REQ-001"],
                given="G",
                when="W",
                then="T",
            ),
        ]

        doc = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=criteria,
            requirement_ids=["REQ-001", "REQ-002", "REQ-003"],
        )

        uncovered = doc.get_uncovered_requirements()

        assert "REQ-002" in uncovered
        assert "REQ-003" in uncovered
        assert "REQ-001" not in uncovered

    def test_acceptance_criteria_get_coverage_percentage(self) -> None:
        """Test that coverage percentage is calculated correctly."""
        criteria = [
            AcceptanceCriterion(
                id="AC-001",
                requirement_ids=["REQ-001", "REQ-002"],
                given="G",
                when="W",
                then="T",
            ),
        ]

        doc = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=criteria,
            requirement_ids=["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
        )

        # 2 covered out of 4 = 50%
        assert doc.get_coverage_percentage() == 50.0

    def test_acceptance_criteria_to_json(self) -> None:
        """Test that acceptance criteria serializes to JSON."""
        doc = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=[],
            requirement_ids=["REQ-001"],
        )

        json_str = doc.to_json()
        data = json.loads(json_str)

        assert data["prd_version"] == "1.0.0"
        assert "coverage_matrix" in data


class TestDiscoveryResult:
    """Tests for DiscoveryResult model."""

    def test_discovery_result_succeeded(self) -> None:
        """Test that successful result can be created."""
        prd = PRDDocument.create(
            title="Test",
            executive_summary="",
            objectives=PRDSection(title="Obj", content=""),
            scope=PRDSection(title="Scope", content=""),
            sections=[],
        )
        acceptance = AcceptanceCriteria.create(
            prd_version="1.0.0",
            criteria=[],
            requirement_ids=[],
        )

        result = DiscoveryResult.succeeded(
            prd=prd,
            acceptance_criteria=acceptance,
            gate_request_id="gate-123",
        )

        assert result.success is True
        assert result.prd is not None
        assert result.acceptance_criteria is not None
        assert result.gate_request_id == "gate-123"

    def test_discovery_result_failed(self) -> None:
        """Test that failed result can be created."""
        result = DiscoveryResult.failed("Something went wrong")

        assert result.success is False
        assert result.error_message == "Something went wrong"
        assert result.prd is None
        assert result.acceptance_criteria is None

    def test_discovery_result_pending_approval(self) -> None:
        """Test that pending approval result can be created."""
        result = DiscoveryResult.pending_approval("gate-456")

        assert result.success is True
        assert result.gate_request_id == "gate-456"
        assert result.metadata["status"] == "pending_approval"
