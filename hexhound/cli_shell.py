from __future__ import annotations

import random

import cmd2
from rich.console import Console

from .banners import BANNERS
from . import __version__
from .core.taint_engine import trace_target
from .server.app import run_server

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

    def do_run(self, arg: str) -> None:
        """run trace

        Run taint trace on configured targets (EVM-only for now).
        """
        parts = arg.split()
        if not parts or parts[0] != "trace":
            console.print("[red]Usage:[/red] run trace")
            return

        if not self.targets:
            console.print("[yellow]No targets configured. Use 'add' first.[/yellow]")
            return

        for t in self.targets:
            chain = t["chain"]
            address = t["address"]
            console.print(
                f"[cyan]Tracing[/cyan] {address} on {chain} with depth {self.depth}..."
            )
            try:
                tg = trace_target(target=address, depth=self.depth, chain=chain)
            except Exception as e:  # noqa: BLE001
                console.print(f"[red]Error tracing {address}: {e}[/red]")
                continue

            console.print(
                f"[green]Trace complete[/green] — nodes: {len(tg.nodes)}, edges: {len(tg.edges)}"
            )

    def do_sniff(self, arg: str) -> None:
        """sniff on|off

        Enable or disable sniff mode (stub for now).
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
        """ui [port]

        Start the HexHound UI server. Default port 8765.
        """
        port: int = 8765
        arg = arg.strip()
        if arg:
            try:
                port = int(arg)
            except ValueError:
                console.print("[red]Port must be an integer.[/red]")
                return

        console.print(f"[cyan]Starting UI on http://localhost:{port}[/cyan]")
        run_server(port=port)

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
