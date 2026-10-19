"use client";

import React, { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { usePersonaStore } from "@/store/persona-store";
import { sendChatMessage } from "@/lib/api";
import { ChatMessage, Citation } from "@/lib/api/contracts";
import {
  Send,
  Bot,
  User,
  BookOpen,
  Sparkles,
  HelpCircle,
  Activity,
  FileCheck2,
} from "lucide-react";

export default function AssistantPage() {
  const { currentPersonaId, currentUser } = usePersonaStore();
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome-1",
      role: "assistant",
      content: `Hello ${currentUser?.name || "there"}! I am Akira, your AI insurance assistant. I can help clarify coverage in your policy documents, guide you through filing a claim (FNOL), or check your billing schedule. How may I assist you today?`,
      intent: "general_inquiry",
      suggestedActions: [
        "What does my health policy cover for day care procedures?",
        "How do I submit a new claim?",
        "When is my next premium due?",
      ],
      createdAt: new Date().toISOString(),
    },
  ]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (text: string) => {
      const history = messages.slice(-6).map((m) => ({
        role: m.role,
        content: m.content,
      }));
      return sendChatMessage({
        message: text,
        conversation_history: history,
      });
    },
    onSuccess: (response) => {
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        intent: response.intent,
        citations: response.citations,
        structuredData: response.structured_data,
        suggestedActions: response.suggested_actions,
        traceId: response.trace_id,
        requiresClarification: response.requires_clarification,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    },
    onError: (err: Error) => {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: `I encountered an issue processing your request: ${err.message}. Please try again or rephrase your question.`,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    },
  });

  const handleSend = (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || chatMutation.isPending) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    chatMutation.mutate(text);
  };

  return (
    <AppShell>
      <PageHeader
        title="AKIRA Policy & Claims Assistant"
        subtitle="Verifiable answers grounded in active policy documents with clause and page citations."
      />

      <div className="washi-panel flex flex-col h-[650px] overflow-hidden">
        {/* Chat History Container */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start gap-3.5 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-semibold ${
                  msg.role === "user"
                    ? "bg-aoi text-white"
                    : "bg-aoi-wash text-aoi border border-aoi/20"
                }`}
              >
                {msg.role === "user" ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              {/* Message Bubble & Citations */}
              <div
                className={`max-w-[85%] sm:max-w-[75%] space-y-2 ${
                  msg.role === "user" ? "text-right" : "text-left"
                }`}
              >
                {/* Intent & Trace header */}
                {msg.role === "assistant" && (msg.intent || msg.traceId) && (
                  <div className="flex items-center gap-2 text-[10px] text-ink-muted">
                    {msg.intent && (
                      <span className="font-mono bg-surface-muted px-2 py-0.5 rounded border border-washi-border uppercase">
                        Intent: {msg.intent}
                      </span>
                    )}
                    {msg.traceId && (
                      <span className="font-mono text-ink-muted/80 flex items-center gap-1">
                        <Activity className="w-3 h-3 text-aoi" />
                        Trace: {msg.traceId.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                )}

                {/* Content Bubble */}
                <div
                  className={`p-4 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-aoi text-white rounded-tr-xs"
                      : "bg-surface border border-washi-border shadow-xs text-ink rounded-tl-xs"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>

                {/* Clarification Alert */}
                {msg.requiresClarification && (
                  <div className="p-2.5 rounded-lg bg-surface-muted border border-washi-border text-xs text-ink-muted flex items-center gap-2">
                    <HelpCircle className="w-3.5 h-3.5 text-aoi shrink-0" />
                    <span>Please provide additional specifics so I can look up the exact coverage clause.</span>
                  </div>
                )}

                {/* Citations Panel */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 space-y-2 pt-2 text-left">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-aoi" />
                      Policy Citations ({msg.citations.length})
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      {msg.citations.map((cite: Citation, idx: number) => (
                        <div
                          key={idx}
                          className="p-3 rounded-xl bg-surface border border-washi-border text-xs space-y-1 hover:border-aoi/40 transition-colors"
                        >
                          <div className="flex items-center justify-between text-[11px]">
                            <span className="font-serif font-bold text-ink">
                              {cite.policy_name}
                            </span>
                            <span className="font-mono text-ink-muted bg-surface-muted px-1.5 py-0.5 rounded">
                              Page {cite.page} • Score {(cite.relevance_score * 100).toFixed(0)}%
                            </span>
                          </div>
                          {cite.section && (
                            <div className="text-[11px] text-aoi font-medium">
                              Section: {cite.section}
                            </div>
                          )}
                          <p className="text-[11px] text-ink-muted italic border-l-2 border-aoi/40 pl-2">
                            "{cite.text_excerpt}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggested Action Chips */}
                {msg.suggestedActions && msg.suggestedActions.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-2">
                    {msg.suggestedActions.map((action, i) => (
                      <button
                        key={i}
                        onClick={() => handleSend(action)}
                        className="text-xs px-3 py-1 rounded-full bg-surface-muted border border-washi-border hover:bg-aoi-wash hover:text-aoi hover:border-aoi/30 text-ink-muted transition-colors flex items-center gap-1"
                      >
                        <Sparkles className="w-3 h-3 text-aoi" />
                        <span>{action}</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {chatMutation.isPending && (
            <div className="flex items-start gap-3.5">
              <div className="w-8 h-8 rounded-full bg-aoi-wash text-aoi border border-aoi/20 flex items-center justify-center shrink-0">
                <Bot className="w-4 h-4 animate-pulse" />
              </div>
              <div className="p-4 rounded-2xl bg-surface border border-washi-border text-xs text-ink-muted flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-aoi animate-bounce" />
                <span className="w-2 h-2 rounded-full bg-aoi animate-bounce [animation-delay:0.2s]" />
                <span className="w-2 h-2 rounded-full bg-aoi animate-bounce [animation-delay:0.4s]" />
                <span className="ml-2 font-mono text-[11px]">Searching policy corpus...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Composer */}
        <div className="p-4 border-t border-washi-border bg-surface">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={inputMessage}
              maxLength={8000}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about policy clauses, claim eligibility, deductibles, or FNOL steps..."
              className="flex-1 px-4 py-2.5 text-sm rounded-xl border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all"
            />
            <Button
              type="submit"
              variant="primary"
              disabled={!inputMessage.trim() || chatMutation.isPending}
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
          <div className="flex items-center justify-between text-[11px] text-ink-muted mt-2 px-1">
            <span>Powered by LangGraph Agent + Qdrant RAG</span>
            <span>{inputMessage.length} / 8000 chars</span>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
