"""Tools for the agent.

This agent uses MACSDK's generic tools directly:
- api_get: For REST API calls
- fetch_file: For downloading files (logs, configs, etc.)

The API schema is described in the system prompt, letting the LLM
decide which endpoints to call based on user queries.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import yaml
from langchain_core.tools import tool
from simpleeval import simple_eval  # type: ignore[import-untyped]

# Import generic tools from MACSDK
from macsdk.tools import api_get, fetch_file

from playground_chatbot.config import config

# =============================================================================
# SERVICE REGISTRATION
# =============================================================================

_api_registered = False

# Skills directory resolved from configuration
SKILLS_DIR = config.skills_path

# Facts directory resolved from configuration
FACTS_DIR = config.facts_path


def _ensure_api_registered() -> None:
    """Register the API service on first use."""
    global _api_registered
    if not _api_registered:
        from macsdk.core.api_registry import register_api_service

        # Register DevOps Mock API as a service
        # Replace with your own API endpoint for production use
        register_api_service(
            name="devops",
            base_url="https://my-json-server.typicode.com/juanje/devops-mock-api",
            timeout=10,
            max_retries=2,
        )
        _api_registered = True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _safe_path(base_dir: Path, relative_path: str) -> Path:
    """Resolve a path safely, preventing directory traversal attacks.

    Args:
        base_dir: The base directory that paths must stay within.
        relative_path: The user-provided relative path.

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If the path attempts to escape the base directory.
    """
    # Resolve both paths to absolute
    base_resolved = base_dir.resolve()
    target_resolved = (base_dir / relative_path).resolve()

    # Ensure the target is within the base directory
    if not str(target_resolved).startswith(str(base_resolved)):
        raise ValueError(f"Path traversal detected: '{relative_path}'")

    return target_resolved


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Uses yaml.safe_load for robust parsing, supporting:
    - Values with colons
    - Quoted strings
    - Multi-line values
    - Nested YAML structures

    Expected format:
    ---
    name: my-name
    description: My description
    ---
    <content>

    Args:
        content: The full file content.

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter).
    """
    # Check if file starts with frontmatter delimiter
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        return {}, content

    # Find the closing delimiter (skip first line)
    lines = content.split("\n")
    end_index = -1

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index == -1:
        return {}, content

    # Extract and parse frontmatter
    frontmatter_text = "\n".join(lines[1:end_index])
    content_without = "\n".join(lines[end_index + 1 :]).strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_text) or {}
    except yaml.YAMLError:
        # Fall back to empty frontmatter on parse error
        frontmatter = {}

    return frontmatter, content_without


