import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Layers, 
  Search, 
  History, 
  BarChart3, 
  Code2, 
  ShieldCheck, 
  ExternalLink,
  Menu,
  X
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
    { id: 'overview', label: 'Overview', icon: Layers },
    { id: 'verify', label: 'Single Verify', icon: Search },
    { id: 'batch', label: 'Batch Audit', icon: ShieldCheck },
    { id: 'history', label: 'History', icon: History },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'api', label: 'API Reference', icon: Code2 },
  ];

  return (
    <div className="min-h-screen bg-white text-navy-800 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Brand */}
            <div className="flex items-center gap-6">
              <div 
                className="flex items-center gap-2.5 cursor-pointer select-none"
                onClick={() => onTabChange('overview')}
              >
                <div className="w-8 h-8 rounded bg-navy-800 flex items-center justify-center text-white">
                  <ShieldCheck className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-navy-900 tracking-tight text-base">OpenMail Verify</span>
                    <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">v1.0</span>
                  </div>
                  <p className="text-[11px] text-slate-500 hidden sm:block">Email Validation & Deliverability Engine</p>
                </div>
              </div>

              {/* Desktop Tabs */}
              <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-200">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = currentTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onTabChange(item.id)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                        isActive
                          ? 'bg-navy-50 text-navy-900 font-semibold border border-slate-200'
                          : 'text-slate-600 hover:text-navy-900 hover:bg-slate-50'
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-navy-900' : 'text-slate-500'}`} />
                      {item.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            {/* Right Status */}
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-50 border border-slate-200 text-xs">
                <span className={`w-2 h-2 rounded-full ${apiStatus === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                <span className="text-slate-600 font-medium">
                  {apiStatus === 'online' ? 'API Online' : 'Connecting...'}
                </span>
              </div>

              {/* Mobile menu toggle */}
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 text-slate-600 hover:text-navy-900 rounded-md"
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-3 space-y-1">
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
                  className={`w-full flex items-center gap-2.5 px-3 py-2 text-sm font-medium rounded-md text-left ${
                    isActive
                      ? 'bg-navy-50 text-navy-900 font-semibold'
                      : 'text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4 text-navy-700" />
                  {item.label}
                </button>
              );
            })}
          </div>
        )}
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Clean, restrained footer */}
      <footer className="border-t border-slate-200 py-6 bg-slate-50/50 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <span className="font-semibold text-navy-900">OpenMail Verify</span> — Open-source email verification & domain intelligence engine.
          </div>
          <div className="flex items-center gap-4 text-slate-500">
            <span>RFC 5322 Compliant</span>
            <span>•</span>
            <span>Real DNS/MX Inspection</span>
            <span>•</span>
            <span>MIT License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
