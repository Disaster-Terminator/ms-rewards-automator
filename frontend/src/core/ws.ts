import { listen } from '@tauri-apps/api/event';
import { invoke } from '@tauri-apps/api/core';
import { useAppStore } from './store';

/**
 * Initialize WebSocket and Tauri IPC listeners.
 * This should be called once at the application root.
 */
export const initCoreBridge = async () => {
  const store = useAppStore.getState();

  // Listen for instance status changes
  await listen<{ status: 'STANDBY' | 'RUNNING' | 'ERROR' }>('instance-status', (event) => {
    store.setInstanceStatus(event.payload.status);
  });

  // Listen for stats updates
  await listen<{ points: number; cpu: number; uptime: string; network: string }>('stats-update', (event) => {
    store.setTotalPoints(event.payload.points);
    store.setCpuUsage(event.payload.cpu);
    store.setUptime(event.payload.uptime);
    store.setNetworkIO(event.payload.network);
  });

  // Listen for logs
  await listen<{ timestamp: string; level: any; message: string }>('log-event', (event) => {
    store.addLog(event.payload);
  });

  console.log('Core Bridge Initialized');
};

/**
 * Send commands to the backend via Tauri IPC
 */
export const sendCommand = async (command: string, args: any = {}) => {
  try {
    return await invoke('handle_command', { command, args });
  } catch (error) {
    console.error(`Failed to send command ${command}:`, error);
    throw error;
  }
};
