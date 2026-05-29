'use client';

import React, { useEffect } from 'react';
import { useScannerStore } from '../store/scannerStore';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, Radio, BarChart3, Settings as SettingsIcon, Terminal, Activity } from 'lucide-react';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { init, wsConnected, metrics } = useScannerStore();
  const pathname = usePathname();

  useEffect(() => {
    init();
  }, [init]);

  const navItems = [
    { name: 'OVERVIEW HUD', path: '/', icon: Shield },
    { name: 'LIVE FINDINGS', path: '/findings', icon: Radio },
    { name: 'SOC ANALYTICS', path: '/analytics', icon: BarChart3 },
    { name: 'SETTINGS & SOURCE', path: '/settings', icon: SettingsIcon },
  ];

  return (
    <html lang="en">
      <body className="bg-cyber-bg text-slate-100 min-h-screen flex flex-col cyber-grid-overlay font-mono">
        {/* Top Header Status HUD */}
        <header className="border-b border-cyber-border bg-slate-950/80 backdrop-blur-md px-6 py-3 flex justify-between items-center z-20">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-cyber-cyan animate-pulse shadow-cyberGlow"></div>
            <span className="text-xl font-bold tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyber-cyan to-indigo-400">
              REPOLEAK WATCHER X
            </span>
            <span className="text-xs border border-cyber-cyan/30 text-cyber-cyan px-2 py-0.5 rounded uppercase font-bold tracking-tighter">
              v1.0.0 Enterprise
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-400">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyber-green" />
              <span>SYSTEM: <span className="text-cyber-green font-bold">ONLINE</span></span>
            </div>
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-cyber-purple" />
              <span>WS STATUS: 
                <span className={`font-bold ml-1 ${wsConnected ? 'text-cyber-green' : 'text-cyber-red animate-pulse'}`}>
                  {wsConnected ? 'CONNECTED' : 'DISCONNECTED'}
                </span>
              </span>
            </div>
            <div className="bg-cyber-panel/50 border border-cyber-border px-3 py-1.5 rounded flex items-center gap-4">
              <div>CRITICAL: <span className="text-cyber-red font-bold">{metrics?.critical_count || 0}</span></div>
              <div className="w-px h-3 bg-slate-800"></div>
              <div>HIGH: <span className="text-cyber-yellow font-bold">{metrics?.high_count || 0}</span></div>
            </div>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden z-10">
          {/* Cyber Sidebar Nav */}
          <aside className="w-64 border-r border-cyber-border bg-slate-950/40 backdrop-blur-md p-4 flex flex-col justify-between">
            <div className="space-y-6">
              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider pl-3">
                Operations Menu
              </div>
              <nav className="space-y-1">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const active = pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      href={item.path}
                      className={`flex items-center gap-3 px-3 py-3 rounded text-sm transition-all duration-300 font-bold relative ${
                        active
                          ? 'bg-gradient-to-r from-cyber-cyan/15 to-transparent text-cyber-cyan border-l-2 border-cyber-cyan'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/30'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${active ? 'text-cyber-cyan' : 'text-slate-500'}`} />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Footer Brand info */}
            <div className="border-t border-cyber-border/50 pt-4 text-[10px] text-slate-500 space-y-1 pl-3">
              <div>BLUE TEAM TELEMETRY</div>
              <div>SECURE DISCLOSURE ENG</div>
              <div className="text-cyber-cyan/50 font-bold">@2026 REPOLEAK LABS</div>
            </div>
          </aside>

          {/* Page content scroll chassis */}
          <main className="flex-1 overflow-y-auto p-8 bg-cyber-bg/50">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
