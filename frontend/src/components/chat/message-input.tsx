"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";

interface MessageInputProps {
  onSendMessage: (content: string, sender: "user" | "assistant") => void;
  value?: string;
  setValue?: (value: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSendMessage, value, setValue, disabled }: MessageInputProps) {
  const [internalMessage, setInternalMessage] = useState("");

  // Use external value if provided, otherwise use internal state
  const message = value !== undefined ? value : internalMessage;
  const setMessage = setValue !== undefined ? setValue : setInternalMessage;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim(), "user");
      setMessage("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <div className="relative">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={disabled ? "Processing..." : "Type your message..."}
          className="w-full resize-none rounded-md border-0 bg-transparent px-3 py-2 pr-12 focus:outline-none focus:ring-0"
          rows={1}
          disabled={disabled}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
        />
        <Button 
          type="submit" 
          disabled={!message.trim() || disabled}
          size="sm"
          className="absolute right-1 top-1/2 -translate-y-1/2 h-8 w-8 p-0"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
        </Button>
      </div>
    </form>
  );
} 