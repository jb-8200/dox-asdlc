"""Domain models for Discovery agents.

Defines data structures for PRD documents and acceptance criteria
produced by the discovery phase agents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RequirementPriority(str, Enum):
    """Priority levels for requirements."""

    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"
    WONT_HAVE = "wont_have"


class RequirementType(str, Enum):
    """Types of requirements."""

    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    CONSTRAINT = "constraint"
    ASSUMPTION = "assumption"


@dataclass
class Requirement:
    """Individual requirement extracted from user input.

    Attributes:
        id: Unique requirement identifier (e.g., REQ-001).
        description: Full description of the requirement.
        priority: MoSCoW priority level.
        type: Requirement type classification.
        rationale: Explanation of why this requirement exists.
        source: Where the requirement came from.
        metadata: Additional requirement metadata.
    """

    id: str
    description: str
    priority: RequirementPriority = RequirementPriority.SHOULD_HAVE
    type: RequirementType = RequirementType.FUNCTIONAL
    rationale: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize requirement to dictionary."""
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority.value,
            "type": self.type.value,
            "rationale": self.rationale,
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Requirement:
        """Create requirement from dictionary."""
        return cls(
            id=data.get("id", ""),
            description=data.get("description", ""),
            priority=RequirementPriority(data.get("priority", "should_have")),
            type=RequirementType(data.get("type", "functional")),
            rationale=data.get("rationale", ""),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )

    def to_markdown(self) -> str:
        """Format requirement as markdown."""
        lines = [
            f"### {self.id}: {self.description[:50]}...",
            "",
            f"**Priority:** {self.priority.value.replace('_', ' ').title()}",
            f"**Type:** {self.type.value.replace('_', ' ').title()}",
            "",
            self.description,
        ]
        if self.rationale:
            lines.extend(["", f"**Rationale:** {self.rationale}"])
        return "\n".join(lines)


