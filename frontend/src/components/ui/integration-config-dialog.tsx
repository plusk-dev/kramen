"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./dialog";
import { Button } from "./button";
import { Input } from "./input";
import { Label } from "./label";
import { AlertCircle, Check } from "lucide-react";

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

interface IntegrationConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  integration: Integration | null;
  onSave: (connection: IntegrationConnection) => void;
}

export function IntegrationConfigDialog({
  open,
  onOpenChange,
  integration,
  onSave
}: IntegrationConfigDialogProps) {
  const [headersJson, setHeadersJson] = useState('{\n  "Authorization": "Bearer your-token-here",\n  "Content-Type": "application/json"\n}');
  const [apiBase, setApiBase] = useState('https://api.example.com');
  const [error, setError] = useState<string | null>(null);
  const [isValidJson, setIsValidJson] = useState(true);

  const validateJson = (jsonString: string) => {
    try {
      JSON.parse(jsonString);
      setIsValidJson(true);
      setError(null);
      return true;
    } catch (err) {
      setIsValidJson(false);
      setError('Invalid JSON format');
      return false;
    }
  };

  const handleJsonChange = (value: string) => {
    setHeadersJson(value);
    validateJson(value);
  };

  const handleSave = () => {
    if (!integration) return;

    if (!validateJson(headersJson)) {
      return;
    }

    if (!apiBase.trim()) {
      setError('API Base URL is required');
      return;
    }

    try {
      const headers = JSON.parse(headersJson);
      const connection: IntegrationConnection = {
        integration,
        headers,
        api_base: apiBase.trim(),
        connectedAt: new Date().toISOString()
      };

      // Store in localStorage
      const existingConnections = JSON.parse(localStorage.getItem('integrationConnections') || '[]');
      const updatedConnections = [...existingConnections, connection];
      localStorage.setItem('integrationConnections', JSON.stringify(updatedConnections));

      onSave(connection);
      onOpenChange(false);
      
      // Reset form
      setHeadersJson('{\n  "Authorization": "Bearer your-token-here",\n  "Content-Type": "application/json"\n}');
      setApiBase('https://api.example.com');
      setError(null);
    } catch (err) {
      setError('Failed to save connection');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {integration && (
              <img
                src={integration.icon}
                alt={integration.name}
                className="w-6 h-6 rounded object-contain"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                }}
              />
            )}
            Configure {integration?.name} Connection
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="api_base">API Base URL</Label>
            <Input
              id="api_base"
              type="url"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value)}
              placeholder="https://api.example.com"
              className="font-mono"
            />
            <p className="text-sm text-muted-foreground">
              The base URL for this integration's API endpoints
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="headers">Headers (JSON format)</Label>
            <div className="relative">
              <textarea
                id="headers"
                value={headersJson}
                onChange={(e) => handleJsonChange(e.target.value)}
                className={`w-full h-40 p-3 border rounded-md font-mono text-sm resize-none ${
                  isValidJson 
                    ? 'border-border focus:border-ring' 
                    : 'border-destructive focus:border-destructive'
                } focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2`}
                placeholder="Enter your headers in JSON format..."
              />
              <div className="absolute top-2 right-2">
                {isValidJson ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                )}
              </div>
            </div>
            {error && (
              <p className="text-sm text-destructive flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {error}
              </p>
            )}
          </div>

          <div className="text-sm text-muted-foreground">
            <p>Configure the connection settings for this integration:</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li><strong>API Base URL:</strong> The root URL for API requests</li>
              <li><strong>Authorization:</strong> Bearer token, API key, etc.</li>
              <li><strong>Content-Type:</strong> Usually application/json</li>
              <li><strong>Custom headers:</strong> Any additional headers specific to the service</li>
            </ul>
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={!isValidJson || !integration || !apiBase.trim()}
          >
            Connect Integration
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
} 