import React, { useEffect, useState } from "react";

type Health = {
  status: string;
  version: string;
};

const App: React.FC = () => {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-slate-900 flex flex-col">
      <header className="border-b border-slate-800 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto max-w-5xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-accent to-accentPurple shadow-glow flex items-center justify-center">
              <span className="text-xs font-semibold tracking-widest">HX</span>
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-wide">HexHound</h1>
              <p className="text-xs text-slate-400">
                Blockchain forensics &amp; taint tracing
              </p>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            {health ? (
              <>
                <span className="inline-flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  Online
                </span>
                <span className="ml-3">v{health.version}</span>
              </>
            ) : (
              <span className="inline-flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-rose-500" />
                Backend unavailable
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-5xl px-4 py-8">
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2 rounded-2xl bg-surface/80 border border-slate-800 shadow-glow p-5">
            <h2 className="text-sm font-semibold text-slate-200 mb-2">
              Taint graph
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              This placeholder will become the interactive address graph
              visualization. For now, control HexHound from the console and
              watch this space evolve.
            </p>
            <div className="h-64 rounded-xl border border-dashed border-slate-700 flex items-center justify-center text-xs text-slate-500">
              Graph canvas
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl bg-surface/80 border border-slate-800 p-4">
              <h3 className="text-sm font-semibold mb-2">Quickstart</h3>
              <ol className="text-xs text-slate-400 list-decimal list-inside space-y-1">
                <li>Run <code>hexhound</code> to open the console.</li>
                <li>Add a target: <code>add eth-mainnet 0xabc...</code></li>
                <li>Set depth: <code>set depth 4</code></li>
                <li>Run the trace: <code>run trace</code></li>
              </ol>
            </div>

            <div className="rounded-2xl bg-surface/80 border border-slate-800 p-4">
              <h3 className="text-sm font-semibold mb-2">Status</h3>
              <p className="text-xs text-slate-400">
                HexHound UI is in early alpha. Core tracing, sniff mode,
                multi-chain support, and rich graph interaction are coming next.
              </p>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-800 bg-background/80">
        <div className="mx-auto max-w-5xl px-4 py-3 text-[10px] text-slate-500 flex justify-between">
          <span>HexHound · blockchain forensics toolkit</span>
          <span>Alpha build</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
