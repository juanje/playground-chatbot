"""Local configuration for Playground Chatbot.

Extend MACSDKConfig to add your own settings.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import SettingsConfigDict

from macsdk.core import MACSDKConfig


def _find_project_root() -> Path:
    """Find the project root by looking for pyproject.toml.

    Returns:
        Path to the project root directory.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback to current file's parent if not found
    return current.parent


class PlaygroundChatbotConfig(MACSDKConfig):
    """Configuration for Playground Chatbot.

    Add your chatbot-specific settings here.
    They will be loaded from environment variables or .env file.

    Example:
        # In .env:
        MY_CUSTOM_SETTING=value

        # Access in code:
        from .config import config
        print(config.my_custom_setting)
    """

    # Add your custom settings here:
    # my_custom_setting: str | None = None
    # debug_mode: bool = False

    # Skills directory (relative to project root or absolute path)
    skills_dir: str | None = None

    # Facts directory (relative to project root or absolute path)
    facts_dir: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def skills_path(self) -> Path:
        """Get the resolved skills directory path.

        Priority:
        1. skills_dir from config.yml (if set)
        2. skills/ directory in project root (default)

        Returns:
            Resolved Path to the skills directory.
        """
        if self.skills_dir:
            skills_path = Path(self.skills_dir)
            # If relative path, resolve from project root
            if not skills_path.is_absolute():
                return _find_project_root() / skills_path
            return skills_path

        # Default: skills/ in project root
        return _find_project_root() / "skills"

    @property
    def facts_path(self) -> Path:
        """Get the resolved facts directory path.

        Priority:
        1. facts_dir from config.yml (if set)
        2. facts/ directory in project root (default)

        Returns:
            Resolved Path to the facts directory.
        """
        if self.facts_dir:
            facts_path = Path(self.facts_dir)
            # If relative path, resolve from project root
            if not facts_path.is_absolute():
                return _find_project_root() / facts_path
            return facts_path

        # Default: facts/ in project root
        return _find_project_root() / "facts"


config = PlaygroundChatbotConfig()
