'use client';

import React, { useState } from 'react';
import { useScannerStore, Finding } from '../../store/scannerStore';
import { ShieldAlert, AlertOctagon, Terminal, ExternalLink, ShieldCheck, Cpu } from 'lucide-react';

export default function FindingsPage() {
  const { findings, resolveFinding } = useScannerStore();
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleResolve = async (finding: Finding) => {
    const isResolved = !finding.is_resolved;
    await resolveFinding(finding.id, isResolved ? 'Fixed' : 'Pending', isResolved);
    if (selectedFinding && selectedFinding.id === finding.id) {
      setSelectedFinding(prev => prev ? { ...prev, is_resolved: isResolved, disclosure_status: isResolved ? 'Fixed' : 'Pending' } : null);
    }
  };

  const handleStatusChange = async (findingId: number, status: string) => {
    await resolveFinding(findingId, status, status === 'Fixed' || status === 'Closed');
    if (selectedFinding && selectedFinding.id === findingId) {
      setSelectedFinding(prev => prev ? { ...prev, disclosure_status: status, is_resolved: status === 'Fixed' || status === 'Closed' } : null);
    }
  };

  const filteredFindings = findings.filter(f => {
    const matchesSeverity = severityFilter === 'ALL' || f.severity === severityFilter;
    const matchesStatus = statusFilter === 'ALL' || 
      (statusFilter === 'RESOLVED' && f.is_resolved) || 
      (statusFilter === 'ACTIVE' && !f.is_resolved);
    const matchesSearch = !searchTerm.trim() || 
      f.secret_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.file_path.toLowerCase().includes(searchTerm.toLowerCase()) ||
      f.repository.name.toLowerCase().includes(searchTerm.toLowerCase());
      
    return matchesSeverity && matchesStatus && matchesSearch;
  });

  const getSeverityColor = (sev: string) => {
    switch (sev) {
      case 'CRITICAL': return 'text-cyber-red border-cyber-red bg-red-950/20';
      case 'HIGH': return 'text-cyber-yellow border-cyber-yellow bg-amber-950/20';
      case 'MEDIUM': return 'text-yellow-400 border-yellow-500/30 bg-yellow-950/10';
      default: return 'text-cyber-cyan border-cyber-cyan bg-blue-950/10';
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 h-[calc(100vh-120px)]">
      
      {/* Left panel: Findings list */}
      <div className="lg:col-span-2 border border-cyber-border bg-slate-950/90 rounded p-4 flex flex-col overflow-hidden">
        <div className="space-y-3 mb-4">
          <h2 className="text-sm font-bold tracking-widest text-cyber-cyan border-b border-cyber-border/40 pb-2">
            INTRUSION DETECTION LIST ({filteredFindings.length})
          </h2>
          
          {/* Search */}
          <input
            type="text"
            placeholder="Search payload type, repo, file..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-cyber-border/30 px-3 py-1.5 rounded text-xs text-slate-300 focus:outline-none focus:border-cyber-cyan"
          />
          
          {/* Filters */}
          <div className="flex gap-2">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="flex-1 bg-slate-900 border border-cyber-border/30 px-2 py-1 rounded text-[10px] text-slate-300 focus:outline-none"
            >
              <option value="ALL">Severity: All</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
            
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="flex-1 bg-slate-900 border border-cyber-border/30 px-2 py-1 rounded text-[10px] text-slate-300 focus:outline-none"
            >
              <option value="ALL">Status: All</option>
              <option value="ACTIVE">Active Alerts</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>

        {/* Scrollable list */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {filteredFindings.map((f) => (
            <div
              key={f.id}
              onClick={() => setSelectedFinding(f)}
              className={`p-3 rounded border text-xs cursor-pointer transition-all ${
                selectedFinding?.id === f.id
                  ? 'border-cyber-cyan bg-cyber-cyan/10 shadow-cyber'
                  : 'border-slate-900 bg-slate-950 hover:border-slate-800'
              }`}
            >
              <div className="flex justify-between items-start">
                <span className="font-bold text-slate-200 truncate">{f.secret_type}</span>
                <span className={`text-[9px] px-1.5 border rounded uppercase font-bold ${getSeverityColor(f.severity)}`}>
                  {f.severity}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 truncate mt-1">
                {f.repository.owner}/{f.repository.name}
              </div>
              <div className="text-[9px] text-slate-500 truncate">
                File: {f.file_path}
              </div>
              {f.is_resolved && (
                <div className="text-[9px] text-cyber-green mt-1 flex items-center gap-1 font-bold">
                  <ShieldCheck className="w-3 h-3" /> RESOLVED
                </div>
              )}
            </div>
          ))}
          {filteredFindings.length === 0 && (
            <div className="text-center text-xs text-slate-500 py-12">
              NO DETECTIONS FOUND MATCHING FILTERS.
            </div>
          )}
        </div>
      </div>

      {/* Right panel: Details & Inspection panel */}
      <div className="lg:col-span-3 border border-cyber-border bg-slate-950/90 rounded p-6 flex flex-col overflow-y-auto">
        {selectedFinding ? (
          <div className="space-y-6">
            
            {/* Header info */}
            <div className="flex justify-between items-start border-b border-cyber-border/40 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-cyber-red animate-pulse" />
                  <h2 className="text-lg font-bold text-slate-200">{selectedFinding.secret_type}</h2>
                </div>
                <div className="text-xs text-slate-400">
                  Target Asset: <a href={selectedFinding.repository.url} target="_blank" className="text-cyber-cyan hover:underline inline-flex items-center gap-1">
                    {selectedFinding.repository.owner}/{selectedFinding.repository.name} <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <button
                  onClick={() => handleResolve(selectedFinding)}
                  className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                    selectedFinding.is_resolved
                      ? 'bg-cyber-green text-slate-950 hover:bg-emerald-400'
                      : 'border border-cyber-cyan text-cyber-cyan hover:bg-cyber-cyan/10'
                  }`}
                >
                  {selectedFinding.is_resolved ? 'REOPEN ALERT' : 'RESOLVE FINDING'}
                </button>
              </div>
            </div>

            {/* Quick Metadata Metadata */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-900/50 p-4 border border-slate-900 rounded">
              <div>
                <span className="text-[9px] text-slate-500 uppercase block">Severity Score</span>
                <span className={`text-xs font-bold ${
                  selectedFinding.severity === 'CRITICAL' ? 'text-cyber-red' : 'text-cyber-yellow'
                }`}>{selectedFinding.severity}</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-500 uppercase block">Confidence Score</span>
                <span className="text-xs font-bold text-slate-300">{(selectedFinding.confidence * 100).toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-500 uppercase block">Disclosure workflow</span>
                <select
                  value={selectedFinding.disclosure_status}
                  onChange={(e) => handleStatusChange(selectedFinding.id, e.target.value)}
                  className="bg-transparent text-xs font-bold text-cyber-cyan border-none p-0 focus:outline-none cursor-pointer"
                >
                  <option value="Pending">Pending</option>
                  <option value="Contacted">Contacted</option>
                  <option value="Acknowledged">Acknowledged</option>
                  <option value="Fixed">Fixed</option>
                  <option value="Closed">Closed</option>
                </select>
              </div>
              <div>
                <span className="text-[9px] text-slate-500 uppercase block">Detected At</span>
                <span className="text-xs font-bold text-slate-300">{new Date(selectedFinding.created_at).toLocaleDateString()}</span>
              </div>
            </div>

            {/* Code snippet viewer */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <AlertOctagon className="w-4 h-4 text-cyber-red" />
                Raw Payload Snippet (Masked)
              </h3>
              <div className="border border-slate-900 rounded overflow-hidden">
                <div className="bg-slate-950 px-4 py-2 text-[10px] text-slate-500 border-b border-slate-900 flex justify-between">
                  <span>File: {selectedFinding.file_path}</span>
                  <span>Line: {selectedFinding.line_number}</span>
                </div>
                <pre className="p-4 bg-slate-950/80 overflow-x-auto font-mono text-xs text-slate-300 leading-relaxed">
                  <code>
                    {selectedFinding.snippet}
                  </code>
                </pre>
              </div>
            </div>

            {/* AI Assessment Report */}
            <div className="space-y-2 border-l-2 border-cyber-purple bg-cyber-purple/5 p-4 rounded-r">
              <h3 className="text-xs font-bold text-cyber-purple uppercase tracking-wider flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-cyber-purple" />
                AI Threat Assessment & Remediation
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                {selectedFinding.ai_analysis}
              </p>
            </div>

            {/* Simulated Action Flow Template */}
            <div className="space-y-2">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <Terminal className="w-4 h-4 text-cyber-cyan" />
                Disclosure Template Generator
              </h3>
              <div className="bg-slate-900/60 p-4 border border-slate-900 rounded space-y-3">
                <p className="text-[10px] text-slate-400">
                  Auto-generated incident notification message for repository owners.
                </p>
                <div className="bg-slate-950 p-3 border border-slate-900 rounded font-mono text-[10px] text-slate-400 select-all leading-normal whitespace-pre-wrap">
{`Subject: Action Required: Exposed ${selectedFinding.secret_type} in ${selectedFinding.repository.name}

Hello,

RepoLeak Watcher X detected a security incident. A credentials token of type ${selectedFinding.secret_type} is exposed in line ${selectedFinding.line_number} of file ${selectedFinding.file_path}.

Leaked Secret Signature: ${selectedFinding.secret_value}

Action Items:
1. Deactivate/Revoke this API Key immediately.
2. Force-push git revisions to erase history, or use git-filter-repo.
3. Review audit logs for credential abuse.

Best,
SecOps Security Team`}
                </div>
              </div>
            </div>

          </div>
        ) : (
          <div className="flex-1 flex flex-col justify-center items-center text-slate-500 py-24 space-y-3">
            <ShieldAlert className="w-12 h-12 text-slate-700" />
            <span className="text-xs uppercase tracking-widest font-bold">Select finding from left panel to audit payload</span>
          </div>
        )}
      </div>

    </div>
  );
}
