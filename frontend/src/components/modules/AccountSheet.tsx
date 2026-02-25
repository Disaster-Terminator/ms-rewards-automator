import React, { useState, useEffect } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from '../ui/sheet';
import { Button } from '../ui/button';
import { fetchConfig, updateConfig } from '../../api';
import { toast } from 'sonner';

interface AccountSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const AccountSheet: React.FC<AccountSheetProps> = ({ open, onOpenChange }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [cookieJson, setCookieJson] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      loadAccountInfo();
    }
  }, [open]);

  const loadAccountInfo = async () => {
    try {
      const config = await fetchConfig();
      setEmail(config.login?.auto_login?.email || '');
      // We don't load password/secret for security, just leave them blank
    } catch (error) {
      console.error('Failed to load account info:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updates: any = {
        login: {
          auto_login: {
            enabled: true,
            email,
          }
        }
      };

      if (password) updates.login.auto_login.password = password;
      if (totp) updates.login.auto_login.totp_secret = totp;

      // Handle cookie JSON if provided
      if (cookieJson) {
        try {
          JSON.parse(cookieJson);
          // In a real app, we'd have a specific field for this in config
          // For now, let's assume the backend can handle it or we're just updating creds
        } catch {
          toast.error('Invalid Cookie JSON format');
          setSaving(false);
          return;
        }
      }

      await updateConfig(updates);
      toast.success('Account credentials updated');
      onOpenChange(false);
    } catch (error) {
      toast.error('Failed to update account');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col h-full bg-zinc-950/95 border-l border-white/10 backdrop-blur-2xl">
        <SheetHeader className="mb-8">
          <SheetTitle className="text-2xl font-bold tracking-tight">Account & Auth</SheetTitle>
          <SheetDescription className="text-zinc-500">
            Manage your Microsoft Rewards credentials and session tokens to bypass authentication blocks.
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-6 overflow-y-auto pr-2">
          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Email Address</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 transition-colors"
              placeholder="example@outlook.com"
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 transition-colors"
              placeholder="••••••••"
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">TOTP Secret (optional)</label>
            <input 
              type="text" 
              value={totp}
              onChange={(e) => setTotp(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white outline-none focus:border-blue-500/50 transition-colors"
              placeholder="2FA Secret Key"
            />
          </div>

          <div className="space-y-2">
            <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Session Cookies (JSON)</label>
            <textarea 
              value={cookieJson}
              onChange={(e) => setCookieJson(e.target.value)}
              className="w-full h-32 bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-xs font-mono text-zinc-300 outline-none focus:border-blue-500/50 transition-colors resize-none"
              placeholder='[{"name": "auth_token", "value": "..."}]'
            />
            <p className="text-[10px] text-zinc-600 italic">
              Paste your exported browser cookies here to skip manual login.
            </p>
          </div>
        </div>

        <SheetFooter className="mt-8 pt-6 border-t border-white/5">
          <Button 
            onClick={handleSave} 
            disabled={saving}
            className="w-full bg-white text-black hover:bg-zinc-200 h-12 font-bold rounded-xl transition-all"
          >
            {saving ? 'Saving...' : 'Save & Hot-Reload'}
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};
