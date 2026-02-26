import React, { useEffect, useState } from 'react';
import { Progress } from '../ui/progress';
import { motion, animate } from 'framer-motion';
import { Area, AreaChart, ResponsiveContainer, YAxis } from 'recharts';

interface StatsMatrixProps {
  points: number;
  cpu: number;
  uptime: string;
  network: string;
  pointsHistory: number[];
}

const Counter: React.FC<{ value: number }> = ({ value }) => {
  const [displayValue, setDisplayValue] = useState(value);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    setIsUpdating(true);
    const controls = animate(displayValue, value, {
      duration: 1.2,
      ease: "easeOut",
      onUpdate: (latest) => setDisplayValue(Math.floor(latest)),
      onComplete: () => {
        setTimeout(() => setIsUpdating(false), 2000);
      }
    });
    return () => controls.stop();
  }, [value]);

  return (
    <div className="relative inline-block">
      <span className="relative z-10">{displayValue.toLocaleString()}</span>
      {isUpdating && (
        <motion.div 
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1.2 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 -z-10 bg-green-500/20 blur-xl rounded-full"
        />
      )}
    </div>
  );
};

const StatCard: React.FC<{ label: string; value: React.ReactNode; children?: React.ReactNode; highlighted?: boolean }> = ({ label, value, children, highlighted }) => (
  <div className={`bg-white/[0.04] backdrop-blur-2xl border ${highlighted ? 'border-green-500/30 shadow-[0_0_20px_rgba(34,197,94,0.05)]' : 'border-white/10 shadow-lg'} rounded-2xl p-4 xl:p-6 h-full flex flex-col justify-between transition-all duration-500 hover:bg-white/[0.07] hover:border-white/20 group overflow-hidden relative`}>
    {highlighted && (
      <div className="absolute top-0 right-0 w-40 h-40 bg-green-500/10 blur-[60px] -mr-20 -mt-20 rounded-full" />
    )}
    <span className="text-[10px] font-bold tracking-[0.25em] text-zinc-400 uppercase group-hover:text-zinc-300 transition-colors relative z-10">{label}</span>
    <div className="space-y-3 relative z-10">
      <motion.div 
        layout
        className="text-3xl font-semibold text-white/90 tracking-tight transition-all duration-500"
      >
        {value}
      </motion.div>
      {children}
    </div>
  </div>
);

export const StatsMatrix: React.FC<StatsMatrixProps> = ({ points, cpu, uptime, network, pointsHistory }) => {
  const chartData = pointsHistory.map((val, i) => ({ val, i }));
  
  // Debug line to see if data is actually there
  const hasData = chartData.length > 0;

  return (
    <div className="grid grid-cols-2 grid-rows-2 gap-4 xl:gap-6 h-full">
      <StatCard label="Total Points" value={<Counter value={points} />} highlighted={points > 0}>
        <div className="h-16 w-full -mb-2 -mx-1 relative">
          {!hasData && (
            <div className="absolute inset-0 flex items-center justify-center text-[8px] text-zinc-600 uppercase tracking-tighter">
              Waiting for data stream...
            </div>
          )}
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={hasData ? chartData : [{val: 0, i: 0}, {val: 0, i: 1}]}>
              <defs>
                <linearGradient id="colorPoints" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <YAxis hide domain={['dataMin - 5', 'dataMax + 5']} />
              <Area 
                type="monotone" 
                dataKey="val" 
                stroke={hasData ? "#10b981" : "transparent"}
                fillOpacity={1} 
                fill={hasData ? "url(#colorPoints)" : "transparent"} 
                strokeWidth={2}
                isAnimationActive={true}
                dot={hasData ? { r: 1.5, fill: '#10b981', strokeWidth: 0 } : false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </StatCard>
      <StatCard label="CPU Usage" value={`${cpu}%`}>
        <div className="relative pt-1">
          <Progress value={cpu} className="h-1.5 bg-white/5 transition-all duration-700 ease-in-out" />
          {/* Subtle glow for progress */}
          <motion.div 
            className="absolute top-1.5 left-0 h-[2px] bg-blue-500/30 blur-sm transition-all duration-700 pointer-events-none" 
            initial={{ width: 0 }}
            animate={{ width: `${cpu}%` }}
          />
        </div>
      </StatCard>
      <StatCard label="Uptime" value={uptime} />
      <StatCard label="Network I/O" value={network} />
    </div>
  );
};
