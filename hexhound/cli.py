from __future__ import annotations

import typer
import os

from . import __version__
from .cli_shell import launch_shell
from .server.app import run_server
from .core.taint_engine import trace_target

app = typer.Typer(
    help="HexHound blockchain forensics CLI"
)

# -------------------------------------------------------
# SHELL MODE (interactive)
# -------------------------------------------------------


@app.command()
def shell():
    """Start the interactive HexHound shell."""
    launch_shell()


# -------------------------------------------------------
# META COMMANDS
# -------------------------------------------------------

@app.command()
def version():
    """Show HexHound version."""
    typer.echo(f"HexHound v{__version__}")


@app.command("show-config")
def show_config():
    """
    Show current HexHound configuration.
    """
    depth = os.getenv("HEXHOUND_DEPTH", "default-shell-depth")
    window = os.getenv("HEXHOUND_SCAN_WINDOW", "default")
    autostop = os.getenv("HEXHOUND_AUTO_STOP", "enabled")

    typer.echo("\n[bold cyan]HexHound Configuration[/bold cyan]")
    typer.echo(f"Scan window:      {window}")
    typer.echo(f"Auto-stop:        {autostop}")
    typer.echo(f"Depth:            {depth}\n")


# -------------------------------------------------------
# UI COMMAND
# -------------------------------------------------------

@app.command()
def ui(
    port: int = typer.Option(
        8765, "--port", "-p", help="Port to serve the HexHound UI on."
    )
):
    """Start the HexHound UI (Flask + React)."""
    run_server(port=port)


# -------------------------------------------------------
# TRACE COMMAND
# -------------------------------------------------------

@app.command()
def trace(
    target: str = typer.Argument(...,
                                 help="Wallet address or transaction hash."),
    depth: int = typer.Option(
        3, "--depth", "-d", help="Tracing depth (number of hops)."),
    chain: str = typer.Option(
        "eth-mainnet",
        "--chain",
        "-c",
        help="Chain identifier (e.g. eth-mainnet). EVM only for now.",
    ),
    no_auto_stop: bool = False
):
    """Run a one-shot taint trace from CLI (non-interactive)."""
    if no_auto_stop:
        os.environ["HEXHOUND_AUTO_STOP"] = "disabled"
    tg = trace_target(target=target, depth=depth, chain=chain)
    typer.echo(f"Nodes: {len(tg.nodes)}, edges: {len(tg.edges)}")
    for e in list(tg.edges)[:5]:
        typer.echo(
            f"{e.from_addr} -> {e.to_addr} [{e.amount} {e.token_symbol}]")


# -------------------------------------------------------
# SNIFF COMMAND
# -------------------------------------------------------

@app.command()
def sniff(
    interval: int = typer.Option(
        30, "--interval", "-i", help="Polling interval (seconds) for sniff mode."
    )
):
    """Run sniff mode (near real-time tracking)."""
    typer.echo(f"[placeholder] Starting sniff mode with interval {interval}s.")


# -------------------------------------------------------
# SETTINGS
# -------------------------------------------------------

@app.command("set-window")
def set_window(blocks: int):
    """
    Set the scan window (number of blocks to look back).
    """
    os.environ["HEXHOUND_SCAN_WINDOW"] = str(blocks)
    typer.echo(f"Scan window set to {blocks} blocks.")


@app.command()
def autostop(
    mode: str = typer.Argument(..., help="'on' or 'off'")
):
    """
    Enable or disable auto-stop during block scanning.
    """
    mode = mode.lower()
    if mode not in ("on", "off"):
        typer.echo("Usage: hexhound autostop on|off")
        raise typer.Exit(1)

    if mode == "on":
        os.environ["HEXHOUND_AUTO_STOP"] = "enabled"
        typer.echo("Auto-stop enabled.")
    else:
        os.environ["HEXHOUND_AUTO_STOP"] = "disabled"
        typer.echo("Auto-stop disabled.")


def main():
    app()


if __name__ == "__main__":
    main()
