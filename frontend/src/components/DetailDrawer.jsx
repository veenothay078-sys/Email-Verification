import React from 'react';
import { X, CheckCircle2, XCircle, AlertTriangle, HelpCircle, Shield, Server, Globe, Lock } from 'lucide-react';

export default function DetailDrawer({ item, isOpen, onClose }) {
  if (!isOpen || !item) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full badge-valid"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>REAL / VALID</span>;
      case 'RISKY':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full badge-risky"><span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>RISKY</span>;
      case 'INVALID':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full badge-invalid"><span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>NOT REAL / INVALID</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-bold rounded-full badge-unknown"><span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>UNKNOWN</span>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-navy-900/30 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md bg-white border-l border-slate-200 shadow-xl flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Verification Inspection</span>
              <h3 className="text-base font-bold text-navy-900 truncate mt-0.5">{item.email}</h3>
            </div>
            <button
              onClick={onClose}
              className="p-1 text-slate-400 hover:text-navy-900 rounded-md transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Status & Score banner */}
            <div className="saas-card p-4 flex items-center justify-between">
              <div>
                <span className="text-xs text-slate-500 block mb-1">Status</span>
                {getStatusBadge(item.status)}
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500 block mb-1">Score</span>
                <span className="font-mono text-xl font-bold text-navy-900">{item.score}<span className="text-xs font-normal text-slate-400">/100</span></span>
              </div>
            </div>



            {/* Section: Identity */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                <Globe className="w-3.5 h-3.5 text-navy-700" />
                Identity & Syntax
              </h4>
              <div className="saas-card divide-y divide-slate-100 text-sm">
                <div className="p-3 flex justify-between">
                  <span className="text-slate-600">Normalized Address</span>
                  <span className="font-mono text-xs text-navy-900 select-all">{item.normalized_email || item.email}</span>
                </div>
                <div className="p-3 flex justify-between">
                  <span className="text-slate-600">Domain</span>
                  <span className="font-mono text-xs text-navy-900">{item.domain}</span>
                </div>
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">RFC 5322 Syntax</span>
                  <span className={`text-xs font-medium ${item.is_syntax_valid !== false ? 'text-emerald-700' : 'text-red-700'}`}>
                    {item.is_syntax_valid !== false ? 'Passed' : 'Failed'}
                  </span>
                </div>
              </div>
            </div>

            {/* Section: Infrastructure */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                <Server className="w-3.5 h-3.5 text-navy-700" />
                Infrastructure & Mail Routing
              </h4>
              <div className="saas-card divide-y divide-slate-100 text-sm">
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">DNS Resolution</span>
                  <span className={`text-xs font-medium ${item.is_domain_resolved !== false ? 'text-emerald-700' : 'text-red-700'}`}>
                    {item.is_domain_resolved !== false ? 'Resolved' : 'Unresolved'}
                  </span>
                </div>
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">MX Mail Server</span>
                  <span className={`text-xs font-medium ${item.is_mx_found !== false ? 'text-emerald-700' : 'text-red-700'}`}>
                    {item.is_mx_found !== false ? 'Configured' : 'Missing'}
                  </span>
                </div>
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">Server-Side SMTP Probing</span>
                  <span className="text-xs font-medium text-navy-900">
                    Non-Delivery Handshake Analyzed
                  </span>
                </div>
              </div>
            </div>

            {/* Section: Risk Signals */}
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                <Shield className="w-3.5 h-3.5 text-navy-700" />
                Risk Signals
              </h4>
              <div className="saas-card divide-y divide-slate-100 text-sm">
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">Disposable Domain</span>
                  <span className={`text-xs font-medium ${item.is_disposable ? 'text-amber-700 font-semibold' : 'text-slate-700'}`}>
                    {item.is_disposable ? 'Yes (Temporary)' : 'No'}
                  </span>
                </div>
                <div className="p-3 flex justify-between items-center">
                  <span className="text-slate-600">Role-Based Alias</span>
                  <span className={`text-xs font-medium ${item.is_role_based ? 'text-amber-700 font-semibold' : 'text-slate-700'}`}>
                    {item.is_role_based ? 'Yes (Group/Role)' : 'No'}
                  </span>
                </div>
              </div>
            </div>

            {/* Section: Diagnostic message */}
            {item.message && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-md">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block mb-1">Diagnostic Output</span>
                <p className="text-xs text-slate-700 leading-relaxed">{item.message}</p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex justify-end">
            <button
              onClick={onClose}
              className="saas-btn-secondary px-4 py-1.5 text-xs"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
