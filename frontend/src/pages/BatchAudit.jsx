import React, { useState } from 'react';
import { 
  ShieldCheck, 
  Download, 
  Loader2, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle,
  FileSpreadsheet,
  RotateCcw
} from 'lucide-react';
import { verificationApi } from '../services/api';
import DetailDrawer from '../components/DetailDrawer';

export default function BatchAudit() {
  const [emailsText, setEmailsText] = useState('');
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');

  const sampleBatch = [
    'john.doe@gmail.com',
    'sarah.connor@outlook.com',
    'support@github.com',
    'admin@stripe.com',
    'testuser@mailinator.com',
    'burner@tempmail.com',
    'invalid-email-format-xyz',
    'contact@fake-nonexistent-domain-449.com',
  ].join('\n');

  const handleStartBatch = async () => {
    const rawList = emailsText
      .split(/[\n,]+/)
      .map(e => e.trim())
      .filter(e => e.length > 0);

    if (rawList.length === 0) {
      setErrorMsg('Please enter at least one email address.');
      return;
    }

    if (rawList.length > 50) {
      setErrorMsg('Batch size limit is 50 email addresses at a time.');
      return;
    }

    setErrorMsg('');
    setLoading(true);
    setBatchResult(null);

    const res = await verificationApi.batchVerifyEmails(rawList);
    setLoading(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setBatchResult(res.data);
    }
  };

  const handleExportCSV = () => {
    if (!batchResult || !batchResult.results) return;

    const headers = ['Email', 'Normalized', 'Domain', 'Status', 'Confidence', 'Syntax', 'Domain', 'DNS', 'MX', 'SMTP', 'Mailbox', 'Disposable', 'RoleBased', 'Reason'];
    const rows = batchResult.results.map(r => [
      r.email,
      r.normalized_email,
      r.domain,
      r.status,
      r.confidence || r.score,
      r.checks.syntax?.display_value || (r.checks.syntax.passed ? 'PASS' : 'FAIL'),
      r.checks.domain?.display_value || (r.checks.domain.passed ? 'PASS' : 'FAIL'),
      r.checks.dns?.display_value || (r.checks.dns.passed ? 'PASS' : 'FAIL'),
      r.checks.mx?.display_value || (r.checks.mx.passed ? 'PASS' : 'FAIL'),
      r.checks.smtp?.display_value || 'UNKNOWN',
      r.checks.mailbox?.display_value || 'UNCONFIRMED',
      r.checks.disposable?.display_value || (!r.checks.disposable.passed ? 'YES' : 'NO'),
      r.checks.role_based?.display_value || (!r.checks.role_based.passed ? 'YES' : 'NO'),
      `"${(r.reason || r.message || '').replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `openmail_batch_audit_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full badge-valid"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>VALID</span>;
      case 'RISKY':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full badge-risky"><span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>RISKY</span>;
      case 'INVALID':
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full badge-invalid"><span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>INVALID</span>;
      default:
        return <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-semibold rounded-full badge-unknown"><span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>UNKNOWN</span>;
    }
  };

  const filteredResults = batchResult?.results?.filter(item => {
    if (statusFilter === 'ALL') return true;
    return item.status === statusFilter;
  }) || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Batch Email Audit</h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Verify up to 50 email addresses in a single pipeline audit. Export results directly to CSV.
        </p>
      </div>

      {/* Input Section */}
      <div className="saas-card p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Paste Email Addresses (One per line or comma separated)
            </label>
            <button
              type="button"
              onClick={() => setEmailsText(sampleBatch)}
              className="text-xs text-navy-700 font-semibold hover:underline"
            >
              Load Sample Batch
            </button>
          </div>

          <textarea
            rows={6}
            value={emailsText}
            onChange={(e) => setEmailsText(e.target.value)}
            placeholder="john.doe@gmail.com&#10;support@company.com&#10;test@mailinator.com"
            className="saas-input w-full p-3 font-mono text-xs resize-y"
          />

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
            <div className="text-xs text-slate-500">
              {emailsText.split(/[\n,]+/).filter(e => e.trim().length > 0).length} / 50 emails entered
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => { setEmailsText(''); setBatchResult(null); setErrorMsg(''); }}
                className="saas-btn-secondary px-3.5 py-2 text-xs flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Clear
              </button>

              <button
                type="button"
                onClick={handleStartBatch}
                disabled={loading}
                className="saas-btn-primary px-5 py-2 text-xs flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Executing Audit...
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-3.5 h-3.5" />
                    Start Verification
                  </>
                )}
              </button>
            </div>
          </div>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700">
              {errorMsg}
            </div>
          )}
        </div>
      </div>

      {/* Batch Summary & Table */}
      {batchResult && (
        <div className="space-y-6">
          {/* Summary Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Total Audited</span>
              <span className="font-mono text-xl font-bold text-navy-900">{batchResult.total}</span>
            </div>
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Valid</span>
              <span className="font-mono text-xl font-bold text-emerald-700">{batchResult.valid_count}</span>
            </div>
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Risky</span>
              <span className="font-mono text-xl font-bold text-amber-700">{batchResult.risky_count}</span>
            </div>
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Invalid</span>
              <span className="font-mono text-xl font-bold text-red-700">{batchResult.invalid_count}</span>
            </div>
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Unknown</span>
              <span className="font-mono text-xl font-bold text-slate-600">{batchResult.unknown_count}</span>
            </div>
            <div className="saas-card p-3">
              <span className="text-[10px] uppercase font-semibold text-slate-500 block">Avg Confidence</span>
              <span className="font-mono text-xl font-bold text-navy-900">{batchResult.average_score}</span>
            </div>
          </div>

          {/* Results Table Card */}
          <div className="saas-card overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              {/* Filter tabs */}
              <div className="flex items-center gap-1">
                {['ALL', 'VALID', 'RISKY', 'INVALID', 'UNKNOWN'].map(status => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-2.5 py-1 text-xs font-semibold rounded ${
                      statusFilter === status
                        ? 'bg-navy-800 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>

              {/* CSV Export */}
              <button
                onClick={handleExportCSV}
                className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5 self-start sm:self-auto"
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Email</th>
                    <th className="py-3 px-4">Domain</th>
                    <th className="py-3 px-4">Result</th>
                    <th className="py-3 px-4 text-center">Confidence</th>
                    <th className="py-3 px-4">SMTP / Mailbox</th>
                    <th className="py-3 px-4">Reason</th>
                    <th className="py-3 px-4 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {filteredResults.map((item, idx) => (
                    <tr 
                      key={idx}
                      className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                      onClick={() => {
                        setSelectedItem({
                          ...item,
                          is_syntax_valid: item.checks.syntax.passed,
                          is_domain_resolved: item.checks.dns.passed,
                          is_mx_found: item.checks.mx.passed,
                          is_disposable: !item.checks.disposable.passed,
                          is_role_based: !item.checks.role_based.passed,
                        });
                        setDrawerOpen(true);
                      }}
                    >
                      <td className="py-3 px-4 font-medium text-navy-900 max-w-xs truncate">{item.email}</td>
                      <td className="py-3 px-4 text-slate-600">{item.domain || 'N/A'}</td>
                      <td className="py-3 px-4 font-sans">{getStatusBadge(item.status)}</td>
                      <td className="py-3 px-4 text-center font-bold text-navy-900">{item.confidence || item.score}</td>
                      <td className="py-3 px-4 font-sans text-slate-700">
                        {item.checks.smtp?.display_value || 'PROBED'} / {item.checks.mailbox?.display_value || 'UNCONFIRMED'}
                      </td>
                      <td className="py-3 px-4 font-sans text-slate-500 max-w-xs truncate">
                        {item.reason || item.message}
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <span className="text-xs text-navy-700 font-medium hover:underline">Inspect</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Slide-out detail drawer */}
      <DetailDrawer
        item={selectedItem}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
