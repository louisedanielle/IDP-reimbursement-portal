import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FiChevronRight, FiChevronDown, FiDownload, FiEye, FiTrash2, FiFolder
} from 'react-icons/fi';
import { getFolderView, deleteRequisition, API_BASE_URL } from '../services/api';

function Requisitions() {
  const [tree, setTree] = useState({});
  const [loading, setLoading] = useState(true);
  const [openCompany, setOpenCompany] = useState({});
  const [openCategory, setOpenCategory] = useState({});
  const [openPayee, setOpenPayee] = useState({});
  const navigate = useNavigate();

  const load = async () => {
    try {
      const data = await getFolderView();
      setTree(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const toggle = (obj, setObj, key) => setObj({ ...obj, [key]: !obj[key] });

  const handleDelete = async (id, prNumber) => {
    if (!window.confirm(`Delete ${prNumber}?`)) return;
    await deleteRequisition(id);
    load();
  };

  if (loading) return <div className="empty-state"><div className="spinner-border text-primary"/></div>;

  return (
    <div>
      <div className="page-header mb-4">
        <h1 className="page-title">Requisitions</h1>
        <p className="page-subtitle">Grouped by company → category → payee → month</p>
      </div>

      {Object.keys(tree).length === 0 && (
        <div className="pro-card">
          <div className="pro-card-body empty-state">
            <FiFolder className="empty-state-icon" />
            <h5>No requisitions yet</h5>
            <p>Upload a document to get started</p>
          </div>
        </div>
      )}

      {Object.entries(tree).map(([companyName, categories]) => {
        const isOpen = openCompany[companyName] !== false;   // default open
        return (
          <div key={companyName} className="pro-card mb-3">
            <div
              className="pro-card-header"
              style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}
              onClick={() => toggle(openCompany, setOpenCompany, companyName)}
            >
              {isOpen ? <FiChevronDown /> : <FiChevronRight />}
              <FiFolder />
              <span style={{ flex: 1 }}>{companyName}</span>
              <span style={{ fontSize: '0.75rem', color: 'var(--neutral-500)' }}>
                {Object.keys(categories).length} categories
              </span>
            </div>
            {isOpen && (
              <div className="pro-card-body" style={{ paddingLeft: '2rem' }}>
                {Object.entries(categories).map(([categoryName, payees]) => {
                  const ck = `${companyName}::${categoryName}`;
                  const cOpen = openCategory[ck] !== false;
                  return (
                    <div key={categoryName} style={{ marginBottom: 12 }}>
                      <div
                        onClick={() => toggle(openCategory, setOpenCategory, ck)}
                        style={{
                          cursor: 'pointer', display: 'flex', alignItems: 'center',
                          gap: 8, fontWeight: 600, padding: '8px 0',
                          borderBottom: '1px solid var(--neutral-200)'
                        }}
                      >
                        {cOpen ? <FiChevronDown /> : <FiChevronRight />}
                        📂 {categoryName}
                      </div>
                      {cOpen && Object.entries(payees).map(([payeeName, periods]) => {
                        const pk = `${ck}::${payeeName}`;
                        const pOpen = openPayee[pk] !== false;
                        return (
                          <div key={payeeName} style={{ marginLeft: 20, marginTop: 8 }}>
                            <div
                              onClick={() => toggle(openPayee, setOpenPayee, pk)}
                              style={{
                                cursor: 'pointer', display: 'flex', alignItems: 'center',
                                gap: 8, fontWeight: 500, padding: '4px 0',
                              }}
                            >
                              {pOpen ? <FiChevronDown /> : <FiChevronRight />}
                              👤 {payeeName}
                            </div>
                            {pOpen && Object.entries(periods).map(([period, prs]) => (
                              <div key={period} style={{ marginLeft: 40, marginTop: 4 }}>
                                <div style={{
                                  fontSize: '0.8125rem', color: 'var(--neutral-500)',
                                  textTransform: 'uppercase', fontWeight: 600,
                                  padding: '4px 0'
                                }}>
                                  📅 {period}
                                </div>
                                {prs.map((pr) => (
                                  <div
                                    key={pr.id}
                                    style={{
                                      display: 'flex', alignItems: 'center',
                                      gap: 12, padding: '8px 12px',
                                      border: '1px solid var(--neutral-200)',
                                      borderRadius: 6, marginBottom: 6,
                                      background: 'white'
                                    }}
                                  >
                                    <span style={{ fontWeight: 600, color: 'var(--primary)' }}>
                                      {pr.pr_number}
                                    </span>
                                    <span style={{ color: 'var(--neutral-500)', fontSize: '0.8125rem' }}>
                                      {pr.item_count} items
                                    </span>
                                    <span style={{ flex: 1 }} />
                                    <span style={{ fontWeight: 600 }}>
                                      HK${pr.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                    </span>
                                    <span className={`status-badge status-${pr.status}`}>{pr.status}</span>
                                    <button className="btn btn-sm btn-outline-primary"
                                      onClick={() => navigate(`/requisitions/${pr.id}`)}>
                                      <FiEye size={14}/>
                                    </button>
                                    <button className="btn btn-sm btn-outline-primary"
                                      onClick={() => window.open(`${API_BASE_URL}/api/requisitions/${pr.id}/export/word`)}>
                                      <FiDownload size={14}/>
                                    </button>
                                    <button className="btn btn-sm btn-outline-danger"
                                      onClick={() => handleDelete(pr.id, pr.pr_number)}>
                                      <FiTrash2 size={14}/>
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default Requisitions;