'use client';

import React, { useState } from 'react';
import { useScannerStore } from '../../store/scannerStore';
import { Settings as SettingsIcon, ShieldCheck, Key, Bell, HelpCircle, History, RefreshCw } from 'lucide-react';

export default function SettingsPage() {
  const { repositories, scanHistory, triggerScan } = useScannerStore();
  
  // Local state for fake integrations configuration saving
  const [gitToken, setGitToken] = useState('****************************************');
  const [teleBotToken, setTeleBotToken] = useState('****************************************');
  const [teleChatId, setTeleChatId] = useState('-100123456789');
  const [saveStatus, setSaveStatus] = useState('');

  const handleSaveConfig = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('INTEGRATIONS UPDATED SUCCESSFULLY.');
    setTimeout(() => setSaveStatus(''), 4000);
  };

  return (
    <div className="space-y-8">
      
      {/* HUD Info Header */}
      <div>
        <h1 className="text-xl font-bold tracking-widest text-cyber-cyan text-cyber-glow flex items-center gap-2">
          <SettingsIcon className="w-5 h-5" />
          SYSTEM INTEGRATIONS & SETTINGS
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Configure API credentials, webhook endpoints, scanning parameters, and review scan histories
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side: Integrations config forms */}
        <div className="lg:col-span-1 space-y-6">
          
          {/* Secrets Config Form */}
          <div className="border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2 flex items-center gap-2">
              <Key className="w-4 h-4 text-cyber-cyan" />
              API Credentials & Tokens
            </h3>
            
            <form onSubmit={handleSaveConfig} className="space-y-4 text-xs">
              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-500 uppercase block font-bold">GitHub OAuth Tokens (Rotated)</label>
                <input
                  type="password"
                  value={gitToken}
                  onChange={(e) => setGitToken(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded focus:outline-none focus:border-cyber-cyan text-slate-300"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-500 uppercase block font-bold">Telegram Bot Token</label>
                <input
                  type="password"
                  value={teleBotToken}
                  onChange={(e) => setTeleBotToken(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded focus:outline-none focus:border-cyber-cyan text-slate-300"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-[10px] text-slate-500 uppercase block font-bold">Telegram Target Chat/Channel ID</label>
                <input
                  type="text"
                  value={teleChatId}
                  onChange={(e) => setTeleChatId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 px-3 py-2 rounded focus:outline-none focus:border-cyber-cyan text-slate-300 font-mono"
                />
              </div>

              {saveStatus && (
                <div className="text-[10px] text-cyber-green bg-emerald-950/20 border border-emerald-900/50 p-2.5 rounded font-bold">
                  {saveStatus}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-cyber-cyan hover:bg-cyan-400 text-slate-950 font-bold py-2 rounded transition-all text-xs"
              >
                SAVE INTEGRATIONS
              </button>
            </form>
          </div>

          {/* Webhooks integrations info */}
          <div className="border border-slate-900 bg-slate-950/40 p-4 rounded text-xs space-y-3">
            <h3 className="font-bold text-slate-300 flex items-center gap-1.5">
              <Bell className="w-4 h-4 text-cyber-purple" /> Webhook Alert Endpoints
            </h3>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              Register Webhook urls to push JSON alert structures instantly to internal systems (e.g. Slack, Splunk, Datadog) upon detecting secrets.
            </p>
            <div className="border border-dashed border-slate-800 p-3 text-center text-slate-600 rounded">
              WEBHOOK ENGINE STANDBY
            </div>
          </div>

        </div>

        {/* Right Side: Scan History and asset telemetry logs */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Target assets list */}
          <div className="border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2">
              Registered Target Repositories ({repositories.length})
            </h3>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead>
                  <tr className="border-b border-slate-900 text-slate-500 text-[10px] uppercase font-bold">
                    <th className="pb-2">Repository</th>
                    <th className="pb-2">Stars</th>
                    <th className="pb-2">URL</th>
                    <th className="pb-2 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900">
                  {repositories.map((repo) => (
                    <tr key={repo.id} className="hover:bg-slate-900/10">
                      <td className="py-2.5 font-bold">{repo.owner}/{repo.name}</td>
                      <td className="py-2.5">★ {repo.stars}</td>
                      <td className="py-2.5 text-cyber-cyan truncate max-w-xs">{repo.url}</td>
                      <td className="py-2.5 text-right">
                        <button
                          onClick={() => triggerScan(repo.id)}
                          className="px-2.5 py-1 border border-cyber-cyan/20 hover:border-cyber-cyan text-cyber-cyan rounded bg-slate-900/60 transition-all font-bold text-[10px] inline-flex items-center gap-1"
                        >
                          <RefreshCw className="w-3 h-3" /> SCAN
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Audit Scan History logs */}
          <div className="border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2 flex items-center gap-2">
              <History className="w-4 h-4 text-cyber-purple" />
              Operations Scan Logs
            </h3>
            
            <div className="overflow-x-auto max-h-[280px] overflow-y-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead>
                  <tr className="border-b border-slate-900 text-slate-500 text-[10px] uppercase font-bold">
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Repository</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2">Leaks Found</th>
                    <th className="pb-2 text-right">Duration</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-900 text-[11px]">
                  {scanHistory.map((history) => (
                    <tr key={history.id} className="hover:bg-slate-900/10">
                      <td className="py-2.5 text-slate-500">{new Date(history.created_at).toLocaleTimeString()}</td>
                      <td className="py-2.5 font-bold">{history.repository.owner}/{history.repository.name}</td>
                      <td className="py-2.5">
                        <span className={`px-1.5 py-0.5 rounded font-bold uppercase text-[9px] ${
                          history.status === 'completed' 
                            ? 'bg-emerald-950 text-cyber-green border border-emerald-900/50' 
                            : 'bg-red-950 text-cyber-red border border-red-900/50'
                        }`}>
                          {history.status}
                        </span>
                      </td>
                      <td className={`py-2.5 font-bold ${history.findings_count > 0 ? 'text-cyber-red' : 'text-slate-500'}`}>
                        {history.findings_count}
                      </td>
                      <td className="py-2.5 text-right text-slate-400">{history.scan_duration_ms} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
