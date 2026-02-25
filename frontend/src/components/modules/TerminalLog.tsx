import React, { useEffect, useRef } from 'react';
import { ScrollArea } from '../ui/scroll-area';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

interface TerminalLogProps {
  logs: LogEntry[];
  wsConnected: boolean;
}

export const TerminalLog: React.FC<TerminalLogProps> = ({ logs, wsConnected }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScrollPaused, setIsAutoScrollPaused] = React.useState(false);
  const [isAtBottom, setIsAtBottom] = React.useState(true);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.currentTarget;
    const scrollBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
    // If we are within 50px of the bottom, consider it "at bottom"
    setIsAtBottom(scrollBottom < 50);
  };

  useEffect(() => {
    if (!isAutoScrollPaused && isAtBottom) {
      const scrollContainer = scrollRef.current?.querySelector('[data-radix-scroll-area-viewport]');
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight;
      }
    }
  }, [logs, isAutoScrollPaused, isAtBottom]);

  const getLevelStyles = (level: string, message: string) => {
    const lowerMsg = message.toLowerCase();
    
    // Semantic Highlighting
    if (level === 'ERROR' || lowerMsg.includes('failed') || lowerMsg.includes('exception') || lowerMsg.includes('失败')) {
      return {
        row: 'bg-red-500/5',
        level: 'text-red-400 drop-shadow-[0_0_8px_rgba(248,113,113,0.5)]',
        message: 'text-red-200/90'
      };
    }
    if (level === 'SUCCESS' || lowerMsg.includes('✓') || lowerMsg.includes('完成') || lowerMsg.includes('成功')) {
      return {
        row: 'bg-green-500/5',
        level: 'text-green-400 drop-shadow-[0_0_8px_rgba(74,222,128,0.5)]',
        message: 'text-green-200/90'
      };
    }
    if (level === 'WARN' || lowerMsg.includes('warning') || lowerMsg.includes('警告')) {
      return {
        row: 'bg-yellow-500/5',
        level: 'text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.5)]',
        message: 'text-yellow-200/90'
      };
    }
    if (level === 'INFO') {
      return {
        row: '',
        level: 'text-blue-400',
        message: 'text-zinc-300'
      };
    }
    
    return {
      row: '',
      level: 'text-zinc-500',
      message: 'text-zinc-400'
    };
  };

  return (
    <div 
      className="bg-white/[0.03] backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden flex flex-col h-[500px] transition-all duration-500"
      onMouseEnter={() => setIsAutoScrollPaused(true)}
      onMouseLeave={() => setIsAutoScrollPaused(false)}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-white/5 border-b border-white/10">
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/30 border border-red-500/20" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/30 border border-yellow-500/20" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/30 border border-green-500/20" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-zinc-500 tracking-wider uppercase">Live Process Logs</span>
            {!isAtBottom && isAutoScrollPaused && (
              <span className="text-[9px] px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 font-mono animate-pulse">Scrolling Paused</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
           <span className="text-[10px] font-mono text-zinc-500">
             {wsConnected ? 'Connected: Localhost:8000' : 'Reconnecting...'}
           </span>
           <div className={`w-1.5 h-1.5 rounded-full ${wsConnected ? 'bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]' : 'bg-yellow-500 animate-pulse'}`} />
        </div>
      </div>

      {/* Content */}
      <ScrollArea 
        ref={scrollRef} 
        className="flex-1 p-6"
        onScrollCapture={handleScroll}
      >
        <div className="font-mono text-[13px] leading-relaxed space-y-1">
          {logs.map((log, i) => {
            const styles = getLevelStyles(log.level, log.message);
            return (
              <div key={i} className={`flex gap-4 group transition-colors -mx-6 px-6 ${styles.row} hover:bg-white/[0.04] p-0.5`}>
                <span className="text-zinc-600 shrink-0 font-light text-[11px] pt-0.5">[{log.timestamp}]</span>
                <span className={`${styles.level} font-bold shrink-0 min-w-[70px] uppercase text-[11px] pt-0.5`}>{log.level}:</span>
                <span className={`${styles.message} transition-colors group-hover:text-white`}>{log.message}</span>
              </div>
            );
          })}
          <div className="flex gap-2 items-center text-zinc-400 pt-2 animate-pulse">
            <span className="text-zinc-600">$</span>
            <span className="flex items-center gap-1 font-light italic">
              tail -f /var/logs/instance-alpha.log
              <span className="w-2 h-4 bg-white/30" />
            </span>
          </div>
        </div>
      </ScrollArea>
      
      {/* Footer hint */}
      {!isAtBottom && (
        <button 
          onClick={() => {
            setIsAtBottom(true);
            setIsAutoScrollPaused(false);
          }}
          className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white text-[10px] rounded-full shadow-lg transition-all flex items-center gap-2 border border-blue-400/30 backdrop-blur-md opacity-90"
        >
          <span>Resume Auto-scroll</span>
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </button>
      )}
    </div>
  );
};
