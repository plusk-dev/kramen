"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { History, User, Trash2 } from "lucide-react";
import { PreviousChatsDialog } from "./previous-chats-dialog";

interface PreviousChat {
  id: string;
  title: string;
  messages: any[];
  createdAt: Date;
  lastModified: Date;
}

interface ChatNavbarProps {
  onLoadChat?: (chat: PreviousChat) => void;
  onNewChat?: () => void;
  onClearChat?: () => void;
}

export function ChatNavbar({ onLoadChat, onNewChat, onClearChat }: ChatNavbarProps) {
  const [previousChatsOpen, setPreviousChatsOpen] = useState(false);
  return (
    <div className="sticky top-0 z-50 w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex justify-center">
        <div className="w-full max-w-4xl border-b flex h-14 items-center justify-between">
          {/* Left side - App name */}
          <div className="flex items-center space-x-2 text-primary">
            <h1 
              className="text-2xl tracking-widest cursor-pointer hover:opacity-80 transition-opacity"
              onClick={onNewChat}
            >
              kramen
            </h1>
          </div>

          {/* Right side - Actions */}
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="flex items-center space-x-2"
              onClick={() => setPreviousChatsOpen(true)}
            >
              <History className="h-4 w-4" />
              {/* <span>Previous Chats</span> */}
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="flex items-center space-x-2 text-destructive hover:text-destructive"
              onClick={onClearChat}
            >
              <Trash2 className="h-4 w-4" />
              {/* <span>Clear Chat</span> */}
            </Button>
            <Button variant="outline" size="sm" className="flex items-center">
              <User className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
      
      <PreviousChatsDialog
        open={previousChatsOpen}
        onOpenChange={setPreviousChatsOpen}
        onLoadChat={onLoadChat}
      />
    </div>
  );
} 