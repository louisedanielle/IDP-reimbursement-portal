import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FiUploadCloud, FiEdit3, FiFolder, FiFileText, FiTag, FiDownload,
} from 'react-icons/fi';
import {
  getDashboardStats,
  downloadCompanyAnnualReport,
  downloadAllCompaniesAnnualReport,
} from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardStats()
      .then((data) => setStats(data))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="empty-state">
        <div className="spinner-border text-primary" role="status" />
        <div className="mt-3">Loading dashboard...</div>
      </div>
    );
  }

  const lastMonth = stats?.last_month || { label: '', count: 0, total: 0 };
  const thisMonth = stats?.this_month || { label: '', count: 0, total: 0 };
  const thisYear = stats?.this_year || { label: '', count: 0, total: 0 };
  const byCompany = stats?.by_company_this_year || {};

  const fmt = (n) =>
    Number(n || 0).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  return (
    <div>
      {/* Header */}
      <div className="page-header mb-4">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of payment requisitions</p>
      </div>

      {/* ---------- Stat cards ---------- */}
      <div className="row g-3 mb-4">
        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {lastMonth.label}</div>
            <div className="stat-value success">HK${fmt(lastMonth.total)}</div>
          </div>
        </div>

        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Requisitions · {thisMonth.label}</div>
            <div className="stat-value primary">{thisMonth.count}</div>
          </div>
        </div>

        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {thisMonth.label}</div>
            <div className="stat-value success">HK${fmt(thisMonth.total)}</div>
          </div>
        </div>

        <div className="col-lg-6 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Requisitions · {thisYear.label}</div>
            <div className="stat-value primary">{thisYear.count}</div>
          </div>
        </div>

        <div className="col-lg-6 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {thisYear.label}</div>
            <div className="stat-value success">HK${fmt(thisYear.total)}</div>
          </div>
        </div>
      </div>

      {/* ---------- Quick Actions ---------- */}
      <div className="pro-card mb-4">
        <div className="pro-card-header">
          <span>Quick Actions</span>
        </div>
        <div className="pro-card-body">
          <div className="d-flex gap-3 flex-wrap">
            <Link to="/upload" className="btn btn-primary d-flex align-items-center gap-2">
              <FiUploadCloud size={16} /> Upload Document
            </Link>
            <Link to="/manual" className="btn btn-outline-primary d-flex align-items-center gap-2">
              <FiEdit3 size={16} /> Manual Input
            </Link>
            <Link to="/requisitions" className="btn btn-outline-primary d-flex align-items-center gap-2">
              <FiFolder size={16} /> Browse Requisitions
            </Link>
            <Link to="/requisitions" className="btn btn-outline-primary d-flex align-items-center gap-2">
              <FiFileText size={16} /> View All PRs
            </Link>
          </div>
        </div>
      </div>

      {/* ---------- Per-Company Category Breakdown (this year) ---------- */}
      {Object.keys(byCompany).length > 0 && (
        <>
          {/* Section header */}
          <div className="d-flex align-items-center mb-3" style={{ gap: 8 }}>
            <FiTag style={{ color: 'var(--neutral-400)' }} size={16} />
            <h5 style={{ margin: 0, fontWeight: 600, flex: 1 }}>
              Spend by Company &amp; Category · {thisYear.label}
            </h5>
            <button
              className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1"
              onClick={() => downloadAllCompaniesAnnualReport(thisYear.label)}
              title="Download all companies annual report"
            >
              <FiDownload size={14} /> All Companies Report
            </button>
          </div>

          {Object.entries(byCompany).map(([company, data]) => (
            <div
              key={company}
              className="pro-card mb-3"
              style={{ overflow: 'hidden' }}
            >
              {/* Company header */}
              <div
                style={{
                  padding: '16px 20px',
                  background: 'var(--primary)',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <FiFolder size={18} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: '1rem',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {company}
                  </div>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      opacity: 0.85,
                      marginTop: 2,
                    }}
                  >
                    {data.count} requisition{data.count !== 1 ? 's' : ''} ·{' '}
                    {Object.keys(data.categories).length} categor
                    {Object.keys(data.categories).length !== 1 ? 'ies' : 'y'}
                  </div>
                </div>
                <div
                  style={{
                    fontSize: '1.25rem',
                    fontWeight: 700,
                    whiteSpace: 'nowrap',
                  }}
                >
                  HK${fmt(data.total)}
                </div>
                {data.company_id && (
                  <button
                    className="btn btn-sm d-flex align-items-center gap-1"
                    onClick={() =>
                      downloadCompanyAnnualReport(data.company_id, thisYear.label)
                    }
                    title={`Download ${company} annual report`}
                    style={{
                      background: 'rgba(255,255,255,0.15)',
                      color: 'white',
                      border: '1px solid rgba(255,255,255,0.35)',
                      fontSize: '0.75rem',
                    }}
                  >
                    <FiDownload size={13} /> Annual
                  </button>
                )}
              </div>

              {/* Categories list */}
              <div style={{ padding: '8px 0' }}>
                {Object.entries(data.categories).map(([cat, catData], idx, arr) => {
                  const pct =
                    data.total > 0 ? (catData.total / data.total) * 100 : 0;
                  const isLast = idx === arr.length - 1;

                  return (
                    <div
                      key={cat}
                      style={{
                        padding: '12px 20px',
                        borderBottom: isLast
                          ? 'none'
                          : '1px solid var(--neutral-100)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 16,
                      }}
                    >
                      {/* Category name */}
                      <div
                        style={{
                          flex: 1,
                          minWidth: 0,
                          fontWeight: 500,
                          color: 'var(--neutral-800)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                        title={cat}
                      >
                        {cat}
                      </div>

                      {/* PR count */}
                      <div
                        style={{
                          width: 60,
                          textAlign: 'right',
                          fontSize: '0.8125rem',
                          color: 'var(--neutral-500)',
                        }}
                      >
                        {catData.count}{' '}
                        <span style={{ fontSize: '0.7rem' }}>
                          PR{catData.count !== 1 ? 's' : ''}
                        </span>
                      </div>

                      {/* Percentage bar */}
                      <div
                        style={{
                          width: 100,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                        }}
                        title={`${pct.toFixed(1)}% of company total`}
                      >
                        <div
                          style={{
                            flex: 1,
                            height: 6,
                            background: 'var(--neutral-100)',
                            borderRadius: 3,
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              width: `${Math.min(pct, 100)}%`,
                              height: '100%',
                              background:
                                'linear-gradient(90deg, #0ea5e9 0%, #1a4d8f 100%)',
                              borderRadius: 3,
                            }}
                          />
                        </div>
                        <span
                          style={{
                            fontSize: '0.7rem',
                            color: 'var(--neutral-500)',
                            width: 32,
                            textAlign: 'right',
                          }}
                        >
                          {pct.toFixed(0)}%
                        </span>
                      </div>

                      {/* Amount */}
                      <div
                        style={{
                          width: 120,
                          textAlign: 'right',
                          fontWeight: 600,
                          color: 'var(--neutral-800)',
                          fontVariantNumeric: 'tabular-nums',
                        }}
                      >
                        {fmt(catData.total)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </>
      )}

      {/* Empty state */}
      {Object.keys(byCompany).length === 0 && (
        <div className="pro-card">
          <div className="pro-card-body empty-state">
            <FiTag className="empty-state-icon" />
            <h5>No activity yet · {thisYear.label}</h5>
            <p>Upload a document or use Manual Input to create a requisition</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;