@dataclass
class PRDSection:
    """Section of a PRD document.

    Attributes:
        title: Section title.
        content: Section content as markdown.
        requirements: Requirements covered in this section.
        subsections: Nested subsections.
    """

    title: str
    content: str
    requirements: list[Requirement] = field(default_factory=list)
    subsections: list[PRDSection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize section to dictionary."""
        return {
            "title": self.title,
            "content": self.content,
            "requirements": [r.to_dict() for r in self.requirements],
            "subsections": [s.to_dict() for s in self.subsections],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PRDSection:
        """Create section from dictionary."""
        return cls(
            title=data.get("title", ""),
            content=data.get("content", ""),
            requirements=[
                Requirement.from_dict(r) for r in data.get("requirements", [])
            ],
            subsections=[
                PRDSection.from_dict(s) for s in data.get("subsections", [])
            ],
        )

    def to_markdown(self, level: int = 2) -> str:
        """Format section as markdown.

        Args:
            level: Heading level (2-6).

        Returns:
            str: Markdown formatted section.
        """
        prefix = "#" * min(level, 6)
        lines = [f"{prefix} {self.title}", "", self.content]

        if self.requirements:
            lines.extend(["", f"{'#' * min(level + 1, 6)} Requirements", ""])
            for req in self.requirements:
                lines.append(f"- **{req.id}**: {req.description}")

        for subsection in self.subsections:
            lines.extend(["", subsection.to_markdown(level + 1)])

        return "\n".join(lines)


@dataclass
class PRDDocument:
    """Complete Product Requirements Document.

    Attributes:
        title: Document title.
        version: Document version.
        created_at: Creation timestamp.
        executive_summary: Brief overview of the project.
        objectives: Project objectives section.
        scope: Scope section (in/out of scope).
        sections: Main content sections.
        all_requirements: Flat list of all requirements.
        metadata: Additional document metadata.
    """

    title: str
    version: str
    created_at: datetime
    executive_summary: str
    objectives: PRDSection
    scope: PRDSection
    sections: list[PRDSection]
    all_requirements: list[Requirement] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        title: str,
        executive_summary: str,
        objectives: PRDSection,
        scope: PRDSection,
        sections: list[PRDSection],
        version: str = "1.0.0",
    ) -> PRDDocument:
        """Create a new PRD document.

        Args:
            title: Document title.
            executive_summary: Brief overview.
            objectives: Objectives section.
            scope: Scope section.
            sections: Content sections.
            version: Document version.

        Returns:
            PRDDocument: New PRD document.
        """
        # Collect all requirements from sections
        all_requirements: list[Requirement] = []

        def collect_requirements(section: PRDSection) -> None:
            all_requirements.extend(section.requirements)
            for subsection in section.subsections:
                collect_requirements(subsection)

        collect_requirements(objectives)
        collect_requirements(scope)
        for section in sections:
            collect_requirements(section)

        return cls(
            title=title,
            version=version,
            created_at=datetime.now(timezone.utc),
            executive_summary=executive_summary,
            objectives=objectives,
            scope=scope,
            sections=sections,
            all_requirements=all_requirements,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize document to dictionary."""
        return {
            "title": self.title,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "executive_summary": self.executive_summary,
            "objectives": self.objectives.to_dict(),
            "scope": self.scope.to_dict(),
            "sections": [s.to_dict() for s in self.sections],
            "all_requirements": [r.to_dict() for r in self.all_requirements],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PRDDocument:
        """Create document from dictionary."""
        return cls(
            title=data.get("title", ""),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            executive_summary=data.get("executive_summary", ""),
            objectives=PRDSection.from_dict(data.get("objectives", {})),
            scope=PRDSection.from_dict(data.get("scope", {})),
            sections=[PRDSection.from_dict(s) for s in data.get("sections", [])],
            all_requirements=[
                Requirement.from_dict(r) for r in data.get("all_requirements", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize document to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> PRDDocument:
        """Create document from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_markdown(self) -> str:
        """Format document as markdown.

        Returns:
            str: Complete markdown document.
        """
        lines = [
            f"# {self.title}",
            "",
            f"**Version:** {self.version}",
            f"**Created:** {self.created_at.strftime('%Y-%m-%d')}",
            "",
            "## Executive Summary",
            "",
            self.executive_summary,
            "",
            self.objectives.to_markdown(),
            "",
            self.scope.to_markdown(),
        ]

        for section in self.sections:
            lines.extend(["", section.to_markdown()])

        # Add requirements summary
        if self.all_requirements:
            lines.extend([
                "",
                "## Requirements Summary",
                "",
                "| ID | Description | Priority | Type |",
                "|---|---|---|---|",
            ])
            for req in self.all_requirements:
                desc = req.description[:50] + "..." if len(req.description) > 50 else req.description
                lines.append(
                    f"| {req.id} | {desc} | {req.priority.value} | {req.type.value} |"
                )

        return "\n".join(lines)

    def get_requirement_by_id(self, req_id: str) -> Requirement | None:
        """Get a requirement by its ID."""
        for req in self.all_requirements:
            if req.id == req_id:
                return req
        return None


@dataclass
class AcceptanceCriterion:
    """Single acceptance criterion in Given-When-Then format.

    Attributes:
        id: Unique criterion identifier.
        requirement_ids: IDs of requirements this criterion validates.
        given: Precondition description.
        when: Action description.
        then: Expected outcome description.
        notes: Additional notes or edge cases.
        metadata: Additional criterion metadata.
    """

    id: str
    requirement_ids: list[str]
    given: str
    when: str
    then: str
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize criterion to dictionary."""
        return {
            "id": self.id,
            "requirement_ids": self.requirement_ids,
            "given": self.given,
            "when": self.when,
            "then": self.then,
            "notes": self.notes,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcceptanceCriterion:
        """Create criterion from dictionary."""
        return cls(
            id=data.get("id", ""),
            requirement_ids=data.get("requirement_ids", []),
            given=data.get("given", ""),
            when=data.get("when", ""),
            then=data.get("then", ""),
            notes=data.get("notes", ""),
            metadata=data.get("metadata", {}),
        )

    def to_markdown(self) -> str:
        """Format criterion as markdown."""
        lines = [
            f"### {self.id}",
            "",
            f"**Requirements:** {', '.join(self.requirement_ids)}",
            "",
            f"**Given** {self.given}",
            f"**When** {self.when}",
            f"**Then** {self.then}",
        ]
        if self.notes:
            lines.extend(["", f"**Notes:** {self.notes}"])
        return "\n".join(lines)


@dataclass
class CoverageEntry:
    """Coverage mapping entry.

    Attributes:
        requirement_id: Requirement being covered.
        criterion_ids: Criteria that cover this requirement.
        coverage_level: Coverage assessment (full, partial, none).
    """

    requirement_id: str
    criterion_ids: list[str]
    coverage_level: str = "full"

    def to_dict(self) -> dict[str, Any]:
        """Serialize entry to dictionary."""
        return {
            "requirement_id": self.requirement_id,
            "criterion_ids": self.criterion_ids,
            "coverage_level": self.coverage_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoverageEntry:
        """Create entry from dictionary."""
        return cls(
            requirement_id=data.get("requirement_id", ""),
            criterion_ids=data.get("criterion_ids", []),
            coverage_level=data.get("coverage_level", "full"),
        )


@dataclass
class AcceptanceCriteria:
    """Collection of acceptance criteria with coverage matrix.

    Attributes:
        prd_version: Version of PRD these criteria were generated from.
        created_at: Creation timestamp.
        criteria: List of acceptance criteria.
        coverage_matrix: Mapping of requirements to criteria.
        metadata: Additional metadata.
    """

    prd_version: str
    created_at: datetime
    criteria: list[AcceptanceCriterion]
    coverage_matrix: list[CoverageEntry]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        prd_version: str,
        criteria: list[AcceptanceCriterion],
        requirement_ids: list[str],
    ) -> AcceptanceCriteria:
        """Create acceptance criteria with auto-generated coverage matrix.

        Args:
            prd_version: Version of source PRD.
            criteria: List of acceptance criteria.
            requirement_ids: All requirement IDs from PRD.

        Returns:
            AcceptanceCriteria: New acceptance criteria document.
        """
        # Build coverage matrix
        coverage: dict[str, list[str]] = {req_id: [] for req_id in requirement_ids}

        for criterion in criteria:
            for req_id in criterion.requirement_ids:
                if req_id in coverage:
                    coverage[req_id].append(criterion.id)

        coverage_matrix = []
        for req_id, criterion_ids in coverage.items():
            if not criterion_ids:
                level = "none"
            elif len(criterion_ids) >= 2:
                level = "full"
            else:
                level = "partial"

            coverage_matrix.append(CoverageEntry(
                requirement_id=req_id,
                criterion_ids=criterion_ids,
                coverage_level=level,
            ))

        return cls(
            prd_version=prd_version,
            created_at=datetime.now(timezone.utc),
            criteria=criteria,
            coverage_matrix=coverage_matrix,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "prd_version": self.prd_version,
            "created_at": self.created_at.isoformat(),
            "criteria": [c.to_dict() for c in self.criteria],
            "coverage_matrix": [e.to_dict() for e in self.coverage_matrix],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AcceptanceCriteria:
        """Create from dictionary."""
        return cls(
            prd_version=data.get("prd_version", ""),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.now(timezone.utc).isoformat())
            ),
            criteria=[
                AcceptanceCriterion.from_dict(c) for c in data.get("criteria", [])
            ],
            coverage_matrix=[
                CoverageEntry.from_dict(e) for e in data.get("coverage_matrix", [])
            ],
            metadata=data.get("metadata", {}),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> AcceptanceCriteria:
        """Create from JSON string."""
        return cls.from_dict(json.loads(json_str))

    def to_markdown(self) -> str:
        """Format as markdown document."""
        lines = [
            "# Acceptance Criteria",
            "",
            f"**PRD Version:** {self.prd_version}",
            f"**Created:** {self.created_at.strftime('%Y-%m-%d')}",
            "",
            "## Criteria",
        ]

        for criterion in self.criteria:
            lines.extend(["", criterion.to_markdown()])

        # Add coverage matrix
        lines.extend([
            "",
            "## Coverage Matrix",
            "",
            "| Requirement | Criteria | Coverage |",
            "|---|---|---|",
        ])

        for entry in self.coverage_matrix:
            criteria_str = ", ".join(entry.criterion_ids) or "None"
            lines.append(
                f"| {entry.requirement_id} | {criteria_str} | {entry.coverage_level} |"
            )

        # Add coverage summary
        full = sum(1 for e in self.coverage_matrix if e.coverage_level == "full")
        partial = sum(1 for e in self.coverage_matrix if e.coverage_level == "partial")
        none = sum(1 for e in self.coverage_matrix if e.coverage_level == "none")
        total = len(self.coverage_matrix)

        lines.extend([
            "",
            "## Coverage Summary",
            "",
            f"- **Full coverage:** {full}/{total} ({full * 100 // total if total else 0}%)",
            f"- **Partial coverage:** {partial}/{total}",
            f"- **No coverage:** {none}/{total}",
        ])

        return "\n".join(lines)

    def get_uncovered_requirements(self) -> list[str]:
        """Get list of requirements with no coverage."""
        return [
            entry.requirement_id
            for entry in self.coverage_matrix
            if entry.coverage_level == "none"
        ]

    def get_coverage_percentage(self) -> float:
        """Get overall coverage percentage."""
        if not self.coverage_matrix:
            return 0.0

        covered = sum(
            1 for e in self.coverage_matrix
            if e.coverage_level in ("full", "partial")
        )
        return (covered / len(self.coverage_matrix)) * 100


@dataclass
class DiscoveryResult:
    """Result from the discovery workflow.

    Attributes:
        success: Whether discovery completed successfully.
        prd: Generated PRD document (if successful).
        acceptance_criteria: Generated criteria (if successful).
        error_message: Error description (if failed).
        gate_request_id: HITL gate request ID (if submitted).
        metadata: Additional result metadata.
    """

    success: bool
    prd: PRDDocument | None = None
    acceptance_criteria: AcceptanceCriteria | None = None
    error_message: str | None = None
    gate_request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def succeeded(
        cls,
        prd: PRDDocument,
        acceptance_criteria: AcceptanceCriteria,
        gate_request_id: str | None = None,
    ) -> DiscoveryResult:
        """Create successful result."""
        return cls(
            success=True,
            prd=prd,
            acceptance_criteria=acceptance_criteria,
            gate_request_id=gate_request_id,
        )

    @classmethod
    def failed(cls, error_message: str) -> DiscoveryResult:
        """Create failed result."""
        return cls(
            success=False,
            error_message=error_message,
        )

    @classmethod
    def pending_approval(cls, gate_request_id: str) -> DiscoveryResult:
        """Create result pending HITL approval."""
        return cls(
            success=True,
            gate_request_id=gate_request_id,
            metadata={"status": "pending_approval"},
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "prd": self.prd.to_dict() if self.prd else None,
            "acceptance_criteria": (
                self.acceptance_criteria.to_dict() if self.acceptance_criteria else None
            ),
            "error_message": self.error_message,
            "gate_request_id": self.gate_request_id,
            "metadata": self.metadata,
        }
