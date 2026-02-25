import React, { useEffect, useState } from 'react';
import { Progress } from '../ui/progress';
import { motion, animate } from 'framer-motion';

interface StatsMatrixProps {
  points: number;
  cpu: number;
  uptime: string;
  network: string;
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
  <div className={`bg-white/[0.03] backdrop-blur-xl border ${highlighted ? 'border-green-500/30' : 'border-white/10'} rounded-xl p-6 h-[213px] flex flex-col justify-between transition-all duration-300 hover:bg-white/[0.05] group overflow-hidden relative`}>
    {highlighted && (
      <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/5 blur-[50px] -mr-16 -mt-16 rounded-full" />
    )}
    <span className="text-[10px] font-bold tracking-[0.2em] text-zinc-500 uppercase group-hover:text-zinc-400 transition-colors relative z-10">{label}</span>
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

export const StatsMatrix: React.FC<StatsMatrixProps> = ({ points, cpu, uptime, network }) => {
  return (
    <div className="grid grid-cols-2 gap-6 h-full">
      <StatCard label="Total Points" value={<Counter value={points} />} highlighted={points > 0} />
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
