import { create } from 'zustand';

export interface Repository {
  id: number;
  name: string;
  owner: string;
  url: string;
  stars: number;
  is_monitored: number;
  created_at: string;
}

export interface Finding {
  id: number;
  secret_type: string;
  secret_value: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  confidence: number;
  file_path: string;
  line_number: number;
  snippet: string;
  ai_analysis: string;
  disclosure_status: string;
  is_resolved: boolean;
  created_at: string;
  repository: Repository;
}

export interface ScanHistory {
  id: number;
  status: string;
  findings_count: number;
  scan_duration_ms: number;
  created_at: string;
  repository: Repository;
}

export interface Metrics {
  total_leaks: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  resolved_count: number;
  types_distribution: Record<string, number>;
  severity_distribution: Record<string, number>;
  disclosure_distribution: Record<string, number>;
}

interface ScannerState {
  findings: Finding[];
  repositories: Repository[];
  scanHistory: ScanHistory[];
  metrics: Metrics | null;
  wsConnected: boolean;
  token: string | null;
  isLoading: boolean;
  
  init: () => Promise<void>;
  authenticate: () => Promise<string | null>;
  fetchFindings: () => Promise<void>;
  fetchRepositories: () => Promise<void>;
  fetchScanHistory: () => Promise<void>;
  fetchMetrics: () => Promise<void>;
  addRepository: (url: string) => Promise<void>;
  triggerScan: (repoId: number) => Promise<void>;
  resolveFinding: (findingId: number, status: string, resolved: boolean) => Promise<void>;
  connectWebSocket: () => void;
}

let apiEnv = typeof window !== "undefined" && (window as any).__env_api_url 
  ? (window as any).__env_api_url 
  : (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000");

if (apiEnv && !apiEnv.startsWith("http://") && !apiEnv.startsWith("https://")) {
  apiEnv = "https://" + apiEnv;
}

const API_BASE = `${apiEnv.replace(/\/$/, '')}/api/v1`;
const WS_BASE = `${apiEnv.replace(/^http/, 'ws').replace(/\/$/, '')}/ws`;

export const useScannerStore = create<ScannerState>((set, get) => ({
  findings: [],
  repositories: [],
  scanHistory: [],
  metrics: null,
  wsConnected: false,
  token: null,
  isLoading: false,

  authenticate: async () => {
    try {
      const savedToken = localStorage.getItem('repoleak_token');
      if (savedToken) {
        set({ token: savedToken });
        return savedToken;
      }
      
      const formData = new URLSearchParams();
      formData.append('username', 'admin@repoleak.io');
      formData.append('password', 'password123');

      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      });
      
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('repoleak_token', data.access_token);
        set({ token: data.access_token });
        return data.access_token;
      }
      return null;
    } catch (e) {
      console.error("Auth failed:", e);
      return null;
    }
  },

  init: async () => {
    set({ isLoading: true });
    const token = await get().authenticate();
    if (token) {
      await Promise.all([
        get().fetchMetrics(),
        get().fetchFindings(),
        get().fetchRepositories(),
        get().fetchScanHistory()
      ]);
      get().connectWebSocket();
    }
    set({ isLoading: false });
  },

  fetchFindings: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/findings/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ findings: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchRepositories: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/scans/repositories`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ repositories: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchScanHistory: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/scans/history`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ scanHistory: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  fetchMetrics: async () => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/metrics/overview`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        set({ metrics: data });
      }
    } catch (e) {
      console.error(e);
    }
  },

  addRepository: async (url: string) => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/scans/repositories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url, name: "", owner: "" })
      });
      if (res.ok) {
        const newRepo = await res.json();
        set(state => ({ repositories: [newRepo, ...state.repositories] }));
        // Trigger initial scan
        await get().triggerScan(newRepo.id);
      }
    } catch (e) {
      console.error(e);
    }
  },

  triggerScan: async (repoId: number) => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/scans/repositories/${repoId}/scan`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        await get().fetchScanHistory();
      }
    } catch (e) {
      console.error(e);
    }
  },

  resolveFinding: async (findingId: number, status: string, resolved: boolean) => {
    const { token } = get();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/findings/${findingId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ disclosure_status: status, is_resolved: resolved })
      });
      if (res.ok) {
        const updated = await res.json();
        set(state => ({
          findings: state.findings.map(f => f.id === findingId ? updated : f)
        }));
        await get().fetchMetrics();
      }
    } catch (e) {
      console.error(e);
    }
  },

  connectWebSocket: () => {
    const socket = new WebSocket(WS_BASE);
    
    socket.onopen = () => {
      set({ wsConnected: true });
      console.log("WebSocket linked to RepoLeak backend.");
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === "new_finding" && data.finding) {
          const newFinding: Finding = data.finding;
          
          // Prepend new finding to list
          set(state => {
            // Update current metrics locally for dynamic HUD updates
            const currentMetrics = state.metrics;
            let updatedMetrics = null;
            if (currentMetrics) {
              const severityKey = newFinding.severity.toLowerCase() + "_count";
              const sevKeyCount = (currentMetrics as any)[severityKey] || 0;
              
              const updatedTypes = { ...currentMetrics.types_distribution };
              updatedTypes[newFinding.secret_type] = (updatedTypes[newFinding.secret_type] || 0) + 1;
              
              const updatedSev = { ...currentMetrics.severity_distribution };
              updatedSev[newFinding.severity] = (updatedSev[newFinding.severity] || 0) + 1;

              updatedMetrics = {
                ...currentMetrics,
                total_leaks: currentMetrics.total_leaks + 1,
                [severityKey]: sevKeyCount + 1,
                types_distribution: updatedTypes,
                severity_distribution: updatedSev
              };
            }

            return {
              findings: [newFinding, ...state.findings].slice(0, 100), // Cap at 100 on client
              metrics: updatedMetrics || state.metrics
            };
          });
        }
      } catch (err) {
        console.error("WS parse error:", err);
      }
    };

    socket.onclose = () => {
      set({ wsConnected: false });
      console.warn("WS connection lost. Retrying in 5 seconds...");
      setTimeout(() => get().connectWebSocket(), 5000);
    };
  }
}));
