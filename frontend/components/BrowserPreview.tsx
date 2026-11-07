"use client";

import React, { useState } from "react";
import { Globe, RefreshCw, AlertTriangle, ShieldCheck, Camera } from "lucide-react";

export function BrowserPreview() {
  const [url, setUrl] = useState("http://localhost:3000");
  const [inspectData, setInspectData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleInspect = async () => {
    setIsLoading(true);
    try {
      const res = await fetch("http://localhost:8000/browser/inspect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, wait_ms: 2000 }),
      });
      const data = await res.json();
      setInspectData(data);
    } catch (e: any) {
      setInspectData({ error: e.message, has_errors: true });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Address Bar */}
      <div className="h-14 border-b border-slate-800 px-6 flex items-center gap-3 bg-slate-900/60">
        <Globe className="w-4 h-4 text-sky-400" />
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Playwright Verification</span>

        <div className="flex-1 max-w-xl flex items-center bg-slate-800 border border-slate-700 rounded-xl px-3 py-1.5 ml-4">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="http://localhost:3000"
            className="flex-1 bg-transparent text-xs text-white focus:outline-none"
          />
        </div>

        <button
          onClick={handleInspect}
          disabled={isLoading}
          className="flex items-center gap-1.5 px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-md shadow-sky-600/20 transition-all active:scale-95"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Inspect Live Site</span>
        </button>
      </div>

      {/* Main Preview Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Visual Screenshot or Iframe */}
        <div className="flex-1 border-r border-slate-800 p-6 flex flex-col items-center justify-center bg-slate-900/20 overflow-y-auto">
          {isLoading ? (
            <div className="text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-sky-400 animate-spin mx-auto" />
              <p className="text-xs text-slate-400">Opening headless Playwright browser session...</p>
            </div>
          ) : inspectData?.screenshot_b64 ? (
            <div className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
              <div className="p-2.5 bg-slate-800/80 border-b border-slate-700 flex items-center gap-2 text-[11px] text-slate-300">
                <Camera className="w-3.5 h-3.5 text-sky-400" />
                <span>Captured Render: {inspectData.title || "Untitled Page"}</span>
              </div>
              <img
                src={`data:image/jpeg;base64,${inspectData.screenshot_b64}`}
                alt="Page preview"
                className="w-full h-auto"
              />
            </div>
          ) : (
            <div className="text-center max-w-sm space-y-2">
              <div className="w-12 h-12 rounded-2xl bg-sky-600/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mx-auto">
                <Globe className="w-6 h-6" />
              </div>
              <h3 className="text-sm font-bold text-white">Browser Verification Engine</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Enter an application address above and click Inspect to launch Playwright, take screenshots, check console errors, and verify behavior.
              </p>
            </div>
          )}
        </div>

        {/* Diagnostics & Console Errors Sidebar */}
        <div className="w-80 p-4 bg-slate-900/40 flex flex-col space-y-4 overflow-y-auto">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400">Page Diagnostics</div>

          {inspectData ? (
            <div className="space-y-3 text-xs">
              <div className="p-3 bg-slate-800/60 rounded-xl border border-slate-700/60 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">HTTP Status:</span>
                  <span className="font-semibold text-emerald-400">{inspectData.status_code || "OK"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Page Title:</span>
                  <span className="font-medium text-white truncate max-w-[140px]">{inspectData.title || "—"}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">DOM Size:</span>
                  <span className="font-mono text-slate-300">{inspectData.html_length || 0} bytes</span>
                </div>
              </div>

              {/* Console Logs */}
              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1.5">Browser Console Logs</div>
                {inspectData.console_logs?.length > 0 ? (
                  <div className="space-y-1 max-h-48 overflow-y-auto font-mono text-[10px]">
                    {inspectData.console_logs.map((log: string, idx: number) => (
                      <div key={idx} className="p-1.5 bg-slate-950 rounded border border-slate-800 text-slate-300">
                        {log}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-[11px] text-slate-500 italic p-2 bg-slate-950/40 rounded border border-slate-800/60">
                    No console messages logged.
                  </div>
                )}
              </div>

              {/* Page Errors */}
              <div>
                <div className="text-[11px] font-semibold text-slate-400 mb-1.5">Runtime Page Errors</div>
                {inspectData.page_errors?.length > 0 ? (
                  <div className="space-y-1 font-mono text-[10px]">
                    {inspectData.page_errors.map((err: string, idx: number) => (
                      <div key={idx} className="p-2 bg-rose-950/40 rounded border border-rose-800/60 text-rose-300">
                        {err}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 p-2 bg-emerald-500/10 rounded border border-emerald-500/20">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>0 Browser Errors Detected</span>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500 italic py-6">Diagnostics will appear once a page is inspected.</div>
          )}
        </div>
      </div>
    </div>
  );
}