def _read_file_content(file_path: Path) -> tuple[dict[str, Any], str]:
    """Read a file and return its frontmatter and content.

    Args:
        file_path: Path to the file to read.

    Returns:
        Tuple of (frontmatter_dict, content_without_frontmatter).

    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return _parse_frontmatter(content)


def _list_documents(directory: Path) -> list[dict[str, str]]:
    """List markdown documents with frontmatter in a directory.

    Searches recursively for .md files and extracts their metadata
    from YAML frontmatter.

    Args:
        directory: The directory to search.

    Returns:
        List of documents with name, description, and path.
    """
    documents = []
    for file in directory.rglob("*.md"):
        try:
            frontmatter, _ = _read_file_content(file)
            if "name" in frontmatter:
                relative_path = file.relative_to(directory)
                documents.append(
                    {
                        "name": str(frontmatter.get("name", "")),
                        "description": str(frontmatter.get("description", "")),
                        "path": str(relative_path),
                    }
                )
        except Exception:
            # Skip files that can't be read
            continue
    return documents


def _read_document(base_dir: Path, path: str, doc_type: str) -> str:
    """Read a document safely, with LLM-friendly error messages.

    Args:
        base_dir: The base directory for the document type.
        path: The relative path to the document.
        doc_type: The type of document (for error messages).

    Returns:
        The document content, or an error message if not found.
    """
    try:
        file_path = _safe_path(base_dir, path)
        _, content = _read_file_content(file_path)
        return content
    except FileNotFoundError:
        return f"Error: {doc_type.capitalize()} '{path}' not found. Use list_{doc_type}s() to see available {doc_type}s."
    except ValueError as e:
        return f"Error: Invalid path - {e}"


# =============================================================================
# MATH CALCULATION SETUP
# =============================================================================

# Safe math functions to expose
SAFE_MATH_FUNCTIONS = {
    # Basic math
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
    # From math module
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "degrees": math.degrees,
    "radians": math.radians,
}

# Safe constants
SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}


# =============================================================================
# TOOLS
# =============================================================================


@tool
def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression using Python syntax.

    Use this tool whenever you need to perform calculations. LLMs are not
    reliable for math, so always use this tool for any numeric computation.

    Supported operations:
    - Arithmetic: +, -, *, /, //, %, **
    - Comparisons: <, >, <=, >=, ==, !=
    - Functions: sqrt, sin, cos, tan, log, log10, log2, exp, abs, round, min,
      max, sum, pow, floor, ceil, factorial, gcd, degrees, radians
    - Constants: pi, e, tau, inf

    Args:
        expression: A Python math expression (e.g., "sqrt(16) + 2**3",
                    "sin(pi/2)", "(100 * 15) / 100")

    Returns:
        The result of the calculation as a string, or an error message if invalid.

    Examples:
        calculate("2 + 2") → "4"
        calculate("sqrt(16) * 2") → "8.0"
        calculate("sin(pi/2)") → "1.0"
        calculate("(1000 * 0.15) + 500") → "650.0"
        calculate("factorial(5)") → "120"
    """
    # Validate input
    if not expression or not expression.strip():
        return (
            "Error: Empty expression provided. Please provide a valid math expression."
        )

    expression = expression.strip()

    try:
        # Use simpleeval with custom functions and names
        result = simple_eval(
            expression,
            functions=SAFE_MATH_FUNCTIONS,
            names=SAFE_CONSTANTS,
        )
        return str(result)
    except ZeroDivisionError:
        return f"Error: Division by zero in expression '{expression}'"
    except NameError as e:
        return f"Error: Unknown function or variable in '{expression}' - {e}"
    except SyntaxError:
        return f"Error: Invalid syntax in expression '{expression}'"
    except Exception as e:
        return f"Error: Cannot evaluate '{expression}' - {e}"


@tool
def list_skills() -> list[dict[str, str]]:
    """List available skills that describe how to perform specific tasks.

    Use this when you need to discover what specialized capabilities or task
    instructions are available. Each skill contains step-by-step guidance for
    accomplishing a particular type of work.

    Skills may be organized hierarchically (general → specific). Use general
    skills first for overview, then specific skills for deep investigation.

    Returns:
        List of available skills with name, description, and path (relative to skills directory).
    """
    return _list_documents(SKILLS_DIR)


@tool
def list_facts() -> list[dict[str, str]]:
    """List available facts that provide contextual information on specific topics.

    Use this to discover what background knowledge, reference information, or
    domain-specific data is available. Facts help provide accurate context when
    working on tasks.

    Returns:
        List of available facts with name, description, and path (relative to facts directory).
    """
    return _list_documents(FACTS_DIR)


@tool
def read_skill(path: str) -> str:
    """Get detailed instructions on how to perform a specific task or capability.

    Use this after finding a relevant skill with list_skills(). The returned
    instructions will guide you through completing that type of task, including
    guidelines, examples, and best practices.

    Skills may reference other more specific skills for progressive disclosure.

    Args:
        path: The path from list_skills() (e.g., 'deploy-service.md' or
              'check-service-health/api-gateway.md').

    Returns:
        Complete instructions and guidelines for performing the task.
    """
    return _read_document(SKILLS_DIR, path, "skill")


@tool
def read_fact(path: str) -> str:
    """Get contextual information and reference data about a specific topic.

    Use this after finding a relevant fact with list_facts(). The returned
    information provides background knowledge, domain-specific details, or
    reference data needed to work accurately on tasks.

    Args:
        path: The path from list_facts() (e.g., 'api-endpoints.md' or
              'services/database-info.md').

    Returns:
        Detailed information and context about the topic.
    """
    return _read_document(FACTS_DIR, path, "fact")


def get_tools() -> list:
    """Get the tools for this agent, ensuring API is registered.

    Returns:
        List of generic tools from this agent.
    """
    _ensure_api_registered()
    return [
        api_get,
        fetch_file,
        calculate,
        list_skills,
        list_facts,
        read_skill,
        read_fact,
    ]


# Tools exposed for CLI inspection
TOOLS = get_tools()
