import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Trash2, 
  Download, 
  RefreshCw, 
  ChevronLeft, 
  ChevronRight, 
  AlertCircle,
  Clock,
  ExternalLink
} from 'lucide-react';
import { verificationApi } from '../services/api';
import DetailDrawer from '../components/DetailDrawer';

export default function History() {
  const [historyData, setHistoryData] = useState({ total: 0, items: [], page: 1, page_size: 15 });
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [clearing, setClearing] = useState(false);

  const fetchHistory = async (page = 1) => {
    setLoading(true);
    const res = await verificationApi.getHistory({
      page,
      pageSize: 15,
      status: statusFilter !== 'ALL' ? statusFilter : null,
      search: searchQuery.trim() || null,
    });
    setLoading(false);

    if (res.data) {
      setHistoryData(res.data);
    }
  };

  useEffect(() => {
    fetchHistory(1);
  }, [statusFilter]);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchHistory(1);
  };

  const handleClearHistory = async () => {
    setClearing(true);
    await verificationApi.clearHistory();
    setClearing(false);
    setShowClearConfirm(false);
    fetchHistory(1);
  };

  const handleExportCSV = () => {
    if (!historyData.items || historyData.items.length === 0) return;

    const headers = ['Email', 'Normalized', 'Domain', 'Status', 'Score', 'Syntax Valid', 'Domain Resolved', 'MX Found', 'Disposable', 'Role Based', 'Date'];
    const rows = historyData.items.map(item => [
      item.email,
      item.normalized_email,
      item.domain,
      item.status,
      item.score,
      item.is_syntax_valid ? 'YES' : 'NO',
      item.is_domain_resolved ? 'YES' : 'NO',
      item.is_mx_found ? 'YES' : 'NO',
      item.is_disposable ? 'YES' : 'NO',
      item.is_role_based ? 'YES' : 'NO',
      new Date(item.created_at).toISOString()
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `openmail_history_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

  const totalPages = Math.ceil(historyData.total / historyData.page_size) || 1;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold text-navy-900 tracking-tight">Verification Audit History</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Full persistent audit log stored locally in SQLite database.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {historyData.total > 0 && (
            <>
              <button
                onClick={handleExportCSV}
                className="saas-btn-secondary px-3 py-1.5 text-xs flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                Export
              </button>
              <button
                onClick={() => setShowClearConfirm(true)}
                className="saas-btn-secondary px-3 py-1.5 text-xs text-red-600 hover:text-red-700 hover:border-red-300 flex items-center gap-1.5"
              >
                <Trash2 className="w-3.5 h-3.5" />
                Clear History
              </button>
            </>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="saas-card p-4 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Status filter tabs */}
        <div className="flex items-center gap-1 w-full md:w-auto overflow-x-auto pb-1 md:pb-0">
          {['ALL', 'VALID', 'RISKY', 'INVALID', 'UNKNOWN'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-xs font-semibold rounded transition-colors ${
                statusFilter === status
                  ? 'bg-navy-800 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Search Input */}
        <form onSubmit={handleSearch} className="flex items-center gap-2 w-full md:w-80">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search email or domain..."
              className="saas-input w-full pl-8 pr-3 py-1.5 text-xs font-mono"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          </div>
          <button type="submit" className="saas-btn-primary px-3 py-1.5 text-xs">
            Filter
          </button>
        </form>
      </div>

      {/* Table Card */}
      <div className="saas-card overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            Loading verification history...
          </div>
        ) : historyData.items.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Clock className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-navy-900">No verification history yet</p>
            <p className="text-xs text-slate-500 mt-0.5">Run email checks to generate audit logs.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Email Address</th>
                  <th className="py-3 px-4">Domain</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-center">Score</th>
                  <th className="py-3 px-4">Checks</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {historyData.items.map((item) => (
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
                    <td className="py-3 px-4 text-slate-600">
                      <span className="space-x-2">
                        <span className={item.is_syntax_valid ? 'text-emerald-700' : 'text-red-700'}>Syntax</span>
                        <span>•</span>
                        <span className={item.is_domain_resolved ? 'text-emerald-700' : 'text-red-700'}>DNS</span>
                        <span>•</span>
                        <span className={item.is_mx_found ? 'text-emerald-700' : 'text-red-700'}>MX</span>
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-xs text-navy-700 font-medium hover:underline">View</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination bar */}
        {historyData.total > 0 && (
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex items-center justify-between text-xs">
            <span className="text-slate-600">
              Showing <span className="font-semibold text-navy-900">{historyData.items.length}</span> of <span className="font-semibold text-navy-900">{historyData.total}</span> entries
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchHistory(historyData.page - 1)}
                disabled={historyData.page <= 1}
                className="saas-btn-secondary px-2.5 py-1 text-xs disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Previous
              </button>
              <span className="font-mono text-slate-700">
                Page {historyData.page} of {totalPages}
              </span>
              <button
                onClick={() => fetchHistory(historyData.page + 1)}
                disabled={historyData.page >= totalPages}
                className="saas-btn-secondary px-2.5 py-1 text-xs disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Confirmation Modal for Clear History */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-navy-900/40 backdrop-blur-xs">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full border border-slate-200 shadow-xl space-y-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-navy-900">Clear Verification History?</h4>
                <p className="text-xs text-slate-600 mt-1">
                  This will permanently delete all verification logs stored in the local SQLite database. This action cannot be undone.
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="saas-btn-secondary px-3.5 py-1.5 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleClearHistory}
                disabled={clearing}
                className="bg-red-700 hover:bg-red-800 text-white font-medium rounded-md px-3.5 py-1.5 text-xs"
              >
                {clearing ? 'Clearing...' : 'Confirm Clear'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Detail Drawer */}
      <DetailDrawer
        item={selectedItem}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
