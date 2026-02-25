import { create } from 'zustand';
import { startTask, stopTask } from '../api';

export type RunnerStatus = 'standby' | 'starting' | 'running' | 'error' | 'failed';

interface RunnerState {
  status: RunnerStatus;
  statusMessage: string | null;
  setStatus: (status: RunnerStatus, message?: string | null) => void;
  startAction: () => Promise<void>;
  stopAction: () => Promise<void>;
  reset: () => void;
}

export const useRunnerStore = create<RunnerState>((set, get) => ({
  status: 'standby',
  statusMessage: null,
  setStatus: (status, message = null) => set({ status, statusMessage: message }),
  
  startAction: async () => {
    const { status } = get();
    if (status === 'starting' || status === 'running') return;
    
    set({ status: 'starting', statusMessage: 'Initializing process...' });
    try {
      await startTask({});
      // Note: The actual 'running' status will be updated via WebSocket/Heartbeat
    } catch (error) {
      console.error('Failed to start runner:', error);
      set({ status: 'error', statusMessage: 'Critical start failure' });
    }
  },

  stopAction: async () => {
    const { status } = get();
    if (status !== 'running') return;
    
    try {
      await stopTask();
    } catch (error) {
      console.error('Failed to stop runner:', error);
    }
  },

  reset: () => set({ status: 'standby', statusMessage: null }),
}));
