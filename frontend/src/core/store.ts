import { create } from 'zustand';

interface LogEntry {
  timestamp: string;
  level: 'INFO' | 'SUCCESS' | 'DEBUG' | 'WARN' | 'ERROR' | 'SYSTEM';
  message: string;
}

interface AppState {
  instanceStatus: 'STANDBY' | 'RUNNING' | 'ERROR';
  instanceName: string;
  totalPoints: number;
  cpuUsage: number;
  uptime: string;
  networkIO: string;
  logs: LogEntry[];
  
  // Actions
  setInstanceStatus: (status: AppState['instanceStatus']) => void;
  setTotalPoints: (points: number) => void;
  setCpuUsage: (usage: number) => void;
  setUptime: (uptime: string) => void;
  setNetworkIO: (io: string) => void;
  addLog: (log: LogEntry) => void;
  clearLogs: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  instanceStatus: 'STANDBY',
  instanceName: 'Instance #420-Alpha',
  totalPoints: 1240.50,
  cpuUsage: 14,
  uptime: '04:20:11',
  networkIO: '24.8 MB/s',
  logs: [
    { timestamp: '14:20:01', level: 'INFO', message: 'Initializing Tauri 2.0.0-rc.0 core components...' },
    { timestamp: '14:20:02', level: 'SYSTEM', message: 'Loading architecture "x86_64-apple-darwin"' },
    { timestamp: '14:20:02', level: 'SYSTEM', message: 'NETWORK: Attempting handshake with remote cluster alpha-420...' },
    { timestamp: '14:20:03', level: 'DEBUG', message: 'DEBUG: malloc_zone_malloc 0x7ff847c2b000 size=48' },
    { timestamp: '14:20:05', level: 'SUCCESS', message: 'SUCCESS: Connection established. Latency 14ms.' },
    { timestamp: '14:20:06', level: 'INFO', message: 'RUNNER: Waiting for manual start command...' },
  ],

  setInstanceStatus: (status) => set({ instanceStatus: status }),
  setTotalPoints: (points) => set({ totalPoints: points }),
  setCpuUsage: (usage) => set({ cpuUsage: usage }),
  setUptime: (uptime) => set({ uptime: uptime }),
  setNetworkIO: (io) => set({ networkIO: io }),
  addLog: (log) => set((state) => ({ logs: [...state.logs.slice(-99), log] })), // Keep last 100 logs
  clearLogs: () => set({ logs: [] }),
}));
