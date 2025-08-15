"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./dialog";
import { Button } from "./button";
import { Card, CardContent, CardHeader, CardTitle } from "./card";
import { getRequest } from "@/lib/rag_service";
import { Plus, X } from "lucide-react";

interface Integration {
  id: number;
  name: string;
  uuid: string;
  icon: string;
  limit: number;
  auth_structure: any;
  created: string;
}

interface AddIntegrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfigureIntegration?: (integration: Integration) => void;
}

export function AddIntegrationDialog({ open, onOpenChange, onConfigureIntegration }: AddIntegrationDialogProps) {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (open) {
      fetchIntegrations();
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

  const handleAddIntegration = (integration: Integration) => {
    console.log('Configuring integration:', integration);
    onConfigureIntegration?.(integration);
    onOpenChange(false);
  };

  const handleCardClick = (integrationId: number) => {
    setExpandedId(expandedId === integrationId ? null : integrationId);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden" showCloseButton={false}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Add Integration</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onOpenChange(false)}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto pr-2">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-8 text-destructive">
              {error}
            </div>
          ) : integrations.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              No integrations available
            </div>
          ) : (
            <div className="space-y-3">
              {integrations.map((integration) => (
                <Card key={integration.id} className="hover:bg-primary/10 cursor-pointer transition-shadow">
                  <div 
                    className="flex items-center justify-between px-3"
                    onClick={() => handleCardClick(integration.id)}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-16 h-16 flex items-center justify-center">
                        {integration.icon ? (
                          <img
                            src={integration.icon}
                            alt={integration.name}
                            className="w-12 h-12 object-contain rounded-full"
                            onError={(e) => {
                              // Fallback to text if image fails to load
                              const target = e.target as HTMLImageElement;
                              target.style.display = 'none';
                              target.nextElementSibling?.classList.remove('hidden');
                            }}
                          />
                        ) : null}
                        <span className="text-2xl font-semibold text-primary hidden">
                          {integration.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <CardTitle className="text-base">{integration.name}</CardTitle>
                        <div className="text-sm text-muted-foreground">
                          Created: {formatDate(integration.created)}
                        </div>
                      </div>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAddIntegration(integration);
                      }}
                      size="sm"
                      className="mr-4"
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {expandedId === integration.id && (
                    <div className="px-3 border-t border-border/50">
                      <div className="pt-3">
                        <h4 className="text-sm font-medium mb-2">Authentication Structure:</h4>
                        <div className="space-y-2">
                          {Object.entries(integration.auth_structure).map(([key, config]: [string, any]) => (
                            <div key={key} className="text-sm bg-muted/50 p-2 rounded">
                              <div className="font-mono font-medium">{key}</div>
                              <div className="text-muted-foreground flex items-center gap-2 mt-1">
                                <span>Type: {config.type}</span>
                                <span>•</span>
                                <span>Location: {config.loc}</span>
                                <span>•</span>
                                <span className={`px-2 py-0.5 rounded-full text-xs ${
                                  config.required 
                                    ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400' 
                                    : 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                                }`}>
                                  {config.required ? 'Required' : 'Optional'}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
} 