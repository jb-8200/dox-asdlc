"""Dependency graph for tracking file and symbol dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.workers.repo_mapper.models import DependencyInfo, ParsedFile


@dataclass
class DependencyGraph:
    """Tracks dependencies between files and symbols.

    Builds a directed graph of file dependencies based on import statements.
    Supports querying dependencies (files that this file imports) and
    dependents (files that import this file).
    """

    _files: dict[str, ParsedFile] = field(default_factory=dict)
    _adjacency: dict[str, set[str]] = field(default_factory=dict)
    _reverse_adjacency: dict[str, set[str]] = field(default_factory=dict)

    def add_file(self, parsed: ParsedFile) -> None:
        """Add a parsed file to the dependency graph.

        Args:
            parsed: ParsedFile containing symbols and imports
        """
        self._files[parsed.path] = parsed

        # Initialize adjacency lists if not present
        if parsed.path not in self._adjacency:
            self._adjacency[parsed.path] = set()
        if parsed.path not in self._reverse_adjacency:
            self._reverse_adjacency[parsed.path] = set()

        # Process imports to build edges
        for import_info in parsed.imports:
            target_path = self._resolve_import(parsed.path, import_info.source)

            if target_path:
                # Add edge from parsed.path -> target_path
                self._adjacency[parsed.path].add(target_path)

                # Add reverse edge
                if target_path not in self._reverse_adjacency:
                    self._reverse_adjacency[target_path] = set()
                self._reverse_adjacency[target_path].add(parsed.path)

    def get_dependencies(
        self, file_path: str, max_depth: int = 3
    ) -> list[DependencyInfo]:
        """Get dependencies for a file up to max_depth.

        Args:
            file_path: Path to the file
            max_depth: Maximum depth to traverse (0 = no dependencies)

        Returns:
            List of DependencyInfo objects for dependencies
        """
        if file_path not in self._adjacency:
            return []

        dependencies: list[DependencyInfo] = []
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(file_path, 0)]

        while queue:
            current, depth = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Skip the source file itself
            if current == file_path:
                depth_for_deps = 0
            else:
                # Add to dependencies if not the source file
                source_file = self._find_source_for_dependency(
                    file_path, current, visited
                )
                if source_file and current in self._files:
                    parsed = self._files[current]
                    dependencies.append(
                        DependencyInfo(
                            source_file=source_file,
                            target_file=current,
                            imported_symbols=parsed.exports,
                            depth=depth,
                        )
                    )

                depth_for_deps = depth

            # Add neighbors if we haven't reached max depth
            if depth_for_deps < max_depth:
                for neighbor in self._adjacency.get(current, []):
                    if neighbor not in visited:
                        queue.append((neighbor, depth_for_deps + 1))

        return dependencies

    def get_dependents(
        self, file_path: str, max_depth: int = 2
    ) -> list[DependencyInfo]:
        """Get symbols that depend on the given file.

        Args:
            file_path: Path to the file
            max_depth: Maximum depth to traverse

        Returns:
            List of DependencyInfo for files that depend on this file
        """
        if file_path not in self._reverse_adjacency:
            return []

        dependents: list[DependencyInfo] = []
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(file_path, 0)]

        while queue:
            current, depth = queue.pop(0)

            if current in visited:
                continue

            visited.add(current)

            # Skip the source file itself
            if current != file_path and current in self._files:
                parsed = self._files[file_path]
                dependents.append(
                    DependencyInfo(
                        source_file=current,
                        target_file=file_path,
                        imported_symbols=parsed.exports,
                        depth=depth,
                    )
                )

            # Add reverse neighbors if we haven't reached max depth
            if depth < max_depth:
                for neighbor in self._reverse_adjacency.get(current, []):
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))

        return dependents

    def _resolve_import(self, source_path: str, import_source: str) -> str | None:
        """Resolve an import statement to an absolute file path.

        Args:
            source_path: Path to the file containing the import
            import_source: Import source string (e.g., "os", ".models")

        Returns:
            Resolved absolute path, or None if not resolvable
        """
        # Handle relative imports
        if import_source.startswith("."):
            return self._resolve_relative_import(source_path, import_source)

        # Handle absolute imports - try to find in known files
        for file_path in self._files:
            # Simple heuristic: check if import_source appears in the path
            if import_source.replace(".", "/") in file_path:
                return file_path

        # For external modules (os, sys, etc.) we don't resolve
        return None

    def _resolve_relative_import(
        self, source_path: str, import_source: str
    ) -> str | None:
        """Resolve a relative import to absolute path.

        Args:
            source_path: Path to file with relative import
            import_source: Relative import string (e.g., ".models", "..utils")

        Returns:
            Resolved absolute path or None
        """
        source_dir = Path(source_path).parent

        # Count leading dots
        dots = len(import_source) - len(import_source.lstrip("."))
        relative_module = import_source[dots:]

        # Go up directories based on dot count
        target_dir = source_dir
        for _ in range(dots - 1):
            target_dir = target_dir.parent

        # Build target path
        if relative_module:
            target_path = target_dir / f"{relative_module.replace('.', '/')}.py"
        else:
            target_path = target_dir / "__init__.py"

        # Check if resolved path exists in our files
        target_str = str(target_path)
        if target_str in self._files:
            return target_str

        # Try without .py extension
        alt_target = str(target_dir / relative_module.replace(".", "/"))
        if alt_target in self._files:
            return alt_target

        return None

    def _find_source_for_dependency(
        self, origin: str, target: str, visited: set[str]
    ) -> str:
        """Find the immediate source file that imports the target.

        Args:
            origin: Original file we're querying dependencies for
            target: Target dependency file
            visited: Set of visited files

        Returns:
            Source file path
        """
        # For simplicity, return origin as the source
        # In a more complex implementation, we would track the exact path
        return origin

    def to_dict(self) -> dict[str, Any]:
        """Convert dependency graph to dictionary for serialization.

        Returns:
            Dictionary representation of the graph
        """
        edges = []
        for source, targets in self._adjacency.items():
            for target in targets:
                edges.append({"source": source, "target": target})

        return {
            "files": list(self._files.keys()),
            "edges": edges,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DependencyGraph:
        """Create dependency graph from dictionary.

        Args:
            data: Dictionary with graph data

        Returns:
            DependencyGraph instance
        """
        graph = cls()

        # Rebuild adjacency from edges
        for edge in data.get("edges", []):
            source = edge["source"]
            target = edge["target"]

            if source not in graph._adjacency:
                graph._adjacency[source] = set()
            graph._adjacency[source].add(target)

            if target not in graph._reverse_adjacency:
                graph._reverse_adjacency[target] = set()
            graph._reverse_adjacency[target].add(source)

        return graph
