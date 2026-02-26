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
    pointsHistory,
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
    // Try structured parsing for "TIMESTAMP - NAME - LEVEL - MESSAGE"
    const parts = log.split(' - ');
    
    if (parts.length >= 4 && /^(\d{4}-\d{2}-\d{2} )?\d{2}:\d{2}:\d{2}/.test(parts[0])) {
      const fullTimestamp = parts[0]; // e.g., "2024-05-20 10:00:00,123"
      const timestampMatch = fullTimestamp.match(/(\d{2}:\d{2}:\d{2})/);
      const timestamp = timestampMatch ? timestampMatch[1] : fullTimestamp;
      
      const level = parts[2].trim().toUpperCase();
      const message = parts.slice(3).join(' - ').trim();
      
      return { timestamp, level, message };
    }

    // Fallback for other formats (like uvicorn or plain messages)
    const timestampMatch = log.match(/(\d{2}:\d{2}:\d{2})/);
    const timestamp = timestampMatch ? timestampMatch[1] : new Date().toLocaleTimeString('en-US', { hour12: false });
    
    const upperLog = log.toUpperCase();
    let level = 'INFO';
    if (upperLog.includes('ERROR') || upperLog.includes('CRITICAL')) level = 'ERROR';
    else if (upperLog.includes('WARN')) level = 'WARN';
    else if (upperLog.includes('SUCCESS')) level = 'SUCCESS';
    else if (upperLog.includes('DEBUG')) level = 'DEBUG';
    else if (upperLog.includes('SYSTEM')) level = 'SYSTEM';

    const cleanMessage = log
      .replace(/^\[?(\d{4}-\d{2}-\d{2} )?\d{2}:\d{2}:\d{2}([,.]\d{3})?\]?\s*/, '')
      .replace(new RegExp(`^${level}:?\\s*`, 'i'), '')
      .replace(/^\[(INFO|ERROR|WARN|SUCCESS|DEBUG|SYSTEM)\]\s*/, '')
      .replace(/^\s*-\s*/, '') 
      .trim();

    return { timestamp, level, message: cleanMessage || log.trim() };
  });

  return (
    <div className="h-screen w-screen overflow-y-auto overflow-x-hidden bg-[#0a0a0a] text-white p-6 font-sans flex flex-col justify-start">
      <div className="max-w-[1600px] min-h-full mx-auto flex flex-col gap-6 w-full">
        
        {/* Top Section: Control and Stats (Constrained Height) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-none h-[45vh] min-h-[380px] max-h-[450px]">
          {/* Left Main Panel - col-span-8 */}
          <div className="lg:col-span-7 xl:col-span-8 h-full">
            <ControlPanel 
              status={instanceStatus} 
              name={instanceName}
              wsConnected={wsConnected}
              backendReady={backendReady}
            />
          </div>

          {/* Right Stats Panel - col-span-4 */}
          <div className="lg:col-span-5 xl:col-span-4 h-full">
            <StatsMatrix 
              points={totalPoints}
              cpu={cpuUsage}
              uptime={uptime}
              network={networkIO}
              pointsHistory={pointsHistory}
            />
          </div>
        </div>

        {/* Bottom Section: Log Panel (Fills remaining space) */}
        <div className="flex-1 min-h-[200px]">
          <TerminalLog logs={logEntries} wsConnected={wsConnected} />
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
