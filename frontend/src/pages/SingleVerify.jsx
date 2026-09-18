import React, { useState } from 'react';
import { 
  Search, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  Loader2, 
  Server, 
  Globe, 
  Shield, 
  Copy, 
  Check, 
  RefreshCw,
  Lock,
  Info
} from 'lucide-react';
import { verificationApi } from '../services/api';
import ScoreBar from '../components/ScoreBar';

export default function SingleVerify() {
  const [emailInput, setEmailInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [copied, setCopied] = useState(false);

  const sampleEmails = [
    'john.smith@gmail.com',
    'random-user-928374928374@gmail.com',
    'info@gmail.com',
    'test@mailinator.com',
    'john@@gmail..com',
    'user@nonexistent-domain-xyz-999.com',
  ];

  const handleVerify = async (emailToVerify) => {
    const target = (emailToVerify || emailInput).trim();
    if (!target) {
      setErrorMsg('Please enter an email address.');
      return;
    }

    setEmailInput(target);
    setErrorMsg('');
    setLoading(true);
    setResult(null);

    const res = await verificationApi.verifyEmail(target);
    setLoading(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setResult(res.data);
    }
  };

  const handleCopyJSON = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = (status) => {
    const statusUpper = (status || '').toUpperCase();
    if ((statusUpper.includes('VALID') || statusUpper.includes('REACHABLE') || statusUpper.includes('REAL')) && !statusUpper.includes('NOT')) {
      return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full badge-valid"><span className="w-2 h-2 rounded-full bg-emerald-600"></span>REAL / REACHABLE</span>;
    }
    if (statusUpper.includes('RISKY')) {
      return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full badge-risky"><span className="w-2 h-2 rounded-full bg-amber-600"></span>RISKY</span>;
    }
    if (statusUpper.includes('INVALID') || statusUpper.includes('NOT REAL')) {
      return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full badge-invalid"><span className="w-2 h-2 rounded-full bg-red-600"></span>NOT REAL / INVALID</span>;
    }
    return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-bold rounded-full badge-unknown"><span className="w-2 h-2 rounded-full bg-slate-500"></span>UNKNOWN</span>;
  };

  const getStepStatusTag = (val, okValue = 'VALID') => {
    if (val === okValue || val === 'FOUND' || val === 'CONNECTED' || val === 'ACCEPTED' || val === 'PASS' || val === 'CONFIRMED') {
      return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    }
    if (val === 'INVALID' || val === 'MISSING' || val === 'REJECTED' || val === 'FAIL') {
      return 'text-red-700 bg-red-50 border-red-200';
    }
    return 'text-amber-700 bg-amber-50 border-amber-200';
  };

  const getStepIcon = (val, okValue = 'VALID') => {
    if (val === okValue || val === 'FOUND' || val === 'CONNECTED' || val === 'ACCEPTED' || val === 'PASS' || val === 'CONFIRMED') {
      return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
    }
    if (val === 'INVALID' || val === 'MISSING' || val === 'REJECTED' || val === 'FAIL') {
      return <XCircle className="w-4 h-4 text-red-600 shrink-0" />;
    }
    return <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Email Verification Workspace</h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Verify whether a specific email address appears to be a REAL/REACHABLE mailbox without sending an email or OTP to the recipient.
        </p>
      </div>

      {/* Input Card */}
      <div className="saas-card p-6">
        <form onSubmit={(e) => { e.preventDefault(); handleVerify(); }} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Email Address to Verify
            </label>
            <div className="flex flex-col sm:flex-row gap-2.5">
              <input
                type="text"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="e.g. alex.smith@company.com"
                className="saas-input flex-1 px-4 py-2.5 text-sm font-mono"
              />
              <button
                type="submit"
                disabled={loading}
                className="saas-btn-primary px-6 py-2.5 text-sm flex items-center justify-center gap-2 shrink-0 font-bold"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    VERIFY EMAIL
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Quick preset chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
            <span className="text-slate-500 font-medium">Test examples:</span>
            {sampleEmails.map((sample) => (
              <button
                key={sample}
                type="button"
                onClick={() => handleVerify(sample)}
                className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 hover:bg-slate-200 font-mono transition-colors"
              >
                {sample}
              </button>
            ))}
          </div>

          {errorMsg && (
            <div className="p-4 bg-red-50 border border-red-200 rounded flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-red-700">
              <div>
                <span className="font-semibold block sm:inline">Verification Notice:</span> {errorMsg}
              </div>
              <button
                type="button"
                onClick={() => handleVerify()}
                className="saas-btn-secondary px-3 py-1.5 text-xs text-navy-900 self-start sm:self-auto flex items-center gap-1 shrink-0"
              >
                <RefreshCw className="w-3 h-3" />
                Retry
              </button>
            </div>
          )}
        </form>
      </div>

      {/* Verification Result Display */}
      {result && (
        <div className="space-y-6">
          {/* Top Result Banner */}
          <div className="saas-card p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-200">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">FINAL RESULT</span>
                  {getStatusBadge(result.final_status || result.status)}
                </div>
                <h2 className="text-xl font-bold font-mono text-navy-900 break-all">{result.email}</h2>
              </div>

              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 self-start md:self-auto">
                <div className="flex items-center gap-2 text-[11px] font-semibold px-3 py-1.5 bg-slate-100 border border-slate-200 rounded text-slate-700">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  <span>EMAIL SENT: NO</span>
                  <span className="text-slate-300">|</span>
                  <span>OTP SENT: NO</span>
                  <span className="text-slate-300">|</span>
                  <span>DATA EXECUTED: NO</span>
                </div>
                <button
                  onClick={handleCopyJSON}
                  className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'JSON Copied' : 'Copy JSON'}
                </button>
              </div>
            </div>

            {/* Diagnostic Reason Box */}
            <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded text-xs space-y-1">
              <span className="font-bold text-navy-900 uppercase tracking-wider text-[11px] block">TECHNICAL REASON</span>
              <p className="text-slate-800 font-medium leading-relaxed">{result.reason || result.message}</p>
              {result.reason !== result.message && (
                <p className="text-slate-500 leading-relaxed">{result.message}</p>
              )}
            </div>

            {/* SMTP Protocol Trace Evidence Panel */}
            {result.smtp_trace && (
              <div className="mt-4 p-4 bg-navy-950 text-slate-200 rounded border border-navy-800 font-mono text-xs space-y-2">
                <div className="flex items-center justify-between pb-2 border-b border-navy-800">
                  <span className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">SMTP PROTOCOL RECIPIENT TRACE EVIDENCE</span>
                  <span className="text-[10px] text-slate-400">MX Host: {result.smtp_trace.hostname || result.mx_host || 'N/A'}</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] pt-1">
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Stage</span>
                    <span className="font-bold text-white">{result.smtp_trace.stage || 'SKIPPED'}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Server Response Code</span>
                    <span className="font-bold text-amber-300">
                      {result.checks.smtp?.details?.server_code || result.smtp_trace.rcpt_to?.code || result.smtp_trace.greeting?.code || 'N/A'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px] uppercase font-semibold">Catch-All Status</span>
                    <span className="font-bold text-white">
                      {result.smtp_trace.catch_all_probe ? (result.smtp_trace.catch_all_probe.is_catch_all ? 'DETECTED (Arbitrary Mailbox Accepted)' : 'NOT DETECTED') : 'NOT TESTED'}
                    </span>
                  </div>
                </div>
                {result.smtp_trace.greeting && (
                  <div className="text-[11px]">
                    <span className="text-slate-400 font-semibold">GREETING: </span>
                    <span className="text-slate-300">{result.smtp_trace.greeting.code} {result.smtp_trace.greeting.response}</span>
                  </div>
                )}
                {result.smtp_trace.mail_from && (
                  <div className="text-[11px]">
                    <span className="text-slate-400 font-semibold">MAIL FROM: </span>
                    <span className="text-slate-300">{result.smtp_trace.mail_from.code} {result.smtp_trace.mail_from.response}</span>
                  </div>
                )}
                {result.smtp_trace.rcpt_to && (
                  <div className="text-[11px]">
                    <span className="text-slate-400 font-semibold">RCPT TO: </span>
                    <span className={result.smtp_trace.rcpt_to.code === 250 ? 'text-emerald-400 font-bold' : (result.smtp_trace.rcpt_to.code >= 500 ? 'text-red-400 font-bold' : 'text-amber-300 font-bold')}>
                      {result.smtp_trace.rcpt_to.code} {result.smtp_trace.rcpt_to.response}
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* 5-Step Core Evidence Breakdown Matrix */}
            <div className="mt-6 border border-slate-200 rounded-md overflow-hidden text-xs">
              <div className="bg-slate-100/70 px-4 py-2.5 border-b border-slate-200 font-bold uppercase tracking-wider text-slate-600 flex items-center justify-between">
                <span>Core 5-Step Verification Breakdown</span>
                <span className="font-mono text-[11px] text-slate-500">FORMAT VALIDITY ≠ MAILBOX EXISTENCE</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-5 divide-y sm:divide-y-0 sm:divide-x divide-slate-200 bg-white">
                {/* Step 1: Email Format */}
                <div className="p-3.5 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">1. Email Format</span>
                  <div className="flex items-center gap-1.5">
                    {getStepIcon(result.email_format)}
                    <span className="font-bold text-navy-900">{result.email_format || 'VALID'}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">RFC 5322 Syntax</p>
                </div>

                {/* Step 2: Domain Status */}
                <div className="p-3.5 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">2. Domain Status</span>
                  <div className="flex items-center gap-1.5">
                    {getStepIcon(result.domain_status)}
                    <span className="font-bold text-navy-900">{result.domain_status || 'VALID'}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">DNS A/AAAA Record</p>
                </div>

                {/* Step 3: MX Records */}
                <div className="p-3.5 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">3. MX Records</span>
                  <div className="flex items-center gap-1.5">
                    {getStepIcon(result.mx_status, 'FOUND')}
                    <span className="font-bold text-navy-900">{result.mx_status || 'FOUND'}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Mail Infrastructure</p>
                </div>

                {/* Step 4: SMTP Connection */}
                <div className="p-3.5 space-y-1">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">4. SMTP Probe</span>
                  <div className="flex items-center gap-1.5">
                    {getStepIcon(result.smtp_connection_status, 'CONNECTED')}
                    <span className="font-bold text-navy-900">{result.smtp_connection_status || 'CONNECTED'}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">Handshake & EHLO</p>
                </div>

                {/* Step 5: Recipient Response */}
                <div className="p-3.5 space-y-1 bg-slate-50/50">
                  <span className="text-[11px] font-semibold text-slate-500 uppercase block">5. Recipient Status</span>
                  <div className="flex items-center gap-1.5">
                    {getStepIcon(result.recipient_status, 'ACCEPTED')}
                    <span className="font-bold text-navy-900">{result.recipient_status || 'UNCONFIRMED'}</span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-tight">RCPT TO Response</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
              {/* Score & Confidence */}
              <div className="lg:col-span-1">
                <ScoreBar confidence={result.confidence || result.score} status={result.status} />
              </div>

              {/* Technical Evidence Grid */}
              <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Mailbox Evidence</span>
                  <span className="font-mono text-xs font-bold text-navy-900">{result.mailbox_evidence || 'NO_EVIDENCE'}</span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Mailbox Existence</span>
                  <span className="text-xs font-bold text-navy-900">{result.mailbox_existence || 'NOT CONFIRMED'}</span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Capability Model</span>
                  <span className="text-[11px] font-medium text-slate-700">{result.verification_capability || 'UNKNOWN'}</span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Risk Signals</span>
                  <span className="text-xs font-semibold text-navy-900">
                    {result.risk_signals && result.risk_signals.length > 0 ? result.risk_signals.join(', ') : 'None'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 2-Column Deep Inspection */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Column 1: Verification Pipeline Checklist */}
            <div className="saas-card p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="text-sm font-bold text-navy-900 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-navy-700" />
                  Technical Verification Checklist
                </h3>
                <span className="text-xs text-slate-500 font-mono">100% Non-Delivery</span>
              </div>

              <div className="space-y-2.5 text-xs">
                {/* Level 1: Syntax */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.syntax.display_value, 'PASS')}
                    <div>
                      <span className="font-bold text-navy-900 block">Level 1: Email Syntax</span>
                      <span className="text-[11px] text-slate-500">RFC 5322 structure, local-part, @ placement</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.syntax.display_value, 'PASS')}`}>
                    {result.checks.syntax.display_value}
                  </span>
                </div>

                {/* Level 2: Domain Format */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.domain.display_value, 'PASS')}
                    <div>
                      <span className="font-bold text-navy-900 block">Level 2: Domain Format</span>
                      <span className="text-[11px] text-slate-500">Valid domain TLD and label length</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.domain.display_value, 'PASS')}`}>
                    {result.checks.domain.display_value}
                  </span>
                </div>

                {/* Level 2: DNS Resolution */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.dns.display_value, 'PASS')}
                    <div>
                      <span className="font-bold text-navy-900 block">Level 2: DNS Resolution</span>
                      <span className="text-[11px] text-slate-500">Active A / AAAA nameserver records</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.dns.display_value, 'PASS')}`}>
                    {result.checks.dns.display_value}
                  </span>
                </div>

                {/* Level 3: MX Record Check */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.mx.display_value, 'PASS')}
                    <div>
                      <span className="font-bold text-navy-900 block">Level 3: MX Record Configuration</span>
                      <span className="text-[11px] text-slate-500">Configured mail exchange servers & priority</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.mx.display_value, 'PASS')}`}>
                    {result.checks.mx.display_value}
                  </span>
                </div>

                {/* Level 4: SMTP Probing */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.smtp.display_value, 'ACCEPTED')}
                    <div>
                      <span className="font-bold text-navy-900 block">Level 4: SMTP Recipient Probe</span>
                      <span className="text-[11px] text-slate-500">Non-delivery EHLO/RCPT TO handshake</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.smtp.display_value, 'ACCEPTED')}`}>
                    {result.checks.smtp.display_value}
                  </span>
                </div>

                {/* Catch-All Check */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getStepIcon(result.checks.catch_all?.display_value === 'YES' ? 'YES' : 'NO', 'NO')}
                    <div>
                      <span className="font-bold text-navy-900 block">Catch-All Routing Check</span>
                      <span className="text-[11px] text-slate-500">Domain accepts arbitrary recipient addresses</span>
                    </div>
                  </div>
                  <span className={`px-2.5 py-0.5 font-mono font-bold rounded border text-[11px] ${getStepStatusTag(result.checks.catch_all?.display_value === 'YES' ? 'YES' : 'NO', 'NO')}`}>
                    {result.checks.catch_all?.display_value || 'NO'}
                  </span>
                </div>
              </div>
            </div>

            {/* Column 2: Domain Intelligence & MX Records */}
            <div className="saas-card p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="text-sm font-bold text-navy-900 flex items-center gap-2">
                  <Server className="w-4 h-4 text-navy-700" />
                  Domain Intelligence & Mail Routing
                </h3>
                <span className="font-mono text-xs text-slate-500">{result.domain || 'N/A'}</span>
              </div>

              {result.domain_intelligence ? (
                <div className="space-y-4 text-xs">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="saas-card-muted p-3">
                      <span className="text-slate-500 block mb-0.5">DNS Status</span>
                      <span className="font-semibold text-navy-900">
                        {result.domain_intelligence.is_resolvable ? 'Resolved (A/AAAA)' : 'Unresolved'}
                      </span>
                    </div>
                    <div className="saas-card-muted p-3">
                      <span className="text-slate-500 block mb-0.5">SMTP Probing</span>
                      <span className="font-semibold text-navy-900">
                        {result.checks.smtp?.display_value || 'SKIPPED'}
                      </span>
                    </div>
                  </div>

                  {/* MX Record Host Table */}
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-2">
                      Configured Mail Exchanges (MX)
                    </span>
                    {result.domain_intelligence.mx_records.length === 0 ? (
                      <div className="p-3 bg-slate-50 rounded border border-slate-200 text-slate-500">
                        No active MX records returned by DNS resolver.
                      </div>
                    ) : (
                      <div className="border border-slate-200 rounded overflow-hidden">
                        <table className="w-full text-left">
                          <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200">
                            <tr>
                              <th className="py-2 px-3">Priority</th>
                              <th className="py-2 px-3">Exchange Hostname</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 font-mono">
                            {result.domain_intelligence.mx_records.map((mx, idx) => (
                              <tr key={idx} className="hover:bg-slate-50/50">
                                <td className="py-2 px-3 text-navy-700 font-bold">{mx.priority}</td>
                                <td className="py-2 px-3 text-navy-900 truncate max-w-xs">{mx.host}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-slate-600 leading-relaxed text-[11px]">
                    <span className="font-semibold text-navy-900">Technical Principle:</span> MailScope evaluates deliverability using non-delivery technical signals. Format validity and domain existence do not guarantee mailbox availability.
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500">No domain intelligence available.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
