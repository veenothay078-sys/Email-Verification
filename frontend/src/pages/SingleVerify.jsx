import React, { useState, useEffect } from 'react';
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
  Mail,
  Send,
  KeyRound,
  ShieldCheck,
  Clock,
  Sparkles,
  Inbox
} from 'lucide-react';
import { verificationApi } from '../services/api';
import ScoreBar from '../components/ScoreBar';

export default function SingleVerify() {
  const [emailInput, setEmailInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [copied, setCopied] = useState(false);

  // Mailbox Verification OTP states
  const [otpInput, setOtpInput] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [otpSuccessMsg, setOtpSuccessMsg] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [attemptsRemaining, setAttemptsRemaining] = useState(null);

  const sampleEmails = [
    'john123@gmail.com',
    'info@gmail.com',
    'test@mailinator.com',
    'john@@gmail.com',
    'user@nonexistent-domain-xyz-982138.com',
  ];

  // Cooldown countdown effect
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

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
    setOtpSent(false);
    setOtpInput('');
    setOtpError('');
    setOtpSuccessMsg('');
    setAttemptsRemaining(null);

    const res = await verificationApi.verifyEmail(target);
    setLoading(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setResult(res.data);
    }
  };

  const handleSendOtp = async () => {
    if (!result || !result.email) return;
    setOtpSending(true);
    setOtpError('');
    setOtpSuccessMsg('');

    const res = await verificationApi.sendMailboxCode(result.email);
    setOtpSending(false);

    if (res.error) {
      setOtpError(res.error);
    } else {
      setOtpSent(true);
      setOtpSuccessMsg(res.data.message || `Verification code sent to ${result.email}`);
      setCooldown(res.data.cooldown_seconds || 60);
    }
  };

  const handleVerifyOtp = async (e) => {
    if (e) e.preventDefault();
    const cleanCode = otpInput.trim();
    if (!cleanCode || cleanCode.length !== 6) {
      setOtpError('Please enter the full 6-digit verification code.');
      return;
    }

    if (!result || !result.email) return;

    setOtpVerifying(true);
    setOtpError('');

    const res = await verificationApi.verifyMailboxCode(result.email, cleanCode);
    setOtpVerifying(false);

    if (res.error) {
      setOtpError(res.error);
      if (res.data?.attempts_remaining !== undefined) {
        setAttemptsRemaining(res.data.attempts_remaining);
      }
    } else {
      setOtpSuccessMsg('✓ Mailbox ownership verified successfully.');
      if (res.data.verification_result) {
        setResult(res.data.verification_result);
      }
    }
  };

  const handleCopyJSON = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full badge-valid"><span className="w-2 h-2 rounded-full bg-emerald-600"></span>VALID</span>;
      case 'RISKY':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full badge-risky"><span className="w-2 h-2 rounded-full bg-amber-600"></span>RISKY</span>;
      case 'INVALID':
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full badge-invalid"><span className="w-2 h-2 rounded-full bg-red-600"></span>INVALID</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-full badge-unknown"><span className="w-2 h-2 rounded-full bg-slate-500"></span>UNKNOWN</span>;
    }
  };

  const getCheckTagStyle = (val) => {
    if (['PASS', 'ACCEPTED', 'CONFIRMED', 'NO'].includes(val)) {
      return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    }
    if (['FAIL', 'REJECTED'].includes(val)) {
      return 'text-red-700 bg-red-50 border-red-200';
    }
    if (['YES'].includes(val)) {
      return 'text-amber-700 bg-amber-50 border-amber-200';
    }
    return 'text-slate-700 bg-slate-100 border-slate-200';
  };

  const getCheckIcon = (val) => {
    if (['PASS', 'ACCEPTED', 'CONFIRMED', 'NO'].includes(val)) {
      return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />;
    }
    if (['FAIL', 'REJECTED'].includes(val)) {
      return <XCircle className="w-4 h-4 text-red-600 shrink-0" />;
    }
    if (['YES'].includes(val)) {
      return <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />;
    }
    return <HelpCircle className="w-4 h-4 text-slate-500 shrink-0" />;
  };

  const isMailboxConfirmed = result && (
    result.checks?.mailbox?.display_value === 'CONFIRMED' || 
    result.status === 'VALID' ||
    result.checks?.mailbox?.message?.includes('verified')
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="pb-2 border-b border-slate-200">
        <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Email Verification Workspace</h1>
        <p className="text-sm text-slate-600 mt-0.5">
          Verify specific mailbox existence, server infrastructure, and deliverability risk signals.
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
                className="saas-btn-primary px-6 py-2.5 text-sm flex items-center justify-center gap-2 shrink-0"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Verify Email
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
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Final Result</span>
                  {getStatusBadge(result.status)}
                </div>
                <h2 className="text-xl font-bold font-mono text-navy-900 break-all">{result.email}</h2>
                <p className="text-xs text-slate-700 font-medium">{result.message}</p>
                {result.reason && result.reason !== result.message && (
                  <p className="text-xs text-slate-500">{result.reason}</p>
                )}
              </div>

              <div className="flex items-center gap-2 self-start md:self-auto">
                <button
                  onClick={handleCopyJSON}
                  className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  {copied ? 'JSON Copied' : 'Copy JSON'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-6">
              {/* Verification Confidence Bar */}
              <div className="lg:col-span-1">
                <ScoreBar confidence={result.confidence || result.score} status={result.status} />
              </div>

              {/* Identity & Mailbox Quick Summary */}
              <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Normalized</span>
                  <span className="font-mono text-xs text-navy-900 break-all">{result.normalized_email}</span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Domain</span>
                  <span className="font-mono text-xs text-navy-900">{result.domain || 'N/A'}</span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Mailbox</span>
                  <span className={`text-xs font-semibold ${
                    result.checks.mailbox?.display_value === 'CONFIRMED'
                      ? 'text-emerald-700'
                      : result.checks.mailbox?.display_value === 'REJECTED'
                      ? 'text-red-700'
                      : 'text-amber-700'
                  }`}>
                    {result.checks.mailbox?.display_value || 'UNCONFIRMED'}
                  </span>
                </div>
                <div className="saas-card-muted p-3">
                  <span className="text-[11px] text-slate-500 block uppercase font-semibold">Risk Factor</span>
                  <span className="text-xs font-semibold text-navy-900">
                    {result.checks.disposable?.display_value === 'YES' ? 'Disposable' : result.checks.role_based?.display_value === 'YES' ? 'Role Based' : 'None'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Mailbox Ownership & Accessibility Verification Challenge Card */}
          <div className="saas-card p-6 border-l-4 border-l-navy-800">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-navy-800" />
                  <h3 className="text-sm font-bold text-navy-900">Mailbox Ownership & Access Verification</h3>
                </div>
                <p className="text-xs text-slate-600">
                  Verify actual recipient mailbox access using a cryptographically secure 6-digit one-time code (OTP).
                </p>
              </div>

              {isMailboxConfirmed && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Mailbox Verified
                </span>
              )}
            </div>

            <div className="pt-4">
              {isMailboxConfirmed ? (
                /* Verified Success State */
                <div className="p-4 bg-emerald-50/80 border border-emerald-200 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                  <div className="space-y-1">
                    <div className="font-bold text-emerald-900 flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-600" />
                      ✓ Mailbox verified &bull; ✓ Verification code confirmed
                    </div>
                    <p className="text-emerald-700">
                      Recipient mailbox ownership and accessibility have been positively confirmed. Final deliverability score certified at 100/100 (VALID).
                    </p>
                  </div>
                  <span className="px-3 py-1 font-mono text-[11px] font-bold bg-white text-emerald-800 border border-emerald-300 rounded shrink-0">
                    STATUS: VALID (100/100)
                  </span>
                </div>
              ) : result.status === 'INVALID' ? (
                /* Disabled for Invalid Emails */
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-600 flex items-center gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-slate-400 shrink-0" />
                  <span>
                    Mailbox code verification is unavailable because this email address failed technical syntax, domain, or mail server routing checks.
                  </span>
                </div>
              ) : (
                /* Interactive Verification Challenge */
                <div className="space-y-4">
                  {!otpSent ? (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                      <div className="space-y-1 max-w-xl">
                        <span className="font-bold text-navy-900 block">Mailbox verification required</span>
                        <p className="text-slate-600">
                          To confirm that <strong className="text-navy-900 font-mono">{result.email}</strong> is actively accessible, dispatch a secure one-time code to the recipient inbox.
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={otpSending}
                        className="saas-btn-primary px-5 py-2.5 text-xs flex items-center justify-center gap-2 shrink-0 font-medium"
                      >
                        {otpSending ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            Sending Code...
                          </>
                        ) : (
                          <>
                            <Send className="w-3.5 h-3.5" />
                            Send verification code
                          </>
                        )}
                      </button>
                    </div>
                  ) : (
                    /* Code Entry State */
                    <div className="space-y-4 p-4 bg-slate-50 border border-slate-200 rounded-lg">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <div className="text-slate-700">
                          <span className="font-bold text-navy-900">Verification code sent</span> to{' '}
                          <span className="font-mono font-bold text-navy-900">{result.email}</span> (expires in 10 minutes).
                        </div>
                        {cooldown > 0 ? (
                          <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" /> Resend in {cooldown}s
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={handleSendOtp}
                            disabled={otpSending}
                            className="text-navy-800 hover:text-navy-950 font-semibold underline text-xs flex items-center gap-1"
                          >
                            <RefreshCw className="w-3 h-3" /> Resend code
                          </button>
                        )}
                      </div>

                      <form onSubmit={handleVerifyOtp} className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
                        <div className="relative flex-1 max-w-xs">
                          <input
                            type="text"
                            maxLength={6}
                            value={otpInput}
                            onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ''))}
                            placeholder="Enter 6-digit code"
                            className="saas-input w-full px-4 py-2 text-base font-mono tracking-widest text-center"
                            autoFocus
                          />
                        </div>

                        <button
                          type="submit"
                          disabled={otpVerifying || otpInput.trim().length !== 6}
                          className="saas-btn-primary px-6 py-2.5 text-xs flex items-center justify-center gap-2 font-medium shrink-0 disabled:opacity-50"
                        >
                          {otpVerifying ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              Verifying Code...
                            </>
                          ) : (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              Verify mailbox
                            </>
                          )}
                        </button>
                      </form>

                      {otpError && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                          <XCircle className="w-4 h-4 shrink-0 text-red-600" />
                          <span>{otpError}</span>
                        </div>
                      )}

                      {otpSuccessMsg && (
                        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                          <span>{otpSuccessMsg}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {otpError && !otpSent && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                      <XCircle className="w-4 h-4 shrink-0 text-red-600" />
                      <span>{otpError}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 2-Column Deep Inspection: Verification Signals Checklist & Domain Intelligence */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Column 1: Individual Verification Signals Checklist */}
            <div className="saas-card p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <h3 className="text-sm font-bold text-navy-900 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-navy-700" />
                  Verification Signals Checklist
                </h3>
                <span className="text-xs text-slate-500">Automated Pipeline</span>
              </div>

              <div className="space-y-2.5 text-xs">
                {/* 1. Syntax */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.syntax.display_value)}
                    <span className="font-medium text-navy-900">Syntax</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.syntax.display_value)}`}>
                    {result.checks.syntax.display_value}
                  </span>
                </div>

                {/* 2. Domain */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.domain.display_value)}
                    <span className="font-medium text-navy-900">Domain</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.domain.display_value)}`}>
                    {result.checks.domain.display_value}
                  </span>
                </div>

                {/* 3. DNS */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.dns.display_value)}
                    <span className="font-medium text-navy-900">DNS</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.dns.display_value)}`}>
                    {result.checks.dns.display_value}
                  </span>
                </div>

                {/* 4. MX */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.mx.display_value)}
                    <span className="font-medium text-navy-900">MX</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.mx.display_value)}`}>
                    {result.checks.mx.display_value}
                  </span>
                </div>

                {/* 5. SMTP */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.smtp.display_value)}
                    <span className="font-medium text-navy-900">SMTP</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.smtp.display_value)}`}>
                    {result.checks.smtp.display_value}
                  </span>
                </div>

                {/* 6. Mailbox */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.mailbox.display_value)}
                    <span className="font-medium text-navy-900">Mailbox</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.mailbox.display_value)}`}>
                    {result.checks.mailbox.display_value}
                  </span>
                </div>

                {/* 7. Disposable */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.disposable.display_value)}
                    <span className="font-medium text-navy-900">Disposable</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.disposable.display_value)}`}>
                    {result.checks.disposable.display_value}
                  </span>
                </div>

                {/* 8. Role Based */}
                <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    {getCheckIcon(result.checks.role_based.display_value)}
                    <span className="font-medium text-navy-900">Role Based</span>
                  </div>
                  <span className={`px-2 py-0.5 font-mono font-bold rounded border text-[11px] ${getCheckTagStyle(result.checks.role_based.display_value)}`}>
                    {result.checks.role_based.display_value}
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
                  {/* Two-column summary metrics */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="saas-card-muted p-3">
                      <span className="text-slate-500 block mb-0.5">DNS Status</span>
                      <span className="font-semibold text-navy-900">
                        {result.domain_intelligence.is_resolvable ? 'Resolved (A/AAAA)' : 'Unresolved'}
                      </span>
                    </div>
                    <div className="saas-card-muted p-3">
                      <span className="text-slate-500 block mb-0.5">Mailbox Presence</span>
                      <span className="font-semibold text-navy-900">
                        {result.checks.mailbox?.display_value || 'UNCONFIRMED'}
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

                  {/* A Records list */}
                  {result.domain_intelligence.a_records.length > 0 && (
                    <div>
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">
                        Domain IP Addresses (A/AAAA)
                      </span>
                      <div className="flex flex-wrap gap-1.5 font-mono text-[11px]">
                        {result.domain_intelligence.a_records.map((ip, idx) => (
                          <span key={idx} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
                            {ip}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="p-3 bg-slate-50 border border-slate-200 rounded text-slate-600 leading-relaxed text-[11px]">
                    <span className="font-semibold text-navy-900">Verification Principle:</span> MailScope requires positive mailbox-level confirmation. Unconfirmed addresses remain <span className="font-semibold text-slate-800">UNKNOWN</span> until verified via confirmation code or direct server handshake.
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
