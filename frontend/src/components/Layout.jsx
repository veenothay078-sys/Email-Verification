import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Layers, 
  Search, 
  History, 
  BarChart3, 
  ShieldCheck, 
  ExternalLink,
  Menu,
  X,
  Server,
  Zap,
  ChevronRight
} from 'lucide-react';
import { verificationApi } from '../services/api';

export default function Layout({ currentTab, onTabChange, children }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    verificationApi.checkHealth().then(res => {
      if (res.data && res.data.status === 'ok') {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    });
  }, []);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: Layers, desc: 'Dashboard & System Health' },
    { id: 'verify', label: 'Single Verify', icon: Search, desc: 'Inspect individual email' },
    { id: 'batch', label: 'Batch Audit', icon: ShieldCheck, desc: 'PDF / Word bulk upload' },
    { id: 'history', label: 'History', icon: History, desc: 'Verification audit logs' },
    { id: 'analytics', label: 'Analytics', icon: BarChart3, desc: 'Performance & signals' },
  ];

  return (
    <div className="min-h-screen bg-slate-50/50 text-navy-800 flex flex-col md:flex-row">
      
      {/* MOBILE TOP BAR (Shown on small screens only) */}
      <div className="md:hidden bg-navy-900 text-white px-4 py-3 border-b border-navy-800 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => onTabChange('overview')}>
          <div className="w-7 h-7 rounded bg-emerald-500 flex items-center justify-center text-navy-950 font-bold">
            <ShieldCheck className="w-4 h-4 text-navy-950" />
          </div>
          <div>
            <span className="font-bold text-sm tracking-tight text-white block">OpenMail Verify</span>
            <span className="text-[10px] text-slate-400">Email Validation Engine</span>
          </div>
        </div>

        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 text-slate-300 hover:text-white rounded-md bg-navy-800"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* LEFT SIDEBAR NAVIGATION (Desktop & Expanded Mobile) */}
      <aside 
        className={`w-full md:w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 sticky top-0 md:h-screen z-40 transition-all ${
          mobileMenuOpen ? 'block' : 'hidden md:flex'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Brand & Logo Header */}
          <div className="p-5 border-b border-slate-100 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-navy-900 flex items-center justify-center text-white shadow-sm shrink-0">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-navy-900 tracking-tight text-sm">OpenMail Verify</span>
                <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 rounded bg-navy-50 text-navy-700 border border-navy-100">v1.0</span>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">Deliverability Engine</p>
            </div>
          </div>

          {/* Navigation Items (Vertical List) */}
          <nav className="p-3 space-y-1 flex-1 overflow-y-auto">
            <div className="px-3 py-2 text-[10px] uppercase font-bold tracking-wider text-slate-400">
              NAVIGATION
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onTabChange(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2.5 text-xs font-semibold rounded-lg transition-all group ${
                    isActive
                      ? 'bg-navy-900 text-white shadow-sm font-bold'
                      : 'text-slate-600 hover:text-navy-900 hover:bg-slate-100/80'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-emerald-400' : 'text-slate-400 group-hover:text-navy-900'}`} />
                    <span>{item.label}</span>
                  </div>
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-emerald-400" />}
                </button>
              );
            })}
          </nav>

          {/* Footer & API Status in Sidebar */}
          <div className="p-4 border-t border-slate-100 bg-slate-50/60 space-y-3">
            <div className="p-2.5 rounded-lg bg-white border border-slate-200 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                <span className="text-slate-700 font-bold text-[11px]">
                  {apiStatus === 'online' ? 'API Online' : 'Connecting...'}
                </span>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">127.0.0.1</span>
            </div>

            <div className="text-[10px] text-slate-500 space-y-0.5 px-1">
              <div className="font-semibold text-navy-900">RFC 5321 Non-Contact Engine</div>
              <div>DNS/MX • SMTP Probing • No OTP</div>
            </div>
          </div>
        </div>
      </aside>

      {/* RIGHT MAIN CONTENT VIEWPORT */}
      <div className="flex-1 min-w-0 flex flex-col min-h-screen">
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Clean Footer */}
        <footer className="border-t border-slate-200 py-4 bg-white text-xs text-slate-500 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div>
              <span className="font-bold text-navy-900">OpenMail Verify</span> — Open-source email verification & deliverability intelligence engine.
            </div>
            <div className="flex items-center gap-3 text-slate-500 text-[11px]">
              <span>RFC 5321 Compliant</span>
              <span>•</span>
              <span>Real DNS/MX Inspection</span>
              <span>•</span>
              <span>MIT License</span>
            </div>
          </div>
        </footer>
      </div>

    </div>
  );
}
