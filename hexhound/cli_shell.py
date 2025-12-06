from __future__ import annotations

import random
import os

import cmd2
from rich.console import Console

from .banners import BANNERS
from . import __version__
from .core.taint_engine import trace_target
from .server.app import run_server_process

console = Console()


class HexHoundShell(cmd2.Cmd):
    prompt = "HexHound > "

    def __init__(self):
        super().__init__(allow_cli_args=False)
        self.intro = self._render_intro()
        self.depth: int = 3
        self.targets: list[dict] = []  # {chain, address}
        self.sniffing: bool = False

    def _render_intro(self) -> str:
        banner = random.choice(BANNERS)
        return banner + f"HexHound v{__version__} — type 'help' to list commands.\n"

    # ---------------------------------------------------
    # TARGET MANAGEMENT
    # ---------------------------------------------------

    def do_add(self, arg: str) -> None:
        """add <chain> <address>

        Add a tracking target, e.g.:

            add eth-mainnet 0xabc123...
        """
        parts = arg.split()
        if len(parts) != 2:
            console.print("[red]Usage:[/red] add <chain> <address>")
            return
        chain, address = parts
        self.targets.append({"chain": chain, "address": address})
        console.print(f"[green]Added target[/green] {address} on {chain}.")

    def do_list(self, arg: str) -> None:
        """list

        List current targets.
        """
        if not self.targets:
            console.print("[yellow]No targets configured.[/yellow]")
            return
        for idx, t in enumerate(self.targets, start=1):
            console.print(f"{idx}. {t['chain']} :: {t['address']}")

    # ---------------------------------------------------
    # SETTINGS
    # ---------------------------------------------------

    def do_set(self, arg: str) -> None:
        """set depth <N>

        Set tracing depth (number of hops).
        """
        parts = arg.split()
        if len(parts) != 2 or parts[0] != "depth":
            console.print("[red]Usage:[/red] set depth <N>")
            return
        try:
            self.depth = int(parts[1])
        except ValueError:
            console.print("[red]Depth must be an integer.[/red]")
            return
        console.print(f"[green]Depth set to {self.depth}[/green]")

    def do_window(self, arg: str) -> None:
        """window <blocks>

        Set the scan window (how many blocks back we search).
        """
        arg = arg.strip()
        if not arg:
            console.print("[red]Usage:[/red] window <blocks>")
            return

        try:
            blocks = int(arg)
        except ValueError:
            console.print("[red]Scan window must be an integer.[/red]")
            return

        os.environ["HEXHOUND_SCAN_WINDOW"] = str(blocks)
        console.print(f"[green]Scan window set to {blocks} blocks.[/green]")

    def do_autostop(self, arg: str) -> None:
        """autostop on|off

        Enable or disable auto-stop for log scanning.
        """
        arg = arg.strip().lower()
        if arg not in ("on", "off"):
            console.print("[red]Usage:[/red] autostop on|off")
            return

        if arg == "on":
            os.environ["HEXHOUND_AUTO_STOP"] = "enabled"
            console.print("[green]Auto-stop enabled.[/green]")
        else:
            os.environ["HEXHOUND_AUTO_STOP"] = "disabled"
            console.print("[yellow]Auto-stop disabled.[/yellow]")

    def do_show(self, arg: str) -> None:
        """show

        Display current HexHound runtime configuration.
        """
        window = os.getenv("HEXHOUND_SCAN_WINDOW", "default")
        autostop = os.getenv("HEXHOUND_AUTO_STOP", "enabled")

        console.print("\n[bold cyan]HexHound Configuration[/bold cyan]")
        console.print(f"Scan window:      {window}")
        console.print(f"Auto-stop:        {autostop}")
        console.print(f"Depth:            {self.depth}")
        console.print(f"Targets:          {len(self.targets)}\n")

    # ---------------------------------------------------
    # EXECUTION
    # ---------------------------------------------------

    def do_run(self, arg: str) -> None:
        """run trace

        Run taint trace on configured targets (EVM-only for now).
        """
        parts = arg.split()
        if not parts or parts[0] != "trace":
            console.print("[red]Usage:[/red] run trace")
            return

        if not self.targets:
            console.print(
                "[yellow]No targets configured. Use 'add' first.[/yellow]")
            return

        for t in self.targets:
            chain = t["chain"]
            address = t["address"]
            console.print(
                f"[cyan]Tracing[/cyan] {address} on {chain} with depth {self.depth}..."
            )
            try:
                tg = trace_target(
                    target=address, depth=self.depth, chain=chain
                )
            except Exception as e:
                console.print(f"[red]Error tracing {address}: {e}[/red]")
                continue

            console.print(
                f"[green]Trace complete[/green] — nodes: {len(tg.nodes)}, edges: {len(tg.edges)}"
            )

    # ---------------------------------------------------
    # UI MANAGEMENT
    # ---------------------------------------------------

    def do_sniff(self, arg: str) -> None:
        """sniff on|off

        Enable or disable sniff mode (placeholder).
        """
        arg = arg.strip().lower()
        if arg not in ("on", "off"):
            console.print("[red]Usage:[/red] sniff on|off")
            return
        self.sniffing = arg == "on"
        console.print(
            f"[green]Sniffing {'enabled' if self.sniffing else 'disabled'} (placeholder).[/green]"
        )

    def do_ui(self, arg: str) -> None:
        """
        ui on [port]
        ui off
        """
        parts = arg.split()
        if not parts:
            console.print("[red]Usage: ui on|off [port][/red]")
            return

        action = parts[0]

        if action == "on":
            port = 8765
            if len(parts) > 1:
                try:
                    port = int(parts[1])
                except ValueError:
                    console.print("[red]Port must be an integer.[/red]")
                    return

            console.print(
                f"[cyan]Starting UI on http://localhost:{port} (background mode)[/cyan]"
            )
            run_server_process(port=port)

        elif action == "off":
            from .server.app import stop_server
            console.print("[cyan]Stopping UI...[/cyan]")
            stop_server()
            console.print("[green]UI stopped.[/green]")

        else:
            console.print("[red]Usage: ui on [port] | ui off[/red]")

    # ---------------------------------------------------
    # META COMMANDS
    # ---------------------------------------------------

    def do_version(self, arg: str) -> None:
        """Show HexHound version."""
        console.print(f"HexHound v{__version__}")

    def do_quit(self, arg: str) -> bool:
        """Exit HexHound."""
        console.print("Goodbye.")
        return True

    def do_exit(self, arg: str) -> bool:
        """Alias for quit."""
        return self.do_quit(arg)


def launch_shell() -> None:
    shell = HexHoundShell()
    shell.cmdloop()
