"use client";

import React, { useState, useEffect } from "react";
import {
  Globe,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  Camera,
  Layers,
  AlertOctagon,
  WifiOff,
  History,
  ShieldCheck,
  ShieldAlert,
  Plus,
  X,
  Play,
  Square,
  ChevronRight,
  ExternalLink,
} from "lucide-react";

interface TabInfo {
  tab_id: string;
  title: string;
  url: string;
  is_active: boolean;
}

interface BrowserDiagnostics {
  status: string;
  error_count: number;
  console_errors: string[];
  page_errors: string[];
  network_failures: Array<{ url: string; method: string; error_text: string }>;
  http_errors: Array<{ url: string; status: number; status_text: string }>;
  recent_console_logs: string[];
}

export function BrowserPreview() {
  const [url, setUrl] = useState("http://127.0.0.1:8000/static/index.html");
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [pageTitle, setPageTitle] = useState("");
  const [screenshotB64, setScreenshotB64] = useState<string | null>(null);
  const [tabs, setTabs] = useState<TabInfo[]>([]);
  const [activeTabId, setActiveTabId] = useState<string>("");
  const [activeView, setActiveView] = useState<"preview" | "dom" | "console" | "network" | "history">("preview");

  // DOM and Diagnostics
  const [domTree, setDomTree] = useState<any>(null);
  const [diagnostics, setDiagnostics] = useState<BrowserDiagnostics>({
    status: "idle",
    error_count: 0,
    console_errors: [],
    page_errors: [],
    network_failures: [],
    http_errors: [],
    recent_console_logs: [],
  });

  // Sensitive action approval dialog
  const [pendingApproval, setPendingApproval] = useState<{
    action: string;
    selector: string;
    reason: string;
  } | null>(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/status");
      const data = await res.json();
      setIsRunning(data.running);
      if (data.page_title) setPageTitle(data.page_title);
      if (data.diagnostics) {
        setDiagnostics((prev) => ({
          ...prev,
          ...data.diagnostics,
          console_errors: data.diagnostics.console_errors || [],
          page_errors: data.diagnostics.page_errors || [],
          network_failures: data.diagnostics.network_failures || [],
          http_errors: data.diagnostics.http_errors || [],
          recent_console_logs: data.diagnostics.recent_console_logs || [],
        }));
      }
      if (data.running) fetchTabs();
    } catch {}
  };

  const fetchTabs = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/tabs");
      const data = await res.json();
      setTabs(data.tabs || []);
      const active = data.tabs?.find((t: TabInfo) => t.is_active);
      if (active) {
        setActiveTabId(active.tab_id);
        setUrl(active.url);
      }
    } catch {}
  };

  const handleLaunch = async () => {
    setIsLoading(true);
    try {
      await fetch("http://127.0.0.1:8000/api/browser/launch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ headless: true }),
      });
      await handleNavigate();
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsLoading(false);
      fetchStatus();
    }
  };

  const handleClose = async () => {
    try {
      await fetch("http://127.0.0.1:8000/api/browser/close", { method: "POST" });
      setIsRunning(false);
      setScreenshotB64(null);
      setPageTitle("");
      setTabs([]);
    } catch {}
  };

  const handleNavigate = async (navUrl?: string) => {
    const target = navUrl || url;
    if (!target.trim()) return;

    setIsLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/navigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: target, timeout_ms: 15000 }),
      });
      const data = await res.json();
      if (data.title) setPageTitle(data.title);
      if (data.url) setUrl(data.url);
      await refreshScreenshot();
      await refreshDom();
      await fetchDiagnostics();
      await fetchTabs();
    } catch (e: any) {
      console.error("Navigation error:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshScreenshot = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/screenshot");
      const data = await res.json();
      if (data.screenshot_b64) {
        setScreenshotB64(data.screenshot_b64);
      }
    } catch {}
  };

  const refreshDom = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/dom?selector=body&max_depth=3");
      const data = await res.json();
      if (data.dom) setDomTree(data.dom);
    } catch {}
  };

  const fetchDiagnostics = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/api/browser/diagnostics");
      const data = await res.json();
      if (data) {
        setDiagnostics((prev) => ({
          ...prev,
          ...data,
          console_errors: data.console_errors || [],
          page_errors: data.page_errors || [],
          network_failures: data.network_failures || [],
          http_errors: data.http_errors || [],
          recent_console_logs: data.recent_console_logs || [],
        }));
      }
    } catch {}
  };

  const handleSwitchTab = async (tabId: string) => {
    try {
      await fetch("http://127.0.0.1:8000/api/browser/tabs/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tab_id: tabId }),
      });
      fetchTabs();
      refreshScreenshot();
    } catch {}
  };

  const handleCloseTab = async (tabId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await fetch("http://127.0.0.1:8000/api/browser/tabs/close", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tab_id: tabId }),
      });
      fetchTabs();
    } catch {}
  };

  // Render DOM tree node recursively
  const renderDomNode = (node: any, depth = 0) => {
    if (!node) return null;
    return (
      <div key={Math.random()} className="space-y-1 font-mono text-[11px]" style={{ paddingLeft: `${depth * 14}px` }}>
        <div className="flex items-center gap-1.5 py-0.5 text-slate-300 hover:text-amber-300">
          <span className="text-sky-400 font-bold">&lt;{node.tag}</span>
          {node.id && <span className="text-amber-400">#{node.id}</span>}
          {node.classes?.length > 0 && <span className="text-emerald-400">.{node.classes.join(".")}</span>}
          {node.text && <span className="text-slate-400 italic truncate max-w-xs">"{node.text}"</span>}
          <span className="text-sky-400 font-bold">&gt;</span>
        </div>
        {node.children?.map((child: any) => renderDomNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Controls & Navigation Bar */}
      <div className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/60 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <div className="p-1.5 bg-sky-500/10 border border-sky-500/30 rounded-lg text-sky-400">
            <Globe className="w-4 h-4" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-white">Browser Automation</span>
            <span className="px-1.5 py-0.5 text-[10px] rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 font-semibold font-mono">
              Chromium Playwright
            </span>
          </div>
        </div>

        {/* Address Bar */}
        <div className="flex-1 max-w-xl mx-4 flex items-center bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 shadow-inner">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleNavigate()}
            placeholder="http://127.0.0.1:8000/static/index.html"
            className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none font-mono"
          />
          <button
            onClick={() => handleNavigate()}
            disabled={isLoading}
            className="p-1 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin text-sky-400" : ""}`} />
          </button>
        </div>

        {/* Browser Status Pill & Actions */}
        <div className="flex items-center gap-2.5">
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs border font-mono ${
              isRunning
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-slate-800 border-slate-700 text-slate-400"
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isRunning ? "bg-emerald-400 animate-pulse" : "bg-slate-500"}`} />
            <span>{isRunning ? "Browser Running" : "Browser Stopped"}</span>
          </div>

          {!isRunning ? (
            <button
              onClick={handleLaunch}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-sky-950 transition-colors"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              <span>Launch</span>
            </button>
          ) : (
            <button
              onClick={handleClose}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-semibold transition-colors"
            >
              <Square className="w-3.5 h-3.5 fill-rose-300" />
              <span>Close</span>
            </button>
          )}
        </div>
      </div>

      {/* Tab Bar (when browser is active) */}
      {tabs.length > 0 && (
        <div className="h-9 border-b border-slate-800 bg-slate-900/40 px-6 flex items-center gap-2 overflow-x-auto text-xs">
          {tabs.map((t) => (
            <div
              key={t.tab_id}
              onClick={() => handleSwitchTab(t.tab_id)}
              className={`flex items-center gap-2 px-3 py-1 rounded-t-lg border-t border-x cursor-pointer transition-colors ${
                t.is_active
                  ? "bg-slate-950 border-slate-800 text-white font-medium shadow-sm"
                  : "bg-slate-900/60 border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <span className="truncate max-w-[140px] font-mono text-[11px]">{t.title || "Untitled Tab"}</span>
              <button
                onClick={(e) => handleCloseTab(t.tab_id, e)}
                className="p-0.5 hover:text-rose-400 rounded transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Navigation View Switcher Subheader */}
      <div className="h-10 border-b border-slate-800/80 bg-slate-900/30 px-6 flex items-center justify-between text-xs">
        <div className="flex items-center gap-1 font-mono text-slate-400 text-[11px]">
          <span className="text-white font-semibold truncate max-w-sm">{pageTitle || "Ready"}</span>
        </div>

        <div className="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-xs font-mono">
          <button
            onClick={() => setActiveView("preview")}
            className={`px-2.5 py-0.5 rounded transition-colors ${
              activeView === "preview" ? "bg-sky-500/20 text-sky-400 font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            Visual Preview
          </button>
          <button
            onClick={() => {
              setActiveView("dom");
              refreshDom();
            }}
            className={`px-2.5 py-0.5 rounded transition-colors ${
              activeView === "dom" ? "bg-sky-500/20 text-sky-400 font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            DOM Inspector
          </button>
          <button
            onClick={() => {
              setActiveView("console");
              fetchDiagnostics();
            }}
            className={`px-2.5 py-0.5 rounded transition-colors flex items-center gap-1 ${
              activeView === "console" ? "bg-sky-500/20 text-sky-400 font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            <span>Console</span>
            {(diagnostics?.console_errors || []).length > 0 && (
              <span className="px-1 py-0.2 rounded-full text-[9px] bg-rose-500 text-white font-bold">
                {(diagnostics?.console_errors || []).length}
              </span>
            )}
          </button>
          <button
            onClick={() => {
              setActiveView("network");
              fetchDiagnostics();
            }}
            className={`px-2.5 py-0.5 rounded transition-colors flex items-center gap-1 ${
              activeView === "network" ? "bg-sky-500/20 text-sky-400 font-semibold" : "text-slate-400 hover:text-white"
            }`}
          >
            <span>Network</span>
            {(diagnostics?.network_failures || []).length > 0 && (
              <span className="px-1 py-0.2 rounded-full text-[9px] bg-rose-500 text-white font-bold">
                {(diagnostics?.network_failures || []).length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Main Panel Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Visual Preview */}
        {activeView === "preview" && (
          <div className="flex-1 p-6 flex flex-col items-center justify-center bg-slate-950 overflow-y-auto">
            {screenshotB64 ? (
              <div className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
                <div className="p-3 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between text-xs text-slate-300 font-mono">
                  <div className="flex items-center gap-2">
                    <Camera className="w-3.5 h-3.5 text-sky-400" />
                    <span className="truncate max-w-md">{pageTitle || "Page Render"}</span>
                  </div>
                  <button
                    onClick={refreshScreenshot}
                    className="p-1 hover:text-white rounded"
                    title="Refresh Screenshot"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
                <img
                  src={`data:image/png;base64,${screenshotB64}`}
                  alt="Captured Page Render"
                  className="w-full h-auto object-contain"
                />
              </div>
            ) : (
              <div className="text-center max-w-sm space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 mx-auto">
                  <Globe className="w-6 h-6" />
                </div>
                <h3 className="text-sm font-bold text-white">Chromium Automation Engine</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Click Launch or enter a local web app address to start real Playwright automation, capture screenshots, and test interactions.
                </p>
                <button
                  onClick={handleLaunch}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-semibold shadow-md transition-all active:scale-95"
                >
                  Launch Local Application
                </button>
              </div>
            )}
          </div>
        )}

        {/* DOM Inspector Panel */}
        {activeView === "dom" && (
          <div className="flex-1 p-6 bg-slate-950 overflow-y-auto font-mono text-xs">
            <div className="border-b border-slate-800 pb-3 mb-4 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Structured DOM Hierarchy</h3>
                <p className="text-xs text-slate-400 font-sans">
                  Real-time element tree extracted directly from the Chromium page context.
                </p>
              </div>
              <button
                onClick={refreshDom}
                className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh Tree
              </button>
            </div>
            {domTree ? (
              <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-1">
                {renderDomNode(domTree)}
              </div>
            ) : (
              <div className="text-slate-500 italic py-8 text-center font-sans">No DOM tree captured yet.</div>
            )}
          </div>
        )}

        {/* Console Errors Panel */}
        {activeView === "console" && (
          <div className="flex-1 p-6 bg-slate-950 overflow-y-auto font-mono text-xs space-y-4">
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">JavaScript Console Log Stream</h3>
                <p className="text-xs text-slate-400 font-sans">
                  Monitors browser console output and captures uncaught runtime errors.
                </p>
              </div>
              <button
                onClick={fetchDiagnostics}
                className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {(diagnostics?.console_errors || []).length === 0 && (diagnostics?.recent_console_logs || []).length === 0 ? (
              <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl text-xs font-sans">
                <ShieldCheck className="w-4 h-4" />
                <span>Zero console errors or exceptions detected on this page.</span>
              </div>
            ) : (
              <div className="space-y-2">
                {(diagnostics?.console_errors || []).map((err, i) => (
                  <div key={i} className="p-2.5 bg-rose-950/40 border border-rose-800/60 rounded-lg text-rose-300 text-[11px]">
                    {err}
                  </div>
                ))}
                {(diagnostics?.recent_console_logs || []).map((log, i) => (
                  <div key={i} className="p-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-300 text-[11px]">
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Network Failures Panel */}
        {activeView === "network" && (
          <div className="flex-1 p-6 bg-slate-950 overflow-y-auto font-mono text-xs space-y-4">
            <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">Network Failure Monitor</h3>
                <p className="text-xs text-slate-400 font-sans">
                  Tracks failed HTTP requests (status &gt;= 400) and aborted network connections.
                </p>
              </div>
              <button
                onClick={fetchDiagnostics}
                className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Refresh
              </button>
            </div>

            {(diagnostics?.network_failures || []).length === 0 && (diagnostics?.http_errors || []).length === 0 ? (
              <div className="flex items-center gap-2 p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-xl text-xs font-sans">
                <ShieldCheck className="w-4 h-4" />
                <span>All network requests succeeded with valid HTTP response status.</span>
              </div>
            ) : (
              <div className="space-y-2">
                {(diagnostics?.network_failures || []).map((fail, i) => (
                  <div key={i} className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-lg space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-rose-400">{fail.method} {fail.url}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300">FAILED</span>
                    </div>
                    <div className="text-[11px] text-slate-400">{fail.error_text}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sensitive Action Approval Modal */}
      {pendingApproval && (
        <div className="absolute inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-slate-900 border border-sky-500/40 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-sky-500/20 text-sky-400 rounded-xl">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white">Browser Action Approval Required</h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  The automated testing agent requested a sensitive web action.
                </p>
              </div>
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5 text-xs font-mono">
              <div className="text-amber-400 font-semibold">{pendingApproval.action} on {pendingApproval.selector}</div>
              <div className="text-slate-400 text-[11px] font-sans">{pendingApproval.reason}</div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setPendingApproval(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold"
              >
                Deny Action
              </button>
              <button
                onClick={() => setPendingApproval(null)}
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold"
              >
                Approve & Proceed
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
