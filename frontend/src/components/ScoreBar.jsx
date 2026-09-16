import React from 'react';
import { Info } from 'lucide-react';

export default function ScoreBar({ score = 0, confidence, status = 'VALID' }) {
  const displayScore = confidence !== undefined ? confidence : score;
  
  // Determine color theme based on score & status
  let barColor = 'bg-navy-800';
  let statusText = 'Email passed the available technical and mailbox verification checks.';

  if (status === 'INVALID' || displayScore === 0) {
    barColor = 'bg-red-700';
    statusText = 'Technical verification found evidence that this email address is invalid.';
  } else if (status === 'RISKY') {
    barColor = 'bg-amber-600';
    statusText = 'Email appears technically valid but contains one or more risk signals.';
  } else if (status === 'UNKNOWN') {
    barColor = 'bg-slate-500';
    statusText = 'The email infrastructure is valid, but mailbox existence could not be reliably confirmed.';
  }

  return (
    <div className="saas-card p-5">
      <div className="flex items-baseline justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-navy-600">Verification Confidence</span>
          <div className="group relative cursor-pointer text-slate-400 hover:text-navy-800">
            <Info className="w-3.5 h-3.5" />
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-64 p-2 bg-navy-900 text-white text-xs rounded shadow-lg z-20">
              Confidence level calculated from syntax, DNS resolution, MX records, and mail server verification.
            </div>
          </div>
        </div>
        <span className="font-mono text-2xl font-bold text-navy-900">{displayScore}<span className="text-sm font-normal text-slate-400">/100</span></span>
      </div>

      {/* Structured progress track */}
      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden mb-2.5">
        <div
          className={`h-full transition-all duration-300 ${barColor}`}
          style={{ width: `${Math.min(Math.max(displayScore, 0), 100)}%` }}
        />
      </div>

      <p className="text-xs text-slate-600 leading-relaxed">{statusText}</p>
    </div>
  );
}
