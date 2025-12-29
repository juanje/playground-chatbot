"""CLI for Playground Chatbot.

This provides commands for running and inspecting the chatbot.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Load environment variables from .env file (for development)
load_dotenv()

console = Console()
error_console = Console(stderr=True)


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", "-v", is_flag=True, help="Show version and exit")
def cli(ctx: click.Context, version: bool) -> None:
    """Playground Chatbot - Playground for Agents"""
    if version:
        console.print("[bold cyan]Playground Chatbot[/] [dim]v0.1.0[/]")
        return

    # Show help if no subcommand
    if ctx.invoked_subcommand is None:
        _show_welcome()


def _show_welcome() -> None:
    """Show a welcome panel with available commands."""
    title = Text("Playground Chatbot", style="bold cyan")
    subtitle = Text("Playground for Agents", style="dim")

    commands_table = Table(show_header=False, box=None, padding=(0, 2))
    commands_table.add_column("Command", style="green")
    commands_table.add_column("Description", style="dim")

    commands_table.add_row("chat", "Start interactive CLI chat")
    commands_table.add_row("web", "Start web interface")
    commands_table.add_row("agents", "List registered agents")
    commands_table.add_row("info", "Show configuration")

    panel = Panel(
        commands_table,
        title=title,
        subtitle=subtitle,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)

    console.print("\n[dim]Examples:[/]")
    console.print("  [green]playground-chatbot chat[/]   Start CLI chat")
    console.print("  [green]playground-chatbot web[/]    Start web at localhost:8000")
    console.print("  [green]playground-chatbot --help[/] Show all options\n")


@cli.command(name="tools", hidden=True)
@click.pass_context
def tools_redirect(ctx: click.Context) -> None:
    """Redirect to agents command with helpful message."""
    console.print()
    console.print(
        "[yellow]💡 Tip:[/] Chatbots use [cyan]agents[/], not tools directly.\n"
        "   Each agent has its own tools. Showing agents instead:\n"
    )
    ctx.invoke(list_agents)


@cli.command(name="agents")
def list_agents() -> None:
    """List all registered agents and their capabilities."""
    # Lazy import to avoid loading heavy dependencies
    from . import agents

    registered = agents.get_registered_agents()

    console.print()
    if not registered:
        console.print(
            Panel(
                "[dim]No agents registered yet.\n\n"
                "Add agents in [white]src/playground_chatbot/agents.py[/][/]",
                title="[bold]🤖 Agents[/]",
                border_style="yellow",
            )
        )
        return

    table = Table(
        title="[bold]🤖 Registered Agents[/]",
        show_header=True,
        header_style="bold magenta",
        border_style="dim",
        title_justify="left",
    )
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Tools", style="green", justify="center")

    for agent_info in registered:
        name = agent_info.get("name", "Unknown")
        description = agent_info.get("description", "No description")
        tools_count = agent_info.get("tools_count", 0)
        table.add_row(name, description, str(tools_count))

    console.print(table)
    console.print(f"\n[dim]Total: {len(registered)} agents registered[/]\n")


@cli.command()
def info() -> None:
    """Show chatbot information and configuration."""
    # Lazy import
    from macsdk.core import ConfigurationError, create_config

    from . import agents

    console.print()

    # Build info content
    info_text = Text()
    info_text.append("Playground for Agents\n\n", style="dim")

    # Show config status
    try:
        config = create_config(search_path=Path.cwd())

        # Supervisor configuration
        info_text.append("Supervisor Model: ", style="dim")
        info_text.append(f"{config.llm_model}\n", style="cyan")
        info_text.append("Temperature: ", style="dim")
        info_text.append(f"{config.llm_temperature}\n", style="cyan")

        # Registered agents
        registered = agents.get_registered_agents()
        agent_names = [a.get("name", "?") for a in registered]
        info_text.append("Agents: ", style="dim")
        info_text.append(f"{', '.join(agent_names) or 'None'}\n", style="cyan")

        info_text.append("\n")
        info_text.append("✓ Configuration loaded successfully", style="green")

    except ConfigurationError as e:
        info_text.append(f"⚠ Configuration error: {e}", style="red")

    panel = Panel(
        info_text,
        title="[bold cyan]Playground Chatbot[/]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
    console.print(
        "\n[dim]Use[/] [green]playground-chatbot agents[/] "
        "[dim]to see agent details.[/]\n"
    )


@cli.command()
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode (show prompts)")
def chat(debug: bool) -> None:
    """Start interactive chat with the chatbot."""
    # Lazy import heavy dependencies
    from macsdk.core import ConfigurationError, create_chatbot_graph, create_config
    from macsdk.interfaces import run_cli_chatbot

    from . import agents

    try:
        # Load config from project root
        _config = create_config(search_path=Path.cwd())
        _config.validate_api_key()

        # Debug can be enabled via flag or config.yml
        debug_enabled = debug or _config.debug

        if debug_enabled:
            console.print("[yellow]🔍 Debug mode enabled[/]\n")

        graph = create_chatbot_graph(agents.register_all_agents, debug=debug_enabled)
        run_cli_chatbot(
            graph=graph,
            title="Playground Chatbot",
        )
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration Error:[/] {e}")
        sys.exit(1)


@cli.command()
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--port", "-p", default=8000, help="Port to bind to")
@click.option("--debug", "-d", is_flag=True, help="Enable debug mode (show prompts)")
def web(host: str, port: int, debug: bool) -> None:
    """Start the web interface.

    Launches a FastAPI server with WebSocket support for real-time chat.
    Open your browser at http://localhost:PORT after starting.
    """
    # Lazy import heavy dependencies
    from macsdk.core import ConfigurationError, create_chatbot_graph, create_config
    from macsdk.interfaces import run_web_server

    from . import agents

    try:
        _config = create_config(search_path=Path.cwd())
        _config.validate_api_key()

        # Debug can be enabled via flag or config.yml
        debug_enabled = debug or _config.debug

        # Look for static files in project root
        static_path = Path.cwd() / "static"
        static_dir: Path | None = static_path if static_path.exists() else None

        console.print()
        debug_msg = " [yellow](debug mode)[/]" if debug_enabled else ""
        console.print(
            Panel(
                f"[dim]Starting server at[/] [cyan]http://{host}:{port}[/]{debug_msg}\n"
                "[dim]Press[/] [white]Ctrl+C[/] [dim]to stop[/]",
                title="[bold cyan]🌐 Web Interface[/]",
                border_style="cyan",
            )
        )
        console.print()

        graph = create_chatbot_graph(agents.register_all_agents, debug=debug_enabled)
        run_web_server(
            graph=graph,
            title="Playground Chatbot",
            static_dir=static_dir,
            host=host,
            port=port,
        )
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration Error:[/] {e}")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
