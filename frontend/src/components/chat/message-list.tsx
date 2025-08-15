"use client";

import { Message } from "./message";

export interface Action {
  type: string;
  data: Record<string, any>;
}

export interface Step {
  id: string;
  title?: string;
  content: string;
  status?: 'running' | 'completed' | 'failed';
  actions?: Action[];
  integration_uuid?: string;
  animationDelay?: number;
}

export interface ChatMessage {
  id: string;
  content: string;
  sender: "user" | "assistant";
  timestamp: Date;
  steps?: Step[];
  isLoading?: boolean;
}

interface MessageListProps {
  messages: ChatMessage[];
}

export function MessageList({ messages }: MessageListProps) {
  return (
    <div className="h-full overflow-y-auto py-4 space-y-4">
      {messages.map((message) => (
        <Message key={message.id} message={message} />
      ))}
    </div>
  );
} 