"use client";

import { useState, useEffect } from "react";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { ConnectedAppsDock } from "./connected-apps-dock";
import { ChatNavbar } from "./chat-navbar";
import { ChatMessage, Step, Action } from "./message-list";
import { Link } from "lucide-react";
import { ArrowRight } from "lucide-react";
import { integrationConnectionUtils } from "@/lib/utils";
import { API_BASE } from "@/lib/rag_service";

interface Integration {
  id: number;
  name: string;
  description: string;
  uuid: string;
  icon: string;
  limit: number;
  auth_structure: {
    name: string;
    loc: string;
    format: string;
  };
  created: string;
}

interface IntegrationConnection {
  integration: Integration;
  headers: Record<string, string>;
  api_base: string;
  connectedAt: string;
}

interface ConnectedApp {
  id: string;
  name: string;
  icon: string;
  type: "linear" | "stripe" | "github" | "slack" | "notion";
}

interface StreamEvent {
  type: string;
  [key: string]: any;
}

function ChatEmptyState({ onExampleClick }: { onExampleClick: (text: string) => void }) {
  const examples = [
    "look at subscriptions from stripe and create an issue on linear for the latest cancelled subscription with the cancellation reason",
    "create a meeting between me and user@example.com for tomorrow 4PM"
  ];
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className=" text-2xl mb-4">Try Asking</div>
      <div className="flex flex-col gap-3 w-full max-w-md mb-6">
        {examples.map((ex, i) => (
          <button
            key={i}
            className="w-full border border-border rounded px-4 py-2 text-sm text-muted-foreground flex items-center justify-between hover:bg-accent transition-colors"
            onClick={() => onExampleClick(ex)}
            type="button"
          >
            <span className="flex-1">{ex}</span>
            <ArrowRight className="ml-2 flex-shrink-0 h-4 w-4" />
          </button>
        ))}
      </div>
      <div className="text-lg mb-4">...or anything else related to the 100+ supported apps</div>
    </div>
  );
}

