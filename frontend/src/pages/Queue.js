import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiInbox, FiRefreshCw, FiArrowRight, FiCheck, FiX, FiLoader, FiFolder } from 'react-icons/fi';
import api from '../services/api';

function Queue() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const loadDocuments = async () => {
    try {
      const { data } = await api.get('/api/documents');
      setDocuments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    // Auto-refresh every 5 seconds
    const interval = setInterval(loadDocuments, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadDocuments();
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <FiCheck size={18} style={{ color: 'var(--success)' }} />;
      case 'failed':
        return <FiX size={18} style={{ color: 'var(--danger)' }} />;
      case 'processing':
        return <FiLoader size={18} className="spin" style={{ color: 'var(--primary)' }} />;
      default:
        return <FiFolder size={18} style={{ color: 'var(--neutral-400)' }} />;
    }
  };

  const getStatusText = (status) => {
    const map = {
      pending: 'Waiting in queue',
      processing: 'Extracting with AI...',
      completed: 'Ready for review',
      failed: 'Processing failed'
    };
    return map[status] || status;
  };

  const getStatusClass = (status) => {
    const map = {
      pending: 'status-draft',
      processing: 'status-submitted',
      completed: 'status-approved',
      failed: 'status-rejected'
    };
    return map[status] || 'status-draft';
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-start mb-4">
        <div>
          <h1 className="page-title">Processing Queue</h1>
          <p className="page-subtitle">
            Files are auto-processed when dropped into <code>backend/watch_folder/</code>
          </p>
        </div>
        <button
          className="btn btn-outline-primary d-flex align-items-center gap-2"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <FiRefreshCw size={16} className={refreshing ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Folder Info Banner */}
      <div className="pro-card mb-4" style={{ background: 'var(--primary-light)', border: '1px solid var(--primary)' }}>
        <div className="pro-card-body">
          <div className="d-flex align-items-start gap-3">
            <FiFolder size={24} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, color: 'var(--primary)', marginBottom: '0.25rem' }}>
                Drop receipts into the watch folder to auto-process
              </div>
              <code style={{
                display: 'block',
                background: 'white',
                padding: '0.5rem 0.75rem',
                borderRadius: '4px',
                fontSize: '0.8125rem',
                color: 'var(--neutral-700)',
                marginTop: '0.5rem',
                wordBreak: 'break-all'
              }}>
                C:\Users\USER\Downloads\Leapstack\idp-receipt-system\backend\watch_folder\
              </code>
              <div style={{ fontSize: '0.8125rem', color: 'var(--neutral-600)', marginTop: '0.5rem' }}>
                Supported: JPG, PNG, TIFF, BMP, WEBP, PDF • Max 20MB per file
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="pro-card">
        <div className="pro-card-header">
          <span>Processed Documents ({documents.length})</span>
          <span style={{ fontSize: '0.75rem', color: 'var(--neutral-500)', fontWeight: 400 }}>
            Auto-refreshes every 5 seconds
          </span>
        </div>
        <div className="pro-card-body" style={{ padding: 0 }}>
          {loading ? (
            <div className="empty-state">
              <div className="spinner-border text-primary" role="status" />
              <div className="mt-3">Loading...</div>
            </div>
          ) : documents.length === 0 ? (
            <div className="empty-state">
              <FiInbox className="empty-state-icon" />
              <h5>No documents yet</h5>
              <p>Drop receipt files into the watch folder to get started</p>
            </div>
          ) : (
            <table className="pro-table">
              <thead>
                <tr>
                  <th style={{ width: '50px' }}></th>
                  <th>Filename</th>
                  <th>Uploaded</th>
                  <th>Status</th>
                  <th style={{ width: '120px' }}></th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => (
                  <tr key={doc.id}>
                    <td>{getStatusIcon(doc.status)}</td>
                    <td>
                      <div style={{ fontWeight: 500, color: 'var(--neutral-800)' }}>
                        {doc.filename}
                      </div>
                      {doc.error_message && (
                        <div style={{ fontSize: '0.75rem', color: 'var(--danger)', marginTop: '2px' }}>
                          {doc.error_message}
                        </div>
                      )}
                    </td>
                    <td style={{ color: 'var(--neutral-500)' }}>
                      {new Date(doc.upload_date).toLocaleString()}
                    </td>
                    <td>
                      <span className={`status-badge ${getStatusClass(doc.status)}`}>
                        {getStatusText(doc.status)}
                      </span>
                    </td>
                    <td>
                      {doc.status === 'completed' && (
                        <button
                          className="btn btn-sm btn-primary d-flex align-items-center gap-1"
                          onClick={() => navigate(`/review?doc=${doc.id}`)}
                        >
                          Review <FiArrowRight size={14} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <style>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Queue;