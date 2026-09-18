import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 45000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const getErrorMessage = (err) => {
  if (err.response?.data?.detail) {
    return err.response.data.detail;
  }
  if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
    return 'Verification request timed out. Mailbox status categorized as UNKNOWN.';
  }
  if (err.message === 'Network Error' || !err.response) {
    return 'Verification service is temporarily unavailable. Please verify the backend server is running.';
  }
  return err.message || 'Unable to complete email verification.';
};

export const verificationApi = {
  // Single email verify
  verifyEmail: async (email) => {
    try {
      const response = await api.post('/verify', { email });
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Batch verify
  batchVerifyEmails: async (emails) => {
    try {
      const response = await api.post('/verify/batch', { emails });
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Extract emails from PDF / Word document
  extractEmailsFromDocument: async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await api.post('/extract-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Export batch verification results (csv, xlsx, pdf)
  exportBatchResults: async (results, format = 'csv') => {
    try {
      const response = await api.post(`/export/batch?format=${format}`, results, {
        responseType: 'blob',
      });
      
      const mimeTypes = {
        csv: 'text/csv',
        xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        pdf: 'application/pdf'
      };
      
      const blob = new Blob([response.data], { type: mimeTypes[format] || 'application/octet-stream' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `mailscope_batch_audit.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      return { success: true, error: null };
    } catch (err) {
      return { success: false, error: getErrorMessage(err) };
    }
  },

  // Get verification history
  getHistory: async ({ page = 1, pageSize = 20, status = null, search = null } = {}) => {
    try {
      const params = { page, page_size: pageSize };
      if (status && status !== 'ALL') params.status = status;
      if (search && search.trim()) params.search = search.trim();

      const response = await api.get('/history', { params });
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Clear history
  clearHistory: async () => {
    try {
      const response = await api.delete('/history');
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Get statistics
  getStats: async () => {
    try {
      const response = await api.get('/stats');
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },

  // Health check
  checkHealth: async () => {
    try {
      const response = await api.get('/health');
      return { data: response.data, error: null };
    } catch (err) {
      return { data: null, error: getErrorMessage(err) };
    }
  },
};
