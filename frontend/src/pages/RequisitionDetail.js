import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiArrowLeft, FiDownload, FiTrash2, FiAlertCircle,
} from 'react-icons/fi';
import { getRequisition, deleteRequisition, API_BASE_URL } from '../services/api';

function RequisitionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      setData(await getRequisition(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm(`Delete ${data.pr_number}?\n\nThis cannot be undone.`)) return;
    setBusy(true);
    try {
      await deleteRequisition(id);
      navigate('/requisitions');
    } finally {
      setBusy(false);
    }
  };

  const handleDownload = () => {
    window.open(
      `${API_BASE_URL}/api/requisitions/${id}/export/word`,
      '_blank'
    );
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner-border text-primary" role="status" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="pro-card" style={{ borderLeft: '4px solid var(--danger)' }}>
        <div
          className="pro-card-body d-flex align-items-center gap-2"
          style={{ color: 'var(--danger)' }}
        >
          <FiAlertCircle /> {error}
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-start mb-4 flex-wrap gap-3">
        <div>
          <button
            className="btn btn-sm btn-outline-primary mb-2 d-flex align-items-center gap-1"
            onClick={() => navigate('/requisitions')}
          >
            <FiArrowLeft size={14} /> Back
          </button>
          <h1 className="page-title mb-1">{data.pr_number}</h1>
          <p className="page-subtitle">
            {data.company_name}
            {data.payment_type_name && ` · ${data.payment_type_name}`}
            {data.category_name && ` · ${data.category_name}`}
            {data.payee_name && ` · ${data.payee_name}`}
            {data.period && ` · ${data.period}`}
          </p>
        </div>
        <div className="d-flex gap-2 flex-wrap">
          <button
            className="btn btn-primary d-flex align-items-center gap-2"
            onClick={handleDownload}
          >
            <FiDownload size={16} /> Download Word
          </button>
          <button
            className="btn btn-outline-danger d-flex align-items-center gap-2"
            onClick={handleDelete}
            disabled={busy}
          >
            <FiTrash2 size={16} /> Delete
          </button>
        </div>
      </div>

      {/* Info cards */}
      <div className="row g-3 mb-4">
        <div className="col-md-8">
          <div className="pro-card" style={{ marginBottom: 0 }}>
            <div className="pro-card-header">
              <span>Requisition Info</span>
              <span className={`status-badge status-${data.status}`}>
                {data.status}
              </span>
            </div>
            <div className="pro-card-body">
              <div className="row g-3">
                <div className="col-md-4">
                  <b>Company</b>
                  <div>{data.company_name || '—'}</div>
                </div>
                <div className="col-md-4">
                  <b>Applicant</b>
                  <div>{data.applicant}</div>
                </div>
                <div className="col-md-4">
                  <b>Nature</b>
                  <div>{data.nature}</div>
                </div>
                <div className="col-md-4">
                  <b>Payment Type</b>
                  <div>{data.payment_type_name || '—'}</div>
                </div>
                <div className="col-md-4">
                  <b>Category</b>
                  <div>{data.category_name || '—'}</div>
                </div>
                <div className="col-md-4">
                  <b>Payee</b>
                  <div>{data.payee_name}</div>
                </div>
                {data.period && (
                  <div className="col-md-4">
                    <b>Period</b>
                    <div>{data.period}</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div
            className="pro-card"
            style={{
              marginBottom: 0,
              background: 'linear-gradient(135deg, #1a4d8f 0%, #0ea5e9 100%)',
              color: 'white',
              border: 'none',
            }}
          >
            <div className="pro-card-body">
              <div
                style={{
                  fontSize: '0.75rem',
                  opacity: 0.85,
                  textTransform: 'uppercase',
                  fontWeight: 600,
                  marginBottom: '0.5rem',
                }}
              >
                Total Amount
              </div>
              <div style={{ fontSize: '2rem', fontWeight: 700, lineHeight: 1 }}>
                HK$
                {data.total_amount.toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </div>
              <div
                style={{
                  fontSize: '0.75rem',
                  opacity: 0.85,
                  marginTop: '0.5rem',
                }}
              >
                {data.line_items?.length || 0} line items
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Line items */}
      <div className="pro-card">
        <div className="pro-card-header">
          <span>Line Items</span>
        </div>
        <table className="pro-table">
          <thead>
            <tr>
              <th style={{ width: 50 }}>#</th>
              <th style={{ width: 140 }}>Date</th>
              <th>Description</th>
              <th style={{ width: 220 }}>Category</th>
              <th style={{ width: 150, textAlign: 'right' }}>Amount (HKD)</th>
            </tr>
          </thead>
          <tbody>
            {data.line_items.map((li, idx) => (
              <tr key={li.id}>
                <td style={{ color: 'var(--neutral-500)', fontWeight: 500 }}>
                  {idx + 1}
                </td>
                <td>
                  {li.date
                    ? new Date(li.date).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })
                    : '—'}
                </td>
                <td style={{ color: 'var(--neutral-800)' }}>
                  {li.description}
                </td>
                <td>
                  {li.category ? (
                    <span
                      style={{
                        display: 'inline-block',
                        padding: '0.2rem 0.6rem',
                        background: 'var(--primary-light)',
                        color: 'var(--primary)',
                        borderRadius: 4,
                        fontSize: '0.75rem',
                        fontWeight: 500,
                      }}
                    >
                      {li.category}
                    </span>
                  ) : (
                    <span style={{ color: 'var(--neutral-400)' }}>—</span>
                  )}
                </td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>
                  ${(li.amount_hkd || 0).toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr style={{ background: 'var(--neutral-50)' }}>
              <td
                colSpan="4"
                style={{
                  textAlign: 'right',
                  fontWeight: 600,
                  padding: '1rem',
                }}
              >
                Total:
              </td>
              <td
                style={{
                  textAlign: 'right',
                  fontWeight: 700,
                  fontSize: '1.05rem',
                  color: 'var(--primary)',
                  padding: '1rem',
                }}
              >
                HK${data.total_amount.toFixed(2)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

export default RequisitionDetail;