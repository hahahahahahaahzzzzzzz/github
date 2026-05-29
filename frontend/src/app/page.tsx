'use client';

import React, { useState } from 'react';
import { useScannerStore } from '../store/scannerStore';
import { AlertTriangle, Plus, Search, Eye, RefreshCw, GitBranch, ShieldCheck } from 'lucide-react';
import Link from 'next/link';

export default function OverviewDashboard() {
  const { metrics, findings, repositories, addRepository, triggerScan, isLoading } = useScannerStore();
  const [repoUrl, setRepoUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setIsSubmitting(true);
    await addRepository(repoUrl);
    setRepoUrl('');
    setIsSubmitting(false);
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return 'border-red-500/30 bg-red-950/20 text-red-400 shadow-cyberRed';
      case 'HIGH':
        return 'border-amber-500/30 bg-amber-950/20 text-amber-400';
      case 'MEDIUM':
        return 'border-yellow-500/20 bg-yellow-950/10 text-yellow-300';
      default:
        return 'border-blue-500/20 bg-blue-950/10 text-blue-400';
    }
  };

  return (
    <div className="space-y-8 animate-cyber-glow rounded p-[1px] bg-cyber-border">
      <div className="p-6 bg-slate-950/90 rounded border border-cyber-border space-y-6">
        
        {/* Header HUD Banner */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold tracking-widest text-cyber-cyan text-cyber-glow">
              CYBER OPERATIONS HUD
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Active defensive monitoring and live GitHub scanning telemetry
            </p>
          </div>
          <div className="flex gap-2">
            <span className="text-[10px] bg-cyber-cyan/10 border border-cyber-cyan/30 text-cyber-cyan px-3 py-1 rounded font-bold">
              SCANNING POOL STATUS: ACTIVE
            </span>
          </div>
        </div>

        {/* Dynamic Metric Display Panels */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className={`border p-4 rounded flex flex-col justify-between h-28 transition-all duration-300 ${getSeverityStyle('CRITICAL')}`}>
            <span className="text-[10px] font-bold tracking-widest uppercase">CRITICAL LEAKS</span>
            <div className="flex justify-between items-end">
              <span className="text-4xl font-extrabold">{metrics?.critical_count || 0}</span>
              <AlertTriangle className="w-6 h-6 animate-pulse text-cyber-red" />
            </div>
          </div>
          
          <div className={`border p-4 rounded flex flex-col justify-between h-28 transition-all duration-300 ${getSeverityStyle('HIGH')}`}>
            <span className="text-[10px] font-bold tracking-widest uppercase">HIGH RISK</span>
            <div className="flex justify-between items-end">
              <span className="text-4xl font-extrabold">{metrics?.high_count || 0}</span>
              <AlertTriangle className="w-6 h-6 text-cyber-yellow" />
            </div>
          </div>

          <div className={`border p-4 rounded flex flex-col justify-between h-28 transition-all duration-300 ${getSeverityStyle('MEDIUM')}`}>
            <span className="text-[10px] font-bold tracking-widest uppercase">MEDIUM THREATS</span>
            <div className="flex justify-between items-end">
              <span className="text-4xl font-extrabold">{metrics?.medium_count || 0}</span>
              <ShieldCheck className="w-6 h-6 text-yellow-500" />
            </div>
          </div>

          <div className="border border-cyber-cyan/20 bg-cyber-cyan/5 p-4 rounded flex flex-col justify-between h-28 text-cyber-cyan shadow-cyber">
            <span className="text-[10px] font-bold tracking-widest uppercase">MONITORED REPOS</span>
            <div className="flex justify-between items-end">
              <span className="text-4xl font-extrabold">{repositories.length}</span>
              <GitBranch className="w-6 h-6 text-cyber-cyan" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Col 1 & 2: Live findings feed stream */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex justify-between items-center border-b border-cyber-border/50 pb-2">
              <h2 className="text-xs font-bold uppercase text-slate-400 tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyber-cyan animate-ping"></span>
                Real-Time Secrets Alert Queue
              </h2>
              <Link href="/findings" className="text-[10px] text-cyber-cyan hover:underline uppercase font-bold">
                View All Findings &rarr;
              </Link>
            </div>
            
            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-2">
              {findings.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs border border-dashed border-slate-800 rounded">
                  NO ACTIVE SECRET LEAKS DETECTED. SYSTEM COMPLIANT.
                </div>
              ) : (
                findings.slice(0, 5).map((f) => (
                  <div key={f.id} className="border border-slate-900 bg-slate-950/60 p-4 rounded flex items-center justify-between gap-4 hover:border-cyber-cyan/30 transition-all duration-300">
                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          f.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-900/50' :
                          f.severity === 'HIGH' ? 'bg-amber-950 text-amber-400 border border-amber-900/50' :
                          'bg-yellow-950/50 text-yellow-400 border border-yellow-900/30'
                        }`}>
                          {f.severity}
                        </span>
                        <span className="text-xs font-bold text-slate-300 truncate">
                          {f.secret_type}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 truncate">
                        File: <code className="text-cyber-cyan">{f.file_path}</code> in <b>{f.repository.owner}/{f.repository.name}</b>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 flex-shrink-0">
                      <div className="text-right text-[10px] text-slate-500">
                        {new Date(f.created_at).toLocaleTimeString()}
                      </div>
                      <Link href="/findings" className="p-1.5 border border-cyber-cyan/20 hover:border-cyber-cyan rounded bg-slate-900/80 transition-all">
                        <Eye className="w-3.5 h-3.5 text-cyber-cyan" />
                      </Link>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Col 3: Monitored Repos & Register form */}
          <div className="space-y-6">
            {/* Register Repository Form */}
            <div className="border border-cyber-cyan/20 bg-slate-950/60 p-4 rounded space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-cyber-border/30 pb-2 flex items-center gap-2">
                <Plus className="w-4 h-4 text-cyber-cyan" /> Add Target Repo
              </h2>
              <form onSubmit={handleRegister} className="space-y-3">
                <div>
                  <label className="text-[10px] text-slate-500 uppercase block mb-1">GitHub Repo URL</label>
                  <input
                    type="url"
                    placeholder="https://github.com/owner/repo"
                    value={repoUrl}
                    onChange={(e) => setRepoUrl(e.target.value)}
                    required
                    className="w-full bg-slate-900/80 border border-cyber-cyan/20 px-3 py-2 rounded text-xs focus:outline-none focus:border-cyber-cyan text-slate-200"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-bold py-2 rounded text-xs transition-all flex items-center justify-center gap-1"
                >
                  <Search className="w-3.5 h-3.5" />
                  {isSubmitting ? "SYNCING..." : "REGISTER & SCAN"}
                </button>
              </form>
            </div>

            {/* Monitored Repos list */}
            <div className="border border-slate-900 bg-slate-950/60 p-4 rounded space-y-4">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-300 border-b border-cyber-border/30 pb-2">
                Monitored Assets ({repositories.length})
              </h2>
              <div className="space-y-3 max-h-[220px] overflow-y-auto pr-1">
                {repositories.map((repo) => (
                  <div key={repo.id} className="text-xs flex items-center justify-between gap-2 p-2 border border-slate-900 rounded bg-slate-950">
                    <div className="min-w-0">
                      <div className="font-bold text-slate-300 truncate">{repo.owner}/{repo.name}</div>
                      <div className="text-[9px] text-slate-500 truncate">★ {repo.stars} stars</div>
                    </div>
                    <button 
                      onClick={() => triggerScan(repo.id)}
                      className="p-1 border border-cyber-cyan/10 hover:border-cyber-cyan/50 text-cyber-cyan rounded bg-slate-900 transition-all flex-shrink-0"
                    >
                      <RefreshCw className="w-3 h-3" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
