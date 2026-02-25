import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { ScrollArea } from '../ui/scroll-area';
import { fetchConfig, updateConfig } from '../../api';
import { toast } from 'sonner';

interface ConfigModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({ open, onOpenChange }) => {
  const [configText, setConfigText] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      loadConfig();
    }
  }, [open]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const config = await fetchConfig();
      // For now, we'll just show the JSON as string, 
      // but in a real app, we might want a YAML library or dedicated editor
      setConfigText(JSON.stringify(config, null, 2));
    } catch (error) {
      toast.error('Failed to load configuration');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const parsed = JSON.parse(configText);
      await updateConfig(parsed);
      toast.success('Configuration saved successfully');
      onOpenChange(false);
    } catch (error) {
      toast.error('Invalid configuration format');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl bg-zinc-950/95 border-white/10 backdrop-blur-2xl">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold tracking-tight">System Configuration</DialogTitle>
        </DialogHeader>
        
        <div className="py-4">
          <ScrollArea className="h-[400px] w-full rounded-md border border-white/5 bg-black/40 p-4">
            {loading ? (
              <div className="flex items-center justify-center h-full text-zinc-500">
                Loading...
              </div>
            ) : (
              <textarea
                value={configText}
                onChange={(e) => setConfigText(e.target.value)}
                className="w-full h-full bg-transparent font-mono text-sm text-zinc-300 outline-none resize-none min-h-[380px]"
                spellCheck={false}
              />
            )}
          </ScrollArea>
          <p className="text-[10px] text-zinc-500 mt-2 italic">
            Note: Currently editing in JSON format for compatibility. Ensure valid syntax before saving.
          </p>
        </div>

        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} className="border-white/10 text-zinc-400 hover:text-white">
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving} className="bg-white text-black hover:bg-zinc-200">
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
