"use client";

import React from "react";
import {
  Files,
  Search,
  GitBranch,
  Sparkles,
  Brain,
  Settings,
  Activity,
  Layers,
} from "lucide-react";

export type SidebarTab = "explorer" | "search" | "git" | "agent_history" | "memory";

interface ActivityBarProps {
  activeTab: SidebarTab;
  onSelectTab: (tab: SidebarTab) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  stagedGitCount?: number;
  onOpenSettings: () => void;
}

export function ActivityBar({
  activeTab,
  onSelectTab,
  isOpen,
  onToggleOpen,
  stagedGitCount = 0,
  onOpenSettings,
}: ActivityBarProps) {
  const navItems = [
    {
      id: "explorer" as SidebarTab,
      label: "Explorer (Ctrl+Shift+E)",
      icon: Files,
    },
    {
      id: "search" as SidebarTab,
      label: "Search Across Files (Ctrl+Shift+F)",
      icon: Search,
    },
    {
      id: "git" as SidebarTab,
      label: "Source Control",
      icon: GitBranch,
      badge: stagedGitCount > 0 ? stagedGitCount : undefined,
    },
    {
      id: "agent_history" as SidebarTab,
      label: "Autonomous Runs & Tasks",
      icon: Sparkles,
    },
    {
      id: "memory" as SidebarTab,
      label: "Persistent Project Memory",
      icon: Brain,
    },
  ];

  const handleTabClick = (tabId: SidebarTab) => {
    if (activeTab === tabId && isOpen) {
      onToggleOpen();
    } else {
      onSelectTab(tabId);
      if (!isOpen) {
        onToggleOpen();
      }
    }
  };

  return (
    <aside className="w-12 bg-slate-950 border-r border-slate-800/80 flex flex-col items-center justify-between py-2 select-none z-20">
      {/* Top Activity Icons */}
      <div className="flex flex-col items-center gap-1 w-full">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id && isOpen;
          return (
            <button
              key={item.id}
              onClick={() => handleTabClick(item.id)}
              title={item.label}
              className={`relative w-full h-11 flex items-center justify-center transition-colors ${
                isActive
                  ? "text-white"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {/* Active left indicator strip */}
              {isActive && (
                <div className="absolute left-0 top-1 bottom-1 w-0.5 bg-amber-400 rounded-r" />
              )}
              <Icon className="w-5 h-5" />

              {/* Git or Run Badge */}
              {item.badge !== undefined && (
                <span className="absolute top-1.5 right-1.5 min-w-[14px] h-[14px] px-0.5 bg-indigo-600 text-[9px] font-bold text-white rounded-full flex items-center justify-center">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Icons: Settings */}
      <div className="flex flex-col items-center gap-1 w-full">
        <button
          onClick={onOpenSettings}
          title="IDE & Model Settings"
          className="w-full h-10 flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
