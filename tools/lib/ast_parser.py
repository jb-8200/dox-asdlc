#!/usr/bin/env python3
"""
AST parser - Extract code structure from Python files.

Parses Python AST and outputs standardized JSON format with:
- Function definitions and signatures
- Class definitions and methods
- Import statements
- Global variables
"""

import ast
import json
import sys
from pathlib import Path
from typing import Any


def extract_function_info(node: ast.FunctionDef, lineno: int) -> dict[str, Any]:
    """Extract function definition information."""
    args = node.args
    arg_names = [arg.arg for arg in args.args]
    return_annotation = (
        ast.unparse(node.returns) if node.returns else None
    )

    signature = f"{node.name}({', '.join(arg_names)})"
    if return_annotation:
        signature += f" -> {return_annotation}"

    return {
        "type": "function",
        "name": node.name,
        "line": lineno,
        "signature": signature,
    }


def extract_class_info(node: ast.ClassDef, lineno: int) -> dict[str, Any]:
    """Extract class definition information."""
    bases = [ast.unparse(base) for base in node.bases]
    methods = []

    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            methods.append(item.name)

    return {
        "type": "class",
        "name": node.name,
        "line": lineno,
        "bases": bases,
        "methods": methods,
    }


def extract_import_info(node: ast.Import | ast.ImportFrom, lineno: int) -> dict[str, Any]:
    """Extract import statement information."""
    if isinstance(node, ast.Import):
        modules = [alias.name for alias in node.names]
        return {
            "type": "import",
            "line": lineno,
            "modules": modules,
        }
    else:  # ImportFrom
        module = node.module or ""
        names = [alias.name for alias in node.names]
        return {
            "type": "from_import",
            "line": lineno,
            "module": module,
            "names": names,
        }


def extract_assign_info(node: ast.Assign, lineno: int) -> dict[str, Any]:
    """Extract global variable assignment information."""
    targets = []
    for target in node.targets:
        if isinstance(target, ast.Name):
            targets.append(target.id)
        elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
            for elt in target.elts:
                if isinstance(elt, ast.Name):
                    targets.append(elt.id)

    return {
        "type": "variable",
        "line": lineno,
        "names": targets,
    }


def parse_python_file(filepath: str) -> list[dict[str, Any]]:
    """Parse Python file and extract structure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        results = []

        for node in ast.walk(tree):
            lineno = getattr(node, "lineno", 0)

            if isinstance(node, ast.FunctionDef):
                # Only capture top-level functions
                if isinstance(node, ast.FunctionDef):
                    results.append(extract_function_info(node, lineno))
            elif isinstance(node, ast.ClassDef):
                results.append(extract_class_info(node, lineno))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                results.append(extract_import_info(node, lineno))
            elif isinstance(node, ast.Assign):
                # Only capture module-level assignments
                if node.col_offset == 0:
                    results.append(extract_assign_info(node, lineno))

        return results

    except SyntaxError as e:
        return [
            {
                "type": "error",
                "line": e.lineno or 0,
                "message": f"Syntax error: {e.msg}",
            }
        ]
    except Exception as e:
        return [
            {
                "type": "error",
                "line": 0,
                "message": f"Parse error: {str(e)}",
            }
        ]


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("[]")
        return

    filepath = sys.argv[1]

    if not Path(filepath).exists():
        print(json.dumps([{"type": "error", "message": f"File not found: {filepath}"}]))
        return

    results = parse_python_file(filepath)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
