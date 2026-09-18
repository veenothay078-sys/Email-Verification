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
  RotateCcw,
  UploadCloud,
  FileText,
  Search,
  Trash2,
  FileCheck,
  Check,
  FileType
} from 'lucide-react';
import { verificationApi } from '../services/api';
import DetailDrawer from '../components/DetailDrawer';

export default function BatchAudit() {
  const [sourceMode, setSourceMode] = useState('paste'); // 'paste' | 'upload'
  const [emailsText, setEmailsText] = useState('');
  
  // Document Upload State
  const [dragActive, setDragActive] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [extractedData, setExtractedData] = useState(null); // { filename, total_found, unique_count, duplicates_count, emails: [] }
  
  // Verification Pipeline State
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Progress tracking
  const [progressState, setProgressState] = useState({
    currentEmail: '',
    completed: 0,
    total: 0,
    realCount: 0,
    invalidCount: 0,
    unknownCount: 0,
    pendingCount: 0
  });

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

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = async (file) => {
    const filename = file.name;
    const ext = filename.toLowerCase().split('.').pop();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      setErrorMsg(`Unsupported file type '.${ext}'. Supported formats: .pdf, .docx, .doc`);
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMsg('File size exceeds maximum limit of 10 MB.');
      return;
    }

    setErrorMsg('');
    setUploadingDoc(true);
    setBatchResult(null);

    const res = await verificationApi.extractEmailsFromDocument(file);
    setUploadingDoc(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setExtractedData(res.data);
    }
  };

  const handleRemoveExtractedEmail = (emailToRemove) => {
    if (!extractedData) return;
    const updatedEmails = extractedData.emails.filter(e => e !== emailToRemove);
    setExtractedData({
      ...extractedData,
      unique_count: updatedEmails.length,
      emails: updatedEmails
    });
  };

  const handleClearDoc = () => {
    setExtractedData(null);
    setErrorMsg('');
  };

  // Start Batch Verification
  const executeBatchVerification = async (targetEmailList) => {
    if (!targetEmailList || targetEmailList.length === 0) {
      setErrorMsg('Please provide at least one email address.');
      return;
    }

    if (targetEmailList.length > 100) {
      setErrorMsg('Too many email addresses. Maximum allowed: 100.');
      return;
    }

    setErrorMsg('');
    setLoading(true);
    setBatchResult(null);

    // Setup Controlled Concurrency Processing & Progress Simulation
    const totalCount = targetEmailList.length;
    setProgressState({
      currentEmail: targetEmailList[0] || '',
      completed: 0,
      total: totalCount,
      realCount: 0,
      invalidCount: 0,
      unknownCount: 0,
      pendingCount: totalCount
    });

    const res = await verificationApi.batchVerifyEmails(targetEmailList);
    setLoading(false);

    if (res.error) {
      setErrorMsg(res.error);
    } else {
      setBatchResult(res.data);
    }
  };

  const handleStartManualBatch = () => {
    const rawList = emailsText
      .split(/[\n,]+/)
      .map(e => e.trim())
      .filter(e => e.length > 0);
    executeBatchVerification(rawList);
  };

  const handleStartDocBatch = () => {
    if (!extractedData || !extractedData.emails) return;
    executeBatchVerification(extractedData.emails);
  };

  const handleExport = async (fmt) => {
    if (!batchResult || !batchResult.results) return;
    await verificationApi.exportBatchResults(batchResult.results, fmt);
  };

  const getStatusBadge = (item) => {
    const status = item.final_status || item.classification || item.status;
    if (status === 'REAL / REACHABLE' || status === 'REAL' || status === 'VALID') {
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-full badge-valid"><span className="w-1.5 h-1.5 rounded-full bg-emerald-600"></span>REAL / VALID</span>;
    } else if (status === 'NOT REAL / INVALID' || status === 'INVALID') {
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-full badge-invalid"><span className="w-1.5 h-1.5 rounded-full bg-red-600"></span>NOT REAL / INVALID</span>;
    } else if (status === 'RISKY') {
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-full badge-risky"><span className="w-1.5 h-1.5 rounded-full bg-amber-600"></span>RISKY</span>;
    } else {
      return <span className="inline-flex items-center gap-1 px-2.5 py-0.5 text-xs font-bold rounded-full badge-unknown"><span className="w-1.5 h-1.5 rounded-full bg-slate-500"></span>UNKNOWN</span>;
    }
  };

  const filteredResults = batchResult?.results?.filter(item => {
    const itemStatus = item.final_status || item.classification || item.status;
    const matchesFilter = statusFilter === 'ALL' || 
      (statusFilter === 'REAL' && (itemStatus.includes('REAL') || itemStatus === 'VALID')) ||
      (statusFilter === 'INVALID' && (itemStatus.includes('INVALID'))) ||
      (statusFilter === 'UNKNOWN' && (itemStatus === 'UNKNOWN')) ||
      (statusFilter === 'RISKY' && (itemStatus === 'RISKY'));

    const matchesSearch = !searchQuery.trim() || 
      item.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (item.domain && item.domain.toLowerCase().includes(searchQuery.toLowerCase()));

    return matchesFilter && matchesSearch;
  }) || [];

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="pb-2 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Batch Email Audit</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Verify list of email addresses via direct PDF/Word extraction or manual input using non-contact SMTP.
          </p>
        </div>
      </div>

      {/* Bulk Email Source Selector */}
      <div className="saas-card p-6 space-y-6">
        <div>
          <label className="text-xs font-bold uppercase tracking-wider text-slate-500 block mb-2">
            BULK EMAIL SOURCE
          </label>
          <p className="text-xs text-slate-600 mb-3">
            Choose how you want to provide email addresses for verification:
          </p>
          
          <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200">
            <button
              type="button"
              onClick={() => setSourceMode('paste')}
              className={`px-4 py-2 text-xs font-bold rounded-md transition-all flex items-center gap-2 ${
                sourceMode === 'paste'
                  ? 'bg-navy-800 text-white shadow-sm'
                  : 'text-slate-600 hover:text-navy-900 hover:bg-slate-200/60'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              Paste Emails
            </button>
            <button
              type="button"
              onClick={() => setSourceMode('upload')}
              className={`px-4 py-2 text-xs font-bold rounded-md transition-all flex items-center gap-2 ${
                sourceMode === 'upload'
                  ? 'bg-navy-800 text-white shadow-sm'
                  : 'text-slate-600 hover:text-navy-900 hover:bg-slate-200/60'
              }`}
            >
              <FileType className="w-3.5 h-3.5" />
              Upload PDF / Word
            </button>
          </div>
        </div>

        {/* MODE 1: Manual Paste Emails */}
        {sourceMode === 'paste' && (
          <div className="space-y-4 pt-2 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-700">
                Enter Email Addresses (One per line or comma separated)
              </label>
              <button
                type="button"
                onClick={() => setEmailsText(sampleBatch)}
                className="text-xs text-navy-700 font-semibold hover:underline flex items-center gap-1"
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
              <div className="text-xs text-slate-500 font-mono">
                {emailsText.split(/[\n,]+/).filter(e => e.trim().length > 0).length} / 100 emails entered
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
                  onClick={handleStartManualBatch}
                  disabled={loading}
                  className="saas-btn-primary px-5 py-2 text-xs flex items-center gap-2 font-bold"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Executing Audit...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-3.5 h-3.5" />
                      START BATCH VERIFICATION
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODE 2: PDF / Word Document Upload */}
        {sourceMode === 'upload' && (
          <div className="space-y-4 pt-2 border-t border-slate-100">
            {!extractedData ? (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                  dragActive ? 'border-navy-700 bg-slate-50' : 'border-slate-300 hover:border-slate-400 bg-white'
                }`}
              >
                <input
                  type="file"
                  id="doc-upload-input"
                  accept=".pdf,.docx,.doc"
                  onChange={handleFileSelect}
                  className="hidden"
                />

                <div className="flex flex-col items-center justify-center space-y-3">
                  <div className="p-3 bg-navy-50 text-navy-800 rounded-full">
                    {uploadingDoc ? (
                      <Loader2 className="w-8 h-8 animate-spin" />
                    ) : (
                      <UploadCloud className="w-8 h-8" />
                    )}
                  </div>

                  <div>
                    <p className="text-sm font-bold text-navy-900">
                      {uploadingDoc ? 'Parsing Document & Extracting Email IDs...' : 'Drag & Drop your document here'}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Supported formats: <span className="font-semibold text-slate-700">PDF (.pdf) • Word (.docx, .doc)</span> (Max 10 MB)
                    </p>
                  </div>

                  {!uploadingDoc && (
                    <label
                      htmlFor="doc-upload-input"
                      className="saas-btn-secondary px-4 py-2 text-xs font-bold cursor-pointer inline-flex items-center gap-2"
                    >
                      <FileSpreadsheet className="w-4 h-4 text-navy-700" />
                      Browse Files
                    </label>
                  )}
                </div>
              </div>
            ) : (
              /* Extraction Summary & Preview Card */
              <div className="space-y-6">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-200">
                    <div className="flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-emerald-600" />
                      <span className="font-bold text-sm text-navy-900">Document Uploaded Successfully</span>
                    </div>
                    <button
                      type="button"
                      onClick={handleClearDoc}
                      className="text-xs font-semibold text-red-600 hover:underline flex items-center gap-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      REMOVE FILE
                    </button>
                  </div>

                  {/* Extraction Stats Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">FILE</span>
                      <span className="font-mono text-xs font-bold text-navy-900 truncate block">{extractedData.filename}</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">EMAILS FOUND</span>
                      <span className="font-mono text-sm font-bold text-navy-900">{extractedData.total_found}</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">UNIQUE EMAILS</span>
                      <span className="font-mono text-sm font-bold text-emerald-700">{extractedData.unique_count}</span>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200">
                      <span className="text-[10px] uppercase font-bold text-slate-500 block">DUPLICATES</span>
                      <span className="font-mono text-sm font-bold text-amber-700">{extractedData.duplicates_count}</span>
                    </div>
                  </div>
                </div>

                {/* Email Preview List */}
                <div className="border border-slate-200 rounded-xl overflow-hidden">
                  <div className="p-3 bg-slate-100 border-b border-slate-200 flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                      EXTRACTED UNIQUE EMAILS ({extractedData.emails.length})
                    </span>
                    <span className="text-xs text-slate-500">
                      Review extracted email list before starting verification
                    </span>
                  </div>

                  <div className="max-h-60 overflow-y-auto divide-y divide-slate-100 font-mono text-xs bg-white">
                    {extractedData.emails.map((emailItem, idx) => (
                      <div key={idx} className="px-4 py-2 flex items-center justify-between hover:bg-slate-50">
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 text-[11px] w-6 text-right">{idx + 1}.</span>
                          <span className="font-semibold text-navy-900">{emailItem}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveExtractedEmail(emailItem)}
                          className="text-slate-400 hover:text-red-600 transition-colors p-1"
                          title="Remove email from list"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={handleClearDoc}
                    className="saas-btn-secondary px-4 py-2 text-xs flex items-center gap-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-red-500" />
                    REMOVE FILE
                  </button>

                  <button
                    type="button"
                    onClick={handleStartDocBatch}
                    disabled={loading || extractedData.emails.length === 0}
                    className="saas-btn-primary px-6 py-2 text-xs flex items-center gap-2 font-bold"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Processing Batch...
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        START BATCH VERIFICATION
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-xs font-semibold text-red-700 flex items-center gap-2">
            <XCircle className="w-4 h-4 shrink-0 text-red-600" />
            <span>{errorMsg}</span>
          </div>
        )}
      </div>

      {/* Live Loading Bar State */}
      {loading && (
        <div className="saas-card p-6 space-y-4 border-l-4 border-navy-800">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-navy-900 uppercase tracking-wider">
                BATCH VERIFICATION IN PROGRESS
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Probing email mailboxes via non-contact SMTP (concurrency limit: 3).
              </p>
            </div>
            <span className="font-mono text-sm font-bold text-navy-800">
              {progressState.completed} / {progressState.total} completed
            </span>
          </div>

          <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden">
            <div 
              className="bg-navy-800 h-full transition-all duration-300 rounded-full animate-pulse"
              style={{ width: `${progressState.total > 0 ? Math.round((progressState.completed / progressState.total) * 100) : 50}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Batch Results Section */}
      {batchResult && (
        <div className="space-y-6">
          {/* Summary Row */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Total Audited</span>
              <span className="font-mono text-xl font-bold text-navy-900">{batchResult.total}</span>
            </div>
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">REAL / VALID</span>
              <span className="font-mono text-xl font-bold text-emerald-700">{batchResult.valid_count}</span>
            </div>
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">INVALID</span>
              <span className="font-mono text-xl font-bold text-red-700">{batchResult.invalid_count}</span>
            </div>
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">UNKNOWN</span>
              <span className="font-mono text-xl font-bold text-slate-600">{batchResult.unknown_count}</span>
            </div>
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">RISKY</span>
              <span className="font-mono text-xl font-bold text-amber-700">{batchResult.risky_count}</span>
            </div>
            <div className="saas-card p-3.5">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">PROCESSED</span>
              <span className="font-mono text-xl font-bold text-navy-900">{batchResult.total} / {batchResult.total}</span>
            </div>
          </div>

          {/* Results Table Card */}
          <div className="saas-card overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4">
              {/* Filter Tabs */}
              <div className="flex items-center gap-1.5 flex-wrap">
                {['ALL', 'REAL', 'INVALID', 'UNKNOWN', 'RISKY'].map(status => (
                  <button
                    key={status}
                    onClick={() => setStatusFilter(status)}
                    className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                      statusFilter === status
                        ? 'bg-navy-800 text-white shadow-sm'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {status}
                  </button>
                ))}
              </div>

              {/* Search & Multi-Format Exports */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    placeholder="Search email..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="saas-input pl-8 pr-3 py-1.5 text-xs w-full sm:w-48 font-mono"
                  />
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => handleExport('csv')}
                    className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1 font-semibold"
                    title="Export CSV"
                  >
                    <Download className="w-3.5 h-3.5" />
                    CSV
                  </button>
                  <button
                    onClick={() => handleExport('xlsx')}
                    className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1 font-semibold"
                    title="Export Excel (XLSX)"
                  >
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-700" />
                    XLSX
                  </button>
                  <button
                    onClick={() => handleExport('pdf')}
                    className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1 font-semibold"
                    title="Export PDF Report"
                  >
                    <FileType className="w-3.5 h-3.5 text-red-600" />
                    PDF
                  </button>
                </div>
              </div>
            </div>

            {/* Main Verification Results Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">EMAIL</th>
                    <th className="py-3 px-4">DOMAIN</th>
                    <th className="py-3 px-4 text-center">SYNTAX</th>
                    <th className="py-3 px-4 text-center">MX</th>
                    <th className="py-3 px-4 text-center">SMTP</th>
                    <th className="py-3 px-4">RESULT</th>
                    <th className="py-3 px-4">REASON</th>
                    <th className="py-3 px-4 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {filteredResults.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500 font-sans">
                        No verification results match current search / filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredResults.map((item, idx) => (
                      <tr 
                        key={idx}
                        className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                        onClick={() => {
                          setSelectedItem({
                            ...item,
                            is_syntax_valid: item.checks?.syntax?.passed ?? item.syntax_valid,
                            is_domain_resolved: item.checks?.dns?.passed ?? item.dns_resolved,
                            is_mx_found: item.checks?.mx?.passed ?? item.mx_found,
                            is_disposable: !(item.checks?.disposable?.passed) ?? item.disposable_detected,
                            is_role_based: !(item.checks?.role_based?.passed) ?? item.role_account_detected,
                          });
                          setDrawerOpen(true);
                        }}
                      >
                        <td className="py-3 px-4 font-medium text-navy-900 max-w-xs truncate">{item.email}</td>
                        <td className="py-3 px-4 text-slate-600">{item.domain || '-'}</td>
                        <td className="py-3 px-4 text-center font-sans">
                          {item.checks?.syntax?.passed ?? item.syntax_valid ? (
                            <span className="text-emerald-700 font-bold">PASS</span>
                          ) : (
                            <span className="text-red-700 font-bold">FAIL</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center font-sans">
                          {item.checks?.mx?.passed ?? item.mx_found ? (
                            <span className="text-emerald-700 font-bold">FOUND</span>
                          ) : (
                            <span className="text-red-700 font-bold">NOT FOUND</span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-center font-sans">
                          <span className="font-semibold text-slate-700">
                            {item.checks?.smtp?.display_value || item.smtp_connection_status || 'PROBED'}
                          </span>
                        </td>
                        <td className="py-3 px-4 font-sans">{getStatusBadge(item)}</td>
                        <td className="py-3 px-4 font-sans text-slate-500 max-w-xs truncate">
                          {item.reason || item.message}
                        </td>
                        <td className="py-3 px-4 text-right font-sans">
                          <span className="text-xs text-navy-700 font-bold hover:underline">Inspect</span>
                        </td>
                      </tr>
                    ))
                  )}
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
