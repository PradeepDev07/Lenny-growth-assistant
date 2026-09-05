"use client";

import React, { useState, useEffect } from "react";
import { ConfigResponse, SessionSummary, Message, Artifact } from "@/lib/types";
import {
  fetchSessions,
  createSession,
  fetchSession,
  deleteSession,
  triggerShip30,
  createArtifact,
  fetchConfig,
} from "@/lib/api";

import { useChatStream } from "@/hooks/useChatStream";
import { Sidebar } from "@/components/layout/Sidebar";
import { MessageList } from "@/components/chat/MessageList";
import { MessageInput } from "@/components/chat/MessageInput";
import { ArtifactViewer } from "@/components/artifact/ArtifactViewer";
import { SettingsDrawer } from "@/components/settings/SettingsDrawer";
import { HelpDrawer } from "@/components/help/HelpDrawer";
import { Sparkles, Menu, Cpu, HelpCircle } from "lucide-react";

export default function Home() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [activeArtifactId, setActiveArtifactId] = useState<string>("");
  const [isArtifactViewerOpen, setIsArtifactViewerOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [config, setConfig] = useState<ConfigResponse | null>(null);

  // Initialize and load sessions & router status
  useEffect(() => {
    initSessions();
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await fetchConfig();
      setConfig(data);
    } catch (e) {
      console.error("Failed to load config:", e);
    }
  };

  const initSessions = async () => {

    try {
      const list = await fetchSessions();
      setSessions(list);
      if (list.length > 0) {
        selectSession(list[0].id);
      } else {
        handleNewChat();
      }
    } catch (e) {
      console.error("Failed to initialize sessions:", e);
    }
  };

  const selectSession = async (id: string) => {
    setCurrentSessionId(id);
    setIsMobileMenuOpen(false);
    try {
      const detail = await fetchSession(id);
      setMessages(detail.messages || []);
      setArtifacts(detail.artifacts || []);
      if (detail.artifacts && detail.artifacts.length > 0) {
        setActiveArtifactId(detail.artifacts[detail.artifacts.length - 1].id);
      }
    } catch (e) {
      console.error(`Failed to load session ${id}:`, e);
    }
  };

  const handleNewChat = async () => {
    try {
      const newSession = await createSession("New Growth Chat");
      setSessions((prev) => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      setArtifacts([]);
      setIsArtifactViewerOpen(false);
      setIsMobileMenuOpen(false);
    } catch (e) {
      console.error("Failed to create new chat:", e);
    }
  };

  const handleDeleteSession = async (id: string) => {
    try {
      await deleteSession(id);
      const updated = sessions.filter((s) => s.id !== id);
      setSessions(updated);
      if (currentSessionId === id) {
        if (updated.length > 0) {
          selectSession(updated[0].id);
        } else {
          handleNewChat();
        }
      }
    } catch (e) {
      console.error("Failed to delete session:", e);
    }
  };

  // Streaming Hook
  const {
    sendMessage,
    isStreaming,
    streamingContent,
    streamingSources,
    streamingModelInfo,
  } = useChatStream({
    sessionId: currentSessionId,
    onFinish: (newAssistantMsg) => {
      setMessages((prev) => [...prev, newAssistantMsg]);
      // Update message count in sessions list
      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId ? { ...s, message_count: s.message_count + 2 } : s
        )
      );
    },
    onError: (err) => {
      console.error("Streaming error:", err);
    },
  });

  const handleSendMessage = async (text: string) => {
    if (!currentSessionId) return;

    // Optimistically append user message to UI
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      session_id: currentSessionId,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);

    // Send via SSE
    await sendMessage(text);
  };

  // Skill Trigger: Turn into Ship 30/30 Post
  const handleTurnIntoShip30 = async (msg: Message) => {
    if (!currentSessionId) return;
    try {
      const res = await triggerShip30(currentSessionId, msg.content, msg.id);
      if (res && res.data) {
        const essayMsg: Message = {
          id: res.data.message_id || `msg-${Date.now()}`,
          session_id: currentSessionId,
          role: "assistant",
          content: res.data.essay,
          sources: res.data.sources,
          model_info: res.data.model_info,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, essayMsg]);
      }
    } catch (e) {
      console.error("Failed to execute Ship 30 skill:", e);
    }
  };

  // Interactive Artifact Generation Trigger
  const handleGenerateArtifact = async (msg: Message) => {
    if (!currentSessionId) return;
    try {
      const art = await createArtifact(
        currentSessionId,
        "Growth Loop & Retention Calculator",
        "html",
        `Build an interactive HTML/JS growth loop calculator based on: ${msg.content}`
      );
      setArtifacts((prev) => [...prev, art]);
      setActiveArtifactId(art.id);
      setIsArtifactViewerOpen(true);
    } catch (e) {
      console.error("Failed to generate artifact:", e);
    }
  };

  const currentSession = sessions.find((s) => s.id === currentSessionId);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Mobile Hamburger Header */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-40 bg-surface-100 border-b border-surface-200 px-4 py-3 flex items-center justify-between">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-1 text-zinc-400 hover:text-white"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="font-semibold text-sm text-zinc-200">Lenny Growth Assistant</span>
        <button
          onClick={() => setIsSettingsOpen(true)}
          className="p-1 text-zinc-400 hover:text-white"
        >
          <Cpu className="w-5 h-5" />
        </button>
      </div>

      {/* Sidebar - Desktop & Mobile Drawer */}
      <div
        className={`${
          isMobileMenuOpen ? "block absolute inset-y-0 left-0 z-50 shadow-2xl" : "hidden"
        } md:block md:relative h-full`}
      >
        <Sidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={selectSession}
          onNewChat={handleNewChat}
          onDeleteSession={handleDeleteSession}
          onOpenSettings={() => setIsSettingsOpen(true)}
          onOpenHelp={() => setIsHelpOpen(true)}
        />
      </div>

      {/* Main Content Area (Chat + Artifacts Split) */}
      <main className="flex-1 flex overflow-hidden pt-12 md:pt-0">
        {/* Chat Thread Panel */}
        <section
          className={`flex flex-col h-full transition-all duration-300 ${
            isArtifactViewerOpen ? "w-full md:w-1/2 lg:w-3/5" : "w-full"
          }`}
        >
          {/* Chat Header */}
          <div className="h-14 border-b border-surface-200 bg-surface-50/50 backdrop-blur-sm px-6 flex items-center justify-between">
            <div className="flex items-center gap-2 truncate">
              <h2 className="text-sm font-semibold text-zinc-100 truncate">
                {currentSession ? currentSession.title : "Lenny Growth Assistant"}
              </h2>
            </div>

            <div className="flex items-center gap-2.5">
              {/* Live Ollama Detection Pill */}
              {config?.providers?.ollama?.is_running ? (
                <div
                  onClick={() => setIsHelpOpen(true)}
                  className="cursor-pointer flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/40 text-emerald-400 border border-emerald-800/40 text-xs font-medium hover:bg-emerald-950/60 transition-colors"
                  title="Ollama is running locally (Click for details)"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  <span>Ollama: Live</span>
                </div>
              ) : (
                <button
                  onClick={() => setIsHelpOpen(true)}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-100 text-zinc-400 hover:text-amber-300 hover:border-amber-800/50 border border-surface-200 text-xs font-medium transition-colors"
                  title="Local Ollama is offline. Click for setup instructions."
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-zinc-500" />
                  <span>Ollama: Offline (Setup)</span>
                </button>
              )}

              {/* Provider Status Pill */}
              <div
                onClick={() => setIsSettingsOpen(true)}
                className="cursor-pointer flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-100 hover:bg-surface-200 border border-surface-200 text-xs font-medium text-zinc-300 transition-colors"
                title="Click to configure model routing"
              >
                <span className="w-2 h-2 rounded-full bg-indigo-400 shadow-sm shadow-indigo-400/50" />
                <span>Router Config</span>
                <span className="text-zinc-500">▾</span>
              </div>

              {/* Quick Help Button */}
              <button
                onClick={() => setIsHelpOpen(true)}
                className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-surface-100 transition-colors"
                title="Setup & Help Guide"
              >
                <HelpCircle className="w-4 h-4 text-primary" />
              </button>

              {artifacts.length > 0 && !isArtifactViewerOpen && (
                <button
                  onClick={() => setIsArtifactViewerOpen(true)}
                  className="text-xs px-2.5 py-1 rounded-md bg-primary-muted text-primary border border-primary/30 font-medium hover:bg-primary/20 transition-colors"
                >
                  View Artifacts ({artifacts.length})
                </button>
              )}
            </div>
          </div>

          {/* Chat Messages */}
          <MessageList
            messages={messages}
            isStreaming={isStreaming}
            streamingContent={streamingContent}
            streamingSources={streamingSources}
            streamingModelInfo={streamingModelInfo}
            onTurnIntoShip30={handleTurnIntoShip30}
            onGenerateArtifact={handleGenerateArtifact}
          />

          {/* Chat Input */}
          <MessageInput onSendMessage={handleSendMessage} disabled={isStreaming} />
        </section>

        {/* Artifact Viewer Panel (Right Column) */}
        {isArtifactViewerOpen && artifacts.length > 0 && (
          <section className="hidden md:flex flex-col h-full w-1/2 lg:w-2/5 transition-all duration-300">
            <ArtifactViewer
              artifacts={artifacts}
              activeArtifactId={activeArtifactId}
              onSelectArtifact={(id) => setActiveArtifactId(id)}
              onClose={() => setIsArtifactViewerOpen(false)}
            />
          </section>
        )}
      </main>

      {/* Model Router Settings Drawer */}
      <SettingsDrawer
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onOpenHelp={() => setIsHelpOpen(true)}
        onRoutesUpdated={loadConfig}
      />

      {/* Help & Setup Guide Drawer */}
      <HelpDrawer
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
        ollamaStatus={config?.providers?.ollama}
        onRefreshStatus={loadConfig}
      />
    </div>
  );
}

