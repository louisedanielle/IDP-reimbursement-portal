import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 120000,   
});

// ---------- Lookups ----------
export const getCategories = async () => {
  const { data } = await api.get('/api/categories');
  return data.categories;
};

export const getCompanies = async () => {
  const { data } = await api.get('/api/companies');
  return data;
};

export const getCompanyCategories = async (companyId) => {
  const { data } = await api.get(`/api/companies/${companyId}/categories`);
  return data;   // { "Monthly Payment": [...], ... }
};

export const createNature = async (companyId, name, paymentType) => {
  const { data } = await api.post(`/api/companies/${companyId}/categories`, {
    name,
    payment_type: paymentType,
  });
  return data;
};

export const getPayees = async () => {
  const { data } = await api.get('/api/payees');
  return data;
};

export const createPayee = async (name) => {
  const { data } = await api.post('/api/payees', { name });
  return data;
};

// ---------- Documents ----------
export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const listDocuments = async () => {
  const { data } = await api.get('/api/documents');
  return data;
};

export const getDocumentStatus = async (docId) => {
  const { data } = await api.get(`/api/documents/${docId}/status`);
  return data;
};

export const getExtractedData = async (docId) => {
  const { data } = await api.get(`/api/documents/${docId}/extracted`);
  return data;
};

export const getSuggestions = async (docId) => {
  const { data } = await api.get(`/api/documents/${docId}/suggestions`);
  return data;
};

export const saveReview = async (docId, payload) => {
  // payload = { items, company_id, payment_category_id, payee_name, period }
  const { data } = await api.post(`/api/documents/${docId}/review`, payload);
  return data;
};

export const reprocessDocument = async (docId) => {
  const { data } = await api.post(`/api/documents/${docId}/reprocess`);
  return data;
};

// ---------- Dashboard ----------
export const getDashboardStats = async () => {
  const { data } = await api.get('/api/dashboard/stats');
  return data;
};

// ---------- Requisitions ----------
export const listRequisitions = async (params = {}) => {
  const { data } = await api.get('/api/requisitions', { params });
  return data;
};

export const getFolderView = async (params = {}) => {
  const { data } = await api.get('/api/requisitions/folders', { params });
  return data;
};

export const getRequisition = async (id) => {
  const { data } = await api.get(`/api/requisitions/${id}`);
  return data;
};

export const deleteRequisition = async (id) => {
  const { data } = await api.delete(`/api/requisitions/${id}`);
  return data;
};

export default api;