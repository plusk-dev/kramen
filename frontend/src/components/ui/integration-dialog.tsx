"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./dialog";
import { Button } from "./button";
import { Card, CardContent } from "./card";
import { getRequest } from "@/lib/rag_service";
import { Plus, X, Link } from "lucide-react";
import { IntegrationConfigDialog } from "./integration-config-dialog";

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

interface IntegrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConnectIntegration?: (connection: IntegrationConnection) => void;
}

export function IntegrationDialog({ 
  open, 
  onOpenChange, 
  onConnectIntegration
}: IntegrationDialogProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectedIntegrations, setConnectedIntegrations] = useState<IntegrationConnection[]>([]);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);

  useEffect(() => {
    if (open) {
      fetchIntegrations();
      loadConnectedIntegrations();
    }
  }, [open]);

  const fetchIntegrations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRequest<Integration[]>('/integrations/all');
      setIntegrations(data);
    } catch (err) {
      setError('Failed to fetch integrations');
      console.error('Error fetching integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadConnectedIntegrations = () => {
    try {
      const connections = JSON.parse(localStorage.getItem('integrationConnections') || '[]');
      setConnectedIntegrations(connections);
    } catch (err) {
      console.error('Error loading connected integrations:', err);
      setConnectedIntegrations([]);
    }
  };

  const handleConnectIntegration = (integration: Integration) => {
    setSelectedIntegration(integration);
    setConfigDialogOpen(true);
  };

  const handleSaveConnection = (connection: IntegrationConnection) => {
    setConnectedIntegrations(prev => [...prev, connection]);
    onConnectIntegration?.(connection);
    setConfigDialogOpen(false);
    setSelectedIntegration(null);
  };

  const isConnected = (integration: Integration) => {
    return connectedIntegrations.some(conn => conn.integration.id === integration.id);
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>Connect an App</DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto pr-2">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : error ? (
              <div className="flex items-center justify-center py-12 text-destructive">
                {error}
              </div>
            ) : integrations.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground">
                No integrations available
              </div>
            ) : (
              <div className="space-y-0">
                {integrations.map((integration, index) => (
                  <div key={integration.id}>
                    <div className="flex items-center gap-4 py-4 hover:bg-muted/50 transition-colors">
                      <div className="flex-shrink-0 relative w-8 h-8">
                        <img
                          src={integration.icon}
                          alt={integration.name}
                          className="w-8 h-8 rounded object-contain"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const fallback = target.nextElementSibling as HTMLElement;
                            if (fallback) {
                              fallback.classList.remove('hidden');
                            }
                          }}
                        />
                        <div className="absolute inset-0 bg-muted rounded flex items-center justify-center text-xs font-medium text-muted-foreground hidden">
                          {integration.name.charAt(0).toUpperCase()}
                        </div>
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-sm">{integration.name}</h3>
                        <p className="text-xs text-muted-foreground truncate">{integration.description}</p>
                      </div>
                      
                      {isConnected(integration) ? (
                        <Button
                          size="sm"
                          disabled
                          className="flex-shrink-0 bg-green-600 hover:bg-green-600 text-white"
                        >
                          Connected
                        </Button>
                      ) : (
                        <Button
                          onClick={() => handleConnectIntegration(integration)}
                          size="sm"
                          className="flex-shrink-0"
                        >
                          <Link className="h-4 w-4 mr-2" />
                          Connect
                        </Button>
                      )}
                    </div>
                    {index < integrations.length - 1 && (
                      <div className="border-b border-border" />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
          <span className="text-center">Support for custom integrations coming soon!</span>
        </DialogContent>
      </Dialog>

      <IntegrationConfigDialog
        open={configDialogOpen}
        onOpenChange={setConfigDialogOpen}
        integration={selectedIntegration}
        onSave={handleSaveConnection}
      />
    </>
  );
} 