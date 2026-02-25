import React from 'react';
import { ControlPanel } from '../components/modules/ControlPanel';
import { StatsMatrix } from '../components/modules/StatsMatrix';
import { TerminalLog } from '../components/modules/TerminalLog';
import { useStore } from '../store';

const Dashboard: React.FC = () => {
  const { 
    logs, 
    health, 
    points, 
    taskStatus,
    wsConnected,
    backendReady,
  } = useStore();

  // Derive stats from the existing store
  const totalPoints = points?.current_points ?? 0;
  const cpuUsage = health?.system?.cpu_percent ?? 0;
  const networkIO = health?.network?.connection_rate 
    ? `${health.network.connection_rate.toFixed(1)} req/s` 
    : '0 req/s';
  
  // Format uptime
  const uptimeSeconds = health?.uptime_seconds ?? 0;
  const hours = Math.floor(uptimeSeconds / 3600);
  const minutes = Math.floor((uptimeSeconds % 3600) / 60);
  const seconds = Math.floor(uptimeSeconds % 60);
  const uptime = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

  const instanceStatus = taskStatus?.is_running ? 'RUNNING' : (backendReady ? 'STANDBY' : 'OFFLINE');
  const instanceName = 'RewardsCore';

  // Convert string logs to LogEntry format
  const logEntries = logs.map((log) => {
    // Match common timestamp formats: [10:00:00], 10:00:00, or 2024-05-20 10:00:00
    const timestampMatch = log.match(/(\d{2}:\d{2}:\d{2})/);
    const timestamp = timestampMatch ? timestampMatch[1] : new Date().toLocaleTimeString('en-US', { hour12: false });
    
    // Clean up level detection
    const upperLog = log.toUpperCase();
    let level = 'INFO';
    if (upperLog.includes('ERROR') || upperLog.includes('CRITICAL')) level = 'ERROR';
    else if (upperLog.includes('WARN')) level = 'WARN';
    else if (upperLog.includes('SUCCESS')) level = 'SUCCESS';
    else if (upperLog.includes('DEBUG')) level = 'DEBUG';
    else if (upperLog.includes('SYSTEM')) level = 'SYSTEM';

    // Remove the level prefix from the message if it exists to avoid double display
    const cleanMessage = log
      .replace(/^\[?(\d{4}-\d{2}-\d{2} )?\d{2}:\d{2}:\d{2}\]?\s*/, '')
      .replace(new RegExp(`^${level}:?\\s*`, 'i'), '')
      .replace(/^\[(INFO|ERROR|WARN|SUCCESS|DEBUG|SYSTEM)\]\s*/, '')
      .trim();

    return { timestamp, level, message: cleanMessage };
  });

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6 font-sans">
      <div className="max-w-[1600px] mx-auto grid grid-cols-12 gap-6">
        
        {/* Left Main Panel - col-span-8 */}
        <div className="col-span-8 space-y-6">
          <ControlPanel 
            status={instanceStatus} 
            name={instanceName}
            wsConnected={wsConnected}
            backendReady={backendReady}
          />
        </div>

        {/* Right Stats Panel - col-span-4 */}
        <div className="col-span-4">
          <StatsMatrix 
            points={totalPoints}
            cpu={cpuUsage}
            uptime={uptime}
            network={networkIO}
          />
        </div>

        {/* Bottom Log Panel - col-span-12 */}
        <div className="col-span-12">
          <TerminalLog logs={logEntries} wsConnected={wsConnected} />
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
