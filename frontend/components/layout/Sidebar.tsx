import React from "react";
import { SessionSummary } from "@/lib/types";
import { Plus, MessageSquare, Settings, Trash2, Sparkles } from "lucide-react";

interface SidebarProps {
  sessions: SessionSummary[];
  currentSessionId?: string;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onDeleteSession: (id: string) => void;
  onOpenSettings: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  onOpenSettings,
}) => {
  // Helper to group sessions by recency
  const groupSessions = (list: SessionSummary[]) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const lastWeek = new Date(today);
    lastWeek.setDate(lastWeek.getDate() - 7);

    const groups: { [key: string]: SessionSummary[] } = {
      Today: [],
      Yesterday: [],
      "Previous 7 Days": [],
      Older: [],
    };

    list.forEach((s) => {
      const d = new Date(s.updated_at || s.created_at);
      if (d >= today) {
        groups.Today.push(s);
      } else if (d >= yesterday) {
        groups.Yesterday.push(s);
      } else if (d >= lastWeek) {
        groups["Previous 7 Days"].push(s);
      } else {
        groups.Older.push(s);
      }
    });

    return groups;
  };

  const grouped = groupSessions(sessions);

  return (
    <aside className="w-64 h-full bg-surface-50 border-r border-surface-200 flex flex-col justify-between flex-shrink-0">
      {/* Top Section */}
      <div className="flex flex-col flex-1 overflow-hidden">
        {/* Brand / Logo */}
        <div className="p-4 border-b border-surface-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center text-white">
              <Sparkles className="w-4 h-4" />
            </div>
            <span className="font-bold text-sm tracking-tight text-zinc-100">
              Lenny Assistant
            </span>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={onNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary border border-primary/30 text-xs font-semibold transition-colors"
          >
            <Plus className="w-4 h-4" /> New Chat
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
          {Object.entries(grouped).map(([category, items]) => {
            if (items.length === 0) return null;

            return (
              <div key={category} className="space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500 px-2">
                  {category}
                </span>
                <div className="space-y-0.5 mt-1">
                  {items.map((session) => {
                    const isActive = session.id === currentSessionId;

                    return (
                      <div
                        key={session.id}
                        className={`group flex items-center justify-between py-2 px-2.5 rounded-lg text-xs transition-colors cursor-pointer ${
                          isActive
                            ? "bg-surface-200 text-white font-medium shadow-xs"
                            : "text-zinc-400 hover:text-zinc-200 hover:bg-surface-100"
                        }`}
                        onClick={() => onSelectSession(session.id)}
                      >
                        <div className="flex items-center gap-2 truncate pr-2">
                          <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate">{session.title}</span>
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteSession(session.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-400 transition-opacity"
                          title="Delete session"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer Settings Button */}
      <div className="p-3 border-t border-surface-200">
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center gap-2.5 py-2 px-3 rounded-lg text-xs text-zinc-400 hover:text-zinc-100 hover:bg-surface-100 transition-colors font-medium"
        >
          <Settings className="w-4 h-4" /> Model Settings
        </button>
      </div>
    </aside>
  );
};
