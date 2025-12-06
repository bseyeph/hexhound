from __future__ import annotations

import typer

from . import __version__
from .cli_shell import launch_shell
from .server.app import run_server
from .core.taint_engine import trace_target

app = typer.Typer(help="HexHound blockchain forensics CLI")


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        launch_shell()


@app.command()
def version():
    """Show HexHound version."""
    typer.echo(f"HexHound v{__version__}")


@app.command()
def ui(
    port: int = typer.Option(
        8765, "--port", "-p", help="Port to serve the HexHound UI on."
    )
):
    """Start the HexHound UI (Flask + React)."""
    run_server(port=port)


@app.command()
def trace(
    target: str = typer.Argument(..., help="Wallet address or transaction hash."),
    depth: int = typer.Option(3, "--depth", "-d", help="Tracing depth (number of hops)."),
    chain: str = typer.Option(
        "eth-mainnet",
        "--chain",
        "-c",
        help="Chain identifier (e.g. eth-mainnet). EVM only for now.",
    ),
):
    """Run a one-shot taint trace from CLI (non-interactive)."""
    tg = trace_target(target=target, depth=depth, chain=chain)
    typer.echo(f"Nodes: {len(tg.nodes)}, edges: {len(tg.edges)}")
    for e in list(tg.edges)[:5]:
        typer.echo(f"{e.from_addr} -> {e.to_addr} [{e.amount} {e.token_symbol}]")


@app.command()
def sniff(
    interval: int = typer.Option(
        30, "--interval", "-i", help="Polling interval (seconds) for sniff mode."
    )
):
    """Run sniff mode (near real-time tracking)."""
    typer.echo(f"[placeholder] Starting sniff mode with interval {interval}s.")


def main():
    app()


if __name__ == "__main__":
    main()
