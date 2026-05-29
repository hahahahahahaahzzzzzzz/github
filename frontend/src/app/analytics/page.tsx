'use client';

import React from 'react';
import { useScannerStore } from '../../store/scannerStore';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { ShieldCheck, BarChart3, TrendingUp, AlertTriangle } from 'lucide-react';

export default function AnalyticsPage() {
  const { metrics, findings } = useScannerStore();

  if (!metrics) {
    return (
      <div className="flex justify-center items-center h-[350px] text-slate-500 text-xs">
        RETRIEVING THREAT TELEMETRY DATA...
      </div>
    );
  }

  // Formatting chart data for Secret Types Distribution
  const typeData = Object.entries(metrics.types_distribution).map(([name, value]) => ({
    name,
    count: value,
  })).sort((a, b) => b.count - a.count);

  // Formatting chart data for Severity Distribution
  const severityData = Object.entries(metrics.severity_distribution).map(([name, value]) => ({
    name,
    value,
  }));

  const COLORS = ['#ff2a5f', '#ffbe3b', '#3b82f6', '#00f3ff', '#9d4edd'];

  // Formatting simulated historical leak rate over time
  // Generate some realistic dates
  const timelineData = [
    { date: '05-24', leaks: Math.max(0, metrics.total_leaks - 12) },
    { date: '05-25', leaks: Math.max(0, metrics.total_leaks - 9) },
    { date: '05-26', leaks: Math.max(0, metrics.total_leaks - 6) },
    { date: '05-27', leaks: Math.max(0, metrics.total_leaks - 3) },
    { date: '05-28', leaks: metrics.total_leaks },
  ];

  return (
    <div className="space-y-6">
      
      {/* HUD Info Header */}
      <div>
        <h1 className="text-xl font-bold tracking-widest text-cyber-cyan text-cyber-glow flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyber-cyan" />
          SOC INTELLIGENCE & TELEMETRY ANALYTICS
        </h1>
        <p className="text-xs text-slate-400 mt-1">
          Historical breach logs, vulnerability statistics, and remediation efficacy
        </p>
      </div>

      {/* Aggregate Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-950/70 border border-slate-900 p-4 rounded flex items-center gap-4">
          <div className="p-3 bg-cyber-cyan/10 text-cyber-cyan rounded">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-bold">Risk Exposure Factor</span>
            <span className="text-xl font-extrabold text-slate-200">
              {metrics.total_leaks > 15 ? 'CRITICAL HIGH' : metrics.total_leaks > 5 ? 'ELEVATED' : 'STABLE'}
            </span>
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-900 p-4 rounded flex items-center gap-4">
          <div className="p-3 bg-cyber-green/10 text-cyber-green rounded">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-bold">Remediation SLA</span>
            <span className="text-xl font-extrabold text-slate-200">
              {metrics.total_leaks > 0 
                ? `${((metrics.resolved_count / metrics.total_leaks) * 100).toFixed(1)}%` 
                : '100%'}
            </span>
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-900 p-4 rounded flex items-center gap-4">
          <div className="p-3 bg-cyber-red/10 text-cyber-red rounded">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 uppercase block font-bold">Unresolved Incidents</span>
            <span className="text-xl font-extrabold text-slate-200">
              {metrics.total_leaks - metrics.resolved_count}
            </span>
          </div>
        </div>
      </div>

      {/* Main Graph Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Graph 1: Leaked types distribution */}
        <div className="border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2">
            Breach Signatures by Secret Type
          </h3>
          <div className="h-[280px] text-xs">
            {typeData.length === 0 ? (
              <div className="flex justify-center items-center h-full text-slate-600">No threat metrics logged yet</div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={typeData} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.03)" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="name" type="category" stroke="#94a3b8" width={110} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0a0c14', borderColor: 'rgba(0, 243, 255, 0.3)', color: '#fff' }}
                  />
                  <Bar dataKey="count" fill="#00f3ff" radius={[0, 4, 4, 0]}>
                    {typeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Graph 2: Severity Distribution */}
        <div className="border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2">
            Threat Severity Ratios
          </h3>
          <div className="h-[280px] flex items-center justify-center">
            {severityData.length === 0 ? (
              <div className="text-slate-600 text-xs">No metrics data</div>
            ) : (
              <div className="w-full h-full flex flex-col md:flex-row items-center gap-4">
                <div className="flex-1 h-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={severityData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {severityData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ backgroundColor: '#0a0c14', borderColor: 'rgba(0, 243, 255, 0.3)', color: '#fff' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="text-xs space-y-2 pr-6">
                  {severityData.map((entry, index) => (
                    <div key={entry.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></div>
                      <span className="font-bold text-slate-300">{entry.name}:</span>
                      <span className="text-slate-400">{entry.value} findings</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Graph 3: Historical Timeline */}
        <div className="lg:col-span-2 border border-cyber-border bg-slate-950/80 p-5 rounded space-y-4">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest border-b border-slate-900 pb-2">
            Threat Detections History (Last 5 Days)
          </h3>
          <div className="h-[260px] text-xs">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={timelineData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.03)" />
                <XAxis dataKey="date" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0a0c14', borderColor: 'rgba(0, 243, 255, 0.3)', color: '#fff' }}
                />
                <Legend />
                <Line type="monotone" dataKey="leaks" stroke="#ff2a5f" strokeWidth={3} name="Total Secrets Exposed" activeDot={{ r: 8 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
}
