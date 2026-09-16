import React, { useState, useEffect } from 'react';
import { 
  Search, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  Loader2, 
  RefreshCw, 
  ExternalLink,
  ShieldCheck,
  Globe,
  Server,
  Send,
  KeyRound,
  Clock
} from 'lucide-react';
import { verificationApi } from '../services/api';
import ScoreBar from '../components/ScoreBar';
import DetailDrawer from '../components/DetailDrawer';

export default function Overview({ onNavigateToVerify }) {
  const [emailInput, setEmailInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [quickResult, setQuickResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [stats, setStats] = useState(null);
  const [recentHistory, setRecentHistory] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Mailbox Verification OTP states
  const [otpInput, setOtpInput] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [otpSending, setOtpSending] = useState(false);
  const [otpVerifying, setOtpVerifying] = useState(false);
  const [otpError, setOtpError] = useState('');
  const [otpSuccessMsg, setOtpSuccessMsg] = useState('');
  const [cooldown, setCooldown] = useState(0);

  // Cooldown countdown effect
  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const loadData = async () => {
    const statsRes = await verificationApi.getStats();
    if (statsRes.data) setStats(statsRes.data);

    const histRes = await verificationApi.getHistory({ page: 1, pageSize: 6 });
    if (histRes.data) setRecentHistory(histRes.data.items || []);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleQuickVerify = async (e) => {
    if (e) e.preventDefault();
    if (!emailInput.trim()) {
      setErrorMsg('Please enter an email address.');
      return;
    }

    setErrorMsg('');
    setLoading(true);
    setQuickResult(null);
    setOtpSent(false);
    setOtpInput('');
    setOtpError('');
    setOtpSuccessMsg('');

    const res = await verificationApi.verifyEmail(emailInput.trim());
    setLoading(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setQuickResult(res.data);
      loadData(); // refresh metrics & recent history
    }
  };

  const handleSendOtp = async () => {
    if (!quickResult || !quickResult.email) return;
    setOtpSending(true);
    setOtpError('');
    setOtpSuccessMsg('');

    const res = await verificationApi.sendMailboxCode(quickResult.email);
    setOtpSending(false);

    if (res.error) {
      setOtpError(res.error);
    } else {
      setOtpSent(true);
      setOtpSuccessMsg(res.data.message || `Verification code sent to ${quickResult.email}`);
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

    if (!quickResult || !quickResult.email) return;

    setOtpVerifying(true);
    setOtpError('');

    const res = await verificationApi.verifyMailboxCode(quickResult.email, cleanCode);
    setOtpVerifying(false);

    if (res.error) {
      setOtpError(res.error);
    } else {
      setOtpSuccessMsg('✓ Mailbox verified successfully.');
      if (res.data.verification_result) {
        setQuickResult(res.data.verification_result);
      }
      loadData();
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full badge-valid"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>VALID</span>;
      case 'RISKY':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full badge-risky"><span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>RISKY</span>;
      case 'INVALID':
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full badge-invalid"><span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>INVALID</span>;
      default:
        return <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-semibold rounded-full badge-unknown"><span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>UNKNOWN</span>;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Verification Overview</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Monitor email deliverability signals, infrastructure DNS/MX health, and verification audits.
          </p>
        </div>
        <button
          onClick={loadData}
          className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh Stats
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="saas-card p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Total Verified</span>
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-bold text-navy-900">{stats?.total_verified ?? 0}</span>
            <span className="text-xs text-slate-500">records</span>
          </div>
        </div>

        <div className="saas-card p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Valid Rate</span>
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-bold text-navy-900">{stats?.valid_count ?? 0}</span>
            <span className="text-xs font-medium text-emerald-700">{stats?.valid_rate ?? 0}%</span>
          </div>
        </div>

        <div className="saas-card p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Risk Signals</span>
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-bold text-navy-900">{stats?.risky_count ?? 0}</span>
            <span className="text-xs text-amber-700">disposable / role</span>
          </div>
        </div>

        <div className="saas-card p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block mb-1">Invalid / Failed</span>
          <div className="flex items-baseline justify-between">
            <span className="font-mono text-2xl font-bold text-navy-900">{stats?.invalid_count ?? 0}</span>
            <span className="text-xs text-red-700">unresolvable</span>
          </div>
        </div>
      </div>

      {/* Quick Verification Form */}
      <div className="saas-card p-6">
        <div className="max-w-2xl">
          <h2 className="text-base font-bold text-navy-900">Verify an Email</h2>
          <p className="text-xs text-slate-600 mt-1 mb-4">
            Analyze syntax RFC compliance, domain DNS resolution, MX records, and risk signals.
          </p>

          <form onSubmit={handleQuickVerify} className="flex flex-col sm:flex-row gap-2.5">
            <div className="relative flex-1">
              <input
                type="text"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                placeholder="e.g. john.doe@company.com"
                className="saas-input w-full px-3.5 py-2 text-sm font-mono"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="saas-btn-primary px-5 py-2 text-sm flex items-center justify-center gap-2 shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                <>
                  Verify Email
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 rounded mt-3 flex items-center justify-between gap-2 text-xs text-red-700">
              <span>{errorMsg}</span>
              <button
                type="button"
                onClick={() => handleQuickVerify()}
                className="saas-btn-secondary px-2.5 py-1 text-xs text-navy-900 flex items-center gap-1 shrink-0"
              >
                <RefreshCw className="w-3 h-3" />
                Retry
              </button>
            </div>
          )}
        </div>

        {/* Quick Result Preview & Mailbox Verification Flow */}
        {quickResult && (
          <div className="mt-6 pt-6 border-t border-slate-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2 saas-card-muted p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs text-slate-500 uppercase tracking-wider font-semibold block mb-0.5">Verification Result</span>
                    <span className="font-mono text-base font-bold text-navy-900 break-all">{quickResult.email}</span>
                  </div>
                  {getStatusBadge(quickResult.status)}
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-200 text-xs">
                  <div>
                    <span className="text-slate-500 block">Syntax</span>
                    <span className="font-semibold text-navy-900">{quickResult.checks?.syntax?.passed ? 'Passed' : 'Failed'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Domain DNS</span>
                    <span className="font-semibold text-navy-900">{quickResult.checks?.dns?.passed ? 'Resolved' : 'Failed'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">MX Mail Server</span>
                    <span className="font-semibold text-navy-900">{quickResult.checks?.mx?.passed ? 'Found' : 'None'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Mailbox Status</span>
                    <span className={`font-semibold ${
                      quickResult.checks?.mailbox?.display_value === 'CONFIRMED' || quickResult.status === 'VALID'
                        ? 'text-emerald-700'
                        : 'text-amber-700'
                    }`}>
                      {quickResult.checks?.mailbox?.display_value || quickResult.domain_intelligence?.mailbox_status || 'UNCONFIRMED'}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-700 bg-white p-2.5 rounded border border-slate-200">
                  {quickResult.message}
                </p>
              </div>

              <div className="flex flex-col justify-between">
                <ScoreBar confidence={quickResult.confidence || quickResult.score} status={quickResult.status} />
              </div>
            </div>

            {/* Mailbox Ownership Verification Challenge Card */}
            <div className="p-4 bg-white border border-slate-200 rounded-lg shadow-xs space-y-3 border-l-4 border-l-navy-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <h3 className="text-sm font-bold text-navy-900 flex items-center gap-2">
                    <KeyRound className="w-4 h-4 text-navy-800" />
                    Mailbox Ownership & Access Verification
                  </h3>
                  <p className="text-xs text-slate-600">
                    Verify whether this particular inbox is accessible using a secure 6-digit confirmation code.
                  </p>
                </div>

                {(quickResult.checks?.mailbox?.display_value === 'CONFIRMED' || quickResult.status === 'VALID') && (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 self-start sm:self-auto">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    Mailbox Verified
                  </span>
                )}
              </div>

              {quickResult.checks?.mailbox?.display_value === 'CONFIRMED' || quickResult.status === 'VALID' ? (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 flex items-center justify-between">
                  <div className="flex items-center gap-2 font-medium">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    ✓ Mailbox verified &bull; ✓ Verification code confirmed &bull; VALID (100/100)
                  </div>
                </div>
              ) : quickResult.status === 'INVALID' ? (
                <div className="p-3 bg-slate-50 border border-slate-200 rounded text-xs text-slate-500">
                  Mailbox code verification is unavailable for invalid email addresses or domains.
                </div>
              ) : (
                <div className="space-y-3 pt-1">
                  {!otpSent ? (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 bg-slate-50 border border-slate-200 rounded">
                      <div className="text-xs text-slate-600">
                        <strong className="text-navy-900 block">Mailbox verification required</strong>
                        Click below to dispatch a secure 6-digit one-time code to <span className="font-mono font-bold text-navy-900">{quickResult.email}</span>.
                      </div>
                      <button
                        type="button"
                        onClick={handleSendOtp}
                        disabled={otpSending}
                        className="saas-btn-primary px-4 py-2 text-xs flex items-center justify-center gap-2 shrink-0 font-medium"
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
                    <div className="space-y-3 p-3.5 bg-slate-50 border border-slate-200 rounded">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                        <span className="text-slate-700">
                          Verification code sent to <strong className="font-mono text-navy-900">{quickResult.email}</strong> (expires in 10m).
                        </span>
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

                      <form onSubmit={handleVerifyOtp} className="flex flex-col sm:flex-row gap-2.5 items-stretch sm:items-center">
                        <input
                          type="text"
                          maxLength={6}
                          value={otpInput}
                          onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ''))}
                          placeholder="Enter 6-digit code"
                          className="saas-input px-3 py-2 text-sm font-mono tracking-widest text-center w-full sm:w-48"
                          autoFocus
                        />
                        <button
                          type="submit"
                          disabled={otpVerifying || otpInput.trim().length !== 6}
                          className="saas-btn-primary px-5 py-2 text-xs flex items-center justify-center gap-2 font-medium shrink-0 disabled:opacity-50"
                        >
                          {otpVerifying ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              Verifying...
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
                        <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                          <XCircle className="w-4 h-4 shrink-0 text-red-600" />
                          <span>{otpError}</span>
                        </div>
                      )}

                      {otpSuccessMsg && (
                        <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded text-xs text-emerald-800 flex items-center gap-2">
                          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                          <span>{otpSuccessMsg}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {otpError && !otpSent && (
                    <div className="p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-center gap-2">
                      <XCircle className="w-4 h-4 shrink-0 text-red-600" />
                      <span>{otpError}</span>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Recent Verifications Table */}
      <div className="saas-card overflow-hidden">
        <div className="p-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-navy-900">Recent Verifications</h3>
            <p className="text-xs text-slate-500">Live inspection records from verification pipeline</p>
          </div>
          <button
            onClick={() => onNavigateToVerify('history')}
            className="text-xs text-navy-700 font-semibold hover:underline flex items-center gap-1"
          >
            View all history
            <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {recentHistory.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <ShieldCheck className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-navy-900">No verifications yet</p>
            <p className="text-xs text-slate-500 mt-0.5">Enter an email address above to run your first verification check.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Email Address</th>
                  <th className="py-3 px-4">Domain</th>
                  <th className="py-3 px-4">Result</th>
                  <th className="py-3 px-4 text-center">Score</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentHistory.map((item) => (
                  <tr 
                    key={item.id} 
                    className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedItem(item);
                      setDrawerOpen(true);
                    }}
                  >
                    <td className="py-3 px-4 font-mono font-medium text-navy-900 max-w-xs truncate">{item.email}</td>
                    <td className="py-3 px-4 font-mono text-slate-600">{item.domain}</td>
                    <td className="py-3 px-4">{getStatusBadge(item.status)}</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-navy-900">{item.score}</td>
                    <td className="py-3 px-4 text-slate-500">{new Date(item.created_at).toLocaleDateString()}</td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-xs text-navy-700 font-medium hover:underline">Inspect</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Slide-out detail drawer */}
      <DetailDrawer
        item={selectedItem}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
