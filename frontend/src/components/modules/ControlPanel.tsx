import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from '../ui/button';
import { useRunnerStore } from '../../core/runnerStore';
import { ConfigModal } from './ConfigModal';
import { AccountSheet } from './AccountSheet';

interface ControlPanelProps {
  status: string;
  name: string;
  wsConnected: boolean;
  backendReady: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({ status: propStatus, name, wsConnected, backendReady }) => {
  const { status: storeStatus, setStatus, startAction, statusMessage } = useRunnerStore();
  
  // Sync prop status with store status
  useEffect(() => {
    if (propStatus === 'RUNNING') {
      setStatus('running');
    } else if (propStatus === 'STANDBY') {
      // Only return to standby if we are not explicitly in the middle of a 'starting' state transition
      if (storeStatus !== 'starting') {
        setStatus('standby');
      }
    }
  }, [propStatus, setStatus, storeStatus]);

  const currentStatus = storeStatus;

  const statusConfig: Record<string, { color: string; label: string }> = {
    running: { color: 'bg-green-500 shadow-[0_0_15px_rgba(34,197,94,0.6)]', label: 'RUNNING' },
    starting: { color: 'bg-yellow-500 shadow-[0_0_15px_rgba(234,179,8,0.6)]', label: 'INITIALIZING' },
    standby: { color: 'bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.6)]', label: 'STANDBY' },
    error: { color: 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.6)]', label: 'CRITICAL ERROR' },
    failed: { color: 'bg-red-500 shadow-[0_0_15px_rgba(239,68,68,0.6)]', label: 'FAILED' },
    offline: { color: 'bg-zinc-500', label: 'OFFLINE' }
  };

  const displayStatus = backendReady ? (statusConfig[currentStatus] || statusConfig.standby) : statusConfig.offline;

  const [configOpen, setConfigOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  return (
    <div className="bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-xl p-8 h-full flex flex-col justify-between relative overflow-hidden transition-all duration-500">
      <ConfigModal open={configOpen} onOpenChange={setConfigOpen} />
      <AccountSheet open={accountOpen} onOpenChange={setAccountOpen} />
      
      {/* Premium Aurora Background Effect */}
      <div className="absolute inset-0 -z-10 overflow-hidden opacity-20">
        <motion.div 
          animate={{ 
            x: [0, 50, -50, 0], 
            y: [0, -30, 30, 0],
            scale: [1, 1.2, 0.9, 1] 
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className={`absolute -top-20 -right-20 w-80 h-80 blur-[100px] rounded-full transition-colors duration-2000 ${
            displayStatus.label.includes('FAILED') || displayStatus.label.includes('ERROR') ? 'bg-red-500' : 'bg-blue-600'
          }`}
        />
        <motion.div 
          animate={{ 
            x: [0, -40, 40, 0], 
            y: [0, 50, -50, 0],
            scale: [1, 0.8, 1.1, 1] 
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
          className={`absolute -bottom-20 -left-20 w-72 h-72 blur-[100px] rounded-full transition-colors duration-2000 ${
            displayStatus.label.includes('FAILED') || displayStatus.label.includes('ERROR') ? 'bg-orange-500/60' : 'bg-indigo-500/60'
          }`}
        />
      </div>
      
      <div>
        <div className="flex items-center gap-2 mb-4">
          <div className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${displayStatus.color}`} />
          <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-400 uppercase">
            Instance Status: {displayStatus.label}
          </span>
        </div>
        
        <h1 className="text-5xl font-bold mb-4 tracking-tight text-white/90">{name}</h1>
        <p className="text-zinc-400 max-w-md leading-relaxed">
          Native Tauri 2.0 runtime. {statusMessage ? <span className="text-red-400/80 block mt-1">{statusMessage}</span> : "Configure local nodes and manage automation scripts."}
        </p>

        {/* Pipeline Stack Visual */}
        <div className="mt-auto pt-6">
          <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Pipeline Stack</span>
          <div className="flex items-center gap-0 mt-3">
            <PipelineNode active={backendReady} label="Backend" />
            <PipelineConnector active={backendReady && wsConnected} />
            <PipelineNode active={wsConnected} label="WebSocket" pending={!wsConnected && backendReady} />
            <PipelineConnector active={wsConnected && currentStatus === 'running'} error={currentStatus === 'failed'} />
            <PipelineNode 
              active={currentStatus === 'running'} 
              label="Runner" 
              pulse={currentStatus === 'starting'} 
              error={currentStatus === 'failed' || currentStatus === 'error'} 
            />
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        {currentStatus === 'failed' || currentStatus === 'error' ? (
          <Button 
            onClick={startAction}
            className="bg-red-500 hover:bg-red-600 text-white px-8 py-6 h-auto text-lg font-semibold rounded-xl transition-all duration-300 shadow-[0_0_20px_rgba(239,68,68,0.2)]"
          >
            Retry Runner
          </Button>
        ) : (
          <Button 
            onClick={startAction}
            disabled={!backendReady || currentStatus === 'starting' || currentStatus === 'running'}
            className="bg-white text-black hover:bg-zinc-200 px-8 py-6 h-auto text-lg font-semibold rounded-xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            {currentStatus === 'starting' ? (
               <span className="flex items-center gap-2">
                 <span className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                 Starting...
               </span>
            ) : currentStatus === 'running' ? 'Running' : 'Start Runner'}
          </Button>
        )}
        
        <Button 
          variant="outline" 
          onClick={() => setAccountOpen(true)}
          className="border-white/10 bg-white/5 hover:bg-white/10 text-white px-8 py-6 h-auto text-lg font-semibold rounded-xl transition-all duration-300 flex items-center gap-2"
        >
          Settings & Auth
        </Button>
      </div>
    </div>
  );
};

interface NodeProps { active: boolean; label: string; pulse?: boolean; error?: boolean; pending?: boolean }

const PipelineNode = ({ active, label, pulse, error, pending }: NodeProps) => (
  <div className="flex flex-col items-center gap-2 group">
    <div className={`w-3.5 h-3.5 rounded-full border-2 transition-all duration-500 ${
      error ? 'bg-red-500 border-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.4)]' :
      active ? 'bg-green-500 border-green-500/50 shadow-[0_0_10px_rgba(34,197,94,0.4)]' : 
      pending ? 'bg-yellow-500/20 border-yellow-500/50 animate-pulse' :
      'bg-transparent border-white/10'
    } ${pulse ? 'animate-pulse scale-125' : ''}`} />
    <span className={`text-[10px] font-medium transition-colors duration-500 ${
      error ? 'text-red-400' :
      active ? 'text-green-400' : 
      pending ? 'text-yellow-400/60' :
      'text-zinc-600'
    }`}>{label}</span>
  </div>
);

const PipelineConnector = ({ active, error }: { active: boolean; error?: boolean }) => (
  <div className="w-12 h-[1px] mb-6 relative">
    <div className="absolute inset-0 bg-white/5" />
    <div className={`absolute inset-0 transition-all duration-1000 origin-left ${
      error ? 'bg-red-500/50 scale-x-100' :
      active ? 'bg-green-500/50 scale-x-100' : 
      'scale-x-0'
    }`} />
  </div>
);
