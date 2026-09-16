import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  PieChart,
  Pie
} from 'recharts';
import { 
  BarChart3, 
  ShieldCheck, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle,
  TrendingUp,
  Percent
} from 'lucide-react';
import { verificationApi } from '../services/api';

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStats = async () => {
    setLoading(true);
    const res = await verificationApi.getStats();
    setLoading(false);
    if (res.data) setStats(res.data);
  };

  useEffect(() => {
    loadStats();
  }, []);

  const chartData = [
    { name: 'Valid', count: stats?.valid_count || 0, color: '#166534' },
    { name: 'Risky', count: stats?.risky_count || 0, color: '#D97706' },
    { name: 'Invalid', count: stats?.invalid_count || 0, color: '#DC2626' },
    { name: 'Unknown', count: stats?.unknown_count || 0, color: '#64748B' },
  ];

  const total = stats?.total_verified || 0;
  const validPct = total > 0 ? ((stats.valid_count / total) * 100).toFixed(1) : 0;
  const riskyPct = total > 0 ? ((stats.risky_count / total) * 100).toFixed(1) : 0;
  const invalidPct = total > 0 ? ((stats.invalid_count / total) * 100).toFixed(1) : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Verification Analytics & Intelligence</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Aggregated metrics derived from live verification pipeline logs.
          </p>
        </div>

        <button
          onClick={loadStats}
          className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Metrics
        </button>
      </div>

      {total === 0 ? (
        <div className="saas-card p-12 text-center text-slate-500">
          <BarChart3 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm font-medium text-navy-900">No verification data available yet</p>
          <p className="text-xs text-slate-500 mt-0.5">Verify email addresses in the dashboard to generate deliverability metrics.</p>
        </div>
      ) : (
        <>
          {/* Key Deliverability Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="saas-card p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Total Inspected</span>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-navy-900">{total}</span>
                <span className="text-xs text-slate-500">addresses</span>
              </div>
            </div>

            <div className="saas-card p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Deliverable (Valid)</span>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-emerald-700">{stats.valid_count}</span>
                <span className="text-xs font-semibold text-emerald-700">{validPct}%</span>
              </div>
            </div>

            <div className="saas-card p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Risk Factors</span>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-amber-700">{stats.risky_count}</span>
                <span className="text-xs font-semibold text-amber-700">{riskyPct}%</span>
              </div>
            </div>

            <div className="saas-card p-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Average Score</span>
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-2xl font-bold text-navy-900">{stats.average_score}</span>
                <span className="text-xs text-slate-400">/ 100</span>
              </div>
            </div>
          </div>

          {/* Primary Chart: Status Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 saas-card p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div>
                  <h3 className="text-sm font-bold text-navy-900">Verification Status Distribution</h3>
                  <p className="text-xs text-slate-500">Breakdown of verified emails by classification</p>
                </div>
              </div>

              <div className="h-64 w-full pt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                    <XAxis 
                      dataKey="name" 
                      tick={{ fill: '#475569', fontSize: 12 }} 
                      axisLine={{ stroke: '#E2E8F0' }}
                      tickLine={false}
                    />
                    <YAxis 
                      tick={{ fill: '#475569', fontSize: 12 }} 
                      axisLine={{ stroke: '#E2E8F0' }}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#0F172A', 
                        borderColor: '#1E293B', 
                        borderRadius: '6px',
                        color: '#FFFFFF',
                        fontSize: '12px'
                      }}
                      cursor={{ fill: '#F1F5F9' }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Quality Summary card */}
            <div className="saas-card p-6 space-y-4 flex flex-col justify-between">
              <div>
                <h3 className="text-sm font-bold text-navy-900 pb-3 border-b border-slate-200">
                  Verification Quality Breakdown
                </h3>
                <div className="space-y-4 pt-4 text-xs">
                  <div>
                    <div className="flex justify-between font-semibold text-slate-700 mb-1">
                      <span>Valid & Resolvable</span>
                      <span>{validPct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-emerald-600 h-full" style={{ width: `${validPct}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between font-semibold text-slate-700 mb-1">
                      <span>Risky (Disposable / Role)</span>
                      <span>{riskyPct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-amber-600 h-full" style={{ width: `${riskyPct}%` }} />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between font-semibold text-slate-700 mb-1">
                      <span>Invalid / Unreachable</span>
                      <span>{invalidPct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div className="bg-red-600 h-full" style={{ width: `${invalidPct}%` }} />
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-600">
                <span className="font-semibold text-navy-900">Health Indicator:</span> High proportion of Valid addresses improves sender reputation and email domain deliverability.
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