export function ChatContainer() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [connectedApps, setConnectedApps] = useState<ConnectedApp[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  // Load connected integrations from localStorage on component mount
  useEffect(() => {
    loadConnectedAppsFromStorage();
  }, []);

  const loadConnectedAppsFromStorage = () => {
    try {
      const connections = integrationConnectionUtils.getConnectedIntegrations();
      const apps: ConnectedApp[] = connections.map(connection => ({
        id: `connected-${connection.integration.id}`,
        name: connection.integration.name,
        icon: connection.integration.icon,
        type: connection.integration.name.toLowerCase() as ConnectedApp['type']
      }));
      setConnectedApps(apps);
    } catch (error) {
      console.error('Error loading connected apps from storage:', error);
    }
  };

  const addMessage = (content: string, sender: "user" | "assistant", steps?: Step[], isLoading?: boolean) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      sender,
      timestamp: new Date(),
      steps: steps || [],
      isLoading: isLoading || false
    };
    setMessages(prev => [...prev, newMessage]);
    return newMessage;
  };

  const updateMessage = (messageId: string, updates: Partial<ChatMessage>) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ));
  };

  const makeStreamingRequest = async (query: string) => {
    setIsProcessing(true);
    
    try {
      // Get connected integrations and their headers
      const connections = integrationConnectionUtils.getConnectedIntegrations();
      
      const integrations = connections.map(conn => conn.integration.uuid);
      const request_headers: Record<string, Record<string, string>> = {};
      const request_api_base: Record<string, string> = {};
      
      connections.forEach(conn => {
        request_headers[conn.integration.uuid] = conn.headers;
        request_api_base[conn.integration.uuid] = conn.api_base;
      });

      // Create the request payload
      const payload = {
        query,
        integrations,
        llm_config: {
          model: "openai/gpt-4.1",
          temperature: 0.7,
          max_tokens: 1000
        },
        api_base: request_api_base,
        request_headers,
        rephraser: true,
        rephrasal_instructions: "Please rephrase and clarify the user's request for better understanding and execution."
      };

      // Make the streaming request
      const response = await fetch(`${API_BASE}/run/deep`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Create assistant message to update during streaming
      const assistantMessage = addMessage("Processing your request...", "assistant", [], true);
      let steps: Step[] = [];
      let currentStep: Step | null = null;
      let maxSteps = 0;
      let stepCount = 0;

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body reader available');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.trim()) {
            try {
              const event: StreamEvent = JSON.parse(line);
              
              switch (event.type) {
                case 'metadata':
                  maxSteps = event.max_steps || 0;
                  updateMessage(assistantMessage.id, {
                    content: `Processing your request with ${event.integrations?.length || 0} integrations...`,
                    steps: []
                  });
                  break;
                
                case 'step_start':
                  currentStep = {
                    id: `step-${event.step_number}`,
                    title: `Step ${event.step_number}: ${event.integration_name || 'Processing'}`,
                    content: event.reasoning || 'Starting step...',
                    status: 'running' as const,
                    actions: [],
                    integration_uuid: event.integration_uuid,
                    animationDelay: stepCount * 150 // Stagger animation by 150ms
                  };
                  steps = [...steps, currentStep];
                  stepCount++;
                  updateMessage(assistantMessage.id, {
                    content: `Step ${event.step_number} of ${maxSteps}`,
                    steps: [...steps],
                    isLoading: true
                  });
                  break;
                
                case 'step_complete':
                  if (currentStep && currentStep.id === `step-${event.step_number}`) {
                    currentStep.status = 'completed' as const;
                    currentStep.content = event.natural_language_response || currentStep.content;
                    
                    steps = steps.map(step => 
                      step.id === currentStep!.id ? currentStep! : step
                    );
                    
                    updateMessage(assistantMessage.id, {
                      content: `Step ${event.step_number} of ${maxSteps} completed`,
                      steps: [...steps],
                      isLoading: true
                    });
                  }
                  break;
                
                case 'final_response':
                  updateMessage(assistantMessage.id, {
                    content: event.final_response || 'Request completed',
                    steps: [...steps],
                    isLoading: true
                  });
                  break;
                
                case 'complete':
                  // Mark the final message as complete
                  updateMessage(assistantMessage.id, {
                    steps: steps.map(step => ({ ...step, status: 'completed' as const })),
                    isLoading: false
                  });
                  break;
                
                default:
                  console.log('Unknown event type:', event.type, event);
              }
            } catch (e) {
              console.error('Error parsing streaming event:', e, line);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error making streaming request:', error);
      addMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error occurred'}`, "assistant", [], false);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSendMessage = async (content: string, sender: "user" | "assistant") => {
    if (sender === "user") {
      // Add user message
      addMessage(content, "user");
      
      // Save chat to localStorage
      saveChatToHistory([...messages, { 
        id: Date.now().toString(), 
        content, 
        sender, 
        timestamp: new Date(), 
        steps: [] 
      }]);
      
      // Make streaming request for assistant response
      await makeStreamingRequest(content);
    }
  };

  const saveChatToHistory = (chatMessages: ChatMessage[]) => {
    if (chatMessages.length === 0) return;
    
    const chatId = currentChatId || `chat-${Date.now()}`;
    const title = chatMessages[0]?.content.slice(0, 50) + (chatMessages[0]?.content.length > 50 ? '...' : '');
    
    const chatData = {
      id: chatId,
      title,
      messages: chatMessages,
      createdAt: currentChatId ? new Date() : new Date(),
      lastModified: new Date()
    };
    
    try {
      const existing = localStorage.getItem('kramen-chat-history');
      const existingChats = existing ? JSON.parse(existing) : [];
      
      // Remove existing chat if it exists
      const filteredChats = existingChats.filter((chat: any) => chat.id !== chatId);
      
      // Add new chat at the beginning
      const updatedChats = [chatData, ...filteredChats];
      
      // Keep only the last 50 chats
      const limitedChats = updatedChats.slice(0, 50);
      
      localStorage.setItem('kramen-chat-history', JSON.stringify(limitedChats));
      setCurrentChatId(chatId);
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  };

  const handleLoadChat = (chat: any) => {
    setMessages(chat.messages);
    setCurrentChatId(chat.id);
  };

  const handleNewChat = () => {
    setMessages([]);
    setCurrentChatId(null);
    setInputValue("");
  };

  const handleAddApp = () => {
    // This is now handled by the ConnectedAppsDock component
    console.log("Add app clicked");
  };

  const handleAppClick = (app: ConnectedApp) => {
    // TODO: Implement app click functionality
    console.log("App clicked:", app);
  };

  const handleAppSettings = (app: ConnectedApp) => {
    // TODO: Implement app settings functionality
    console.log("App settings clicked:", app);
  };

  const handleConnectIntegration = (connection: IntegrationConnection) => {
    // Convert integration connection to connected app format
    const newConnectedApp: ConnectedApp = {
      id: `connected-${connection.integration.id}`,
      name: connection.integration.name,
      icon: connection.integration.icon,
      type: connection.integration.name.toLowerCase() as ConnectedApp['type']
    };
    
    setConnectedApps(prev => [...prev, newConnectedApp]);
    console.log("Connected integration:", connection.integration);
    console.log("With headers:", connection.headers);
  };

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      <ChatNavbar onLoadChat={handleLoadChat} onNewChat={handleNewChat} onClearChat={handleNewChat} />
      <div className="flex justify-center flex-1 overflow-hidden">
        <div className="w-full max-w-4xl flex flex-col">
          <div className="flex-1 overflow-hidden">
            {messages.length === 0 ? (
              <ChatEmptyState onExampleClick={setInputValue} />
            ) : (
              <MessageList messages={messages} />
            )}
          </div>
          <div className="border-t bg-card flex-shrink-0">
            <ConnectedAppsDock
              connectedApps={connectedApps}
              onAddApp={handleAddApp}
              onAppClick={handleAppClick}
              onAppSettings={handleAppSettings}
              onConnectIntegration={handleConnectIntegration}
            />
            <MessageInput 
              onSendMessage={handleSendMessage} 
              value={inputValue} 
              setValue={setInputValue}
              disabled={isProcessing}
            />
          </div>
        </div>
      </div>
    </div>
  );
} 