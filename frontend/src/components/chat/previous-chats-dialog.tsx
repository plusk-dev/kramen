"use client";

import React, { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Clock, MessageSquare, Trash2 } from "lucide-react";
import { ChatMessage } from "./message-list";

interface PreviousChat {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  lastModified: Date;
}

interface PreviousChatsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onLoadChat?: (chat: PreviousChat) => void;
}

export function PreviousChatsDialog({ 
  open, 
  onOpenChange, 
  onLoadChat 
}: PreviousChatsDialogProps) {
  const [previousChats, setPreviousChats] = useState<PreviousChat[]>([]);

  useEffect(() => {
    // Load previous chats from localStorage
    const loadPreviousChats = () => {
      try {
        const stored = localStorage.getItem('kramen-chat-history');
        if (stored) {
          const chats = JSON.parse(stored);
          // Convert date strings back to Date objects
          const parsedChats = chats.map((chat: any) => ({
            ...chat,
            createdAt: new Date(chat.createdAt),
            lastModified: new Date(chat.lastModified),
            messages: chat.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp)
            }))
          }));
          setPreviousChats(parsedChats);
        }
      } catch (error) {
        console.error('Error loading previous chats:', error);
      }
    };

    if (open) {
      loadPreviousChats();
    }
  }, [open]);

  const handleLoadChat = (chat: PreviousChat) => {
    if (onLoadChat) {
      onLoadChat(chat);
    }
    onOpenChange(false);
  };

  const handleDeleteChat = (chatId: string) => {
    const updatedChats = previousChats.filter(chat => chat.id !== chatId);
    setPreviousChats(updatedChats);
    
    // Update localStorage
    try {
      localStorage.setItem('kramen-chat-history', JSON.stringify(updatedChats));
    } catch (error) {
      console.error('Error saving updated chat history:', error);
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) {
      return 'Just now';
    } else if (diffInHours < 24) {
      return `${diffInHours}h ago`;
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Previous Chats
          </DialogTitle>
          <DialogDescription>
            Select a chat to continue where you left off
          </DialogDescription>
        </DialogHeader>
        
        <div className="max-h-[60vh] overflow-y-auto">
          {previousChats.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No previous chats found</p>
              <p className="text-sm">Your chat history will appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {previousChats
                .sort((a, b) => b.lastModified.getTime() - a.lastModified.getTime())
                .map((chat) => (
                  <div
                    key={chat.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer group"
                    onClick={() => handleLoadChat(chat)}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h4 className="font-medium truncate">{chat.title}</h4>
                        <span className="text-xs text-muted-foreground">
                          {chat.messages.length} messages
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{formatDate(chat.lastModified)}</span>
                        </div>
                        <span>{formatTime(chat.lastModified)}</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
} 