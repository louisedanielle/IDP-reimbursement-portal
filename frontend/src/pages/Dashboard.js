import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
   FiUploadCloud, FiEdit3, FiFolder, FiFileText, FiTag, FiDownload,
} from 'react-icons/fi';
import { getDashboardStats } from '../services/api';

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

      {/* ---------- 5 stat cards ---------- */}
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
          <div
            className="mb-3"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <FiTag style={{ color: 'var(--neutral-500)' }} />
            <h5 style={{ margin: 0, fontWeight: 600, flex: 1 }}>
              Spend by Company &amp; Category · {thisYear.label}
            </h5>
            <button
              className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1"
              onClick={() => downloadAllCompaniesAnnualReport(thisYear.label)}
              title="Download all companies annual report"
            >
              <FiDownload size={14} /> All Companies Annual Report
            </button>
          </div>

          {Object.entries(byCompany).map(([company, data]) => (
            <div key={company} className="pro-card mb-4">
              <div
                className="pro-card-header"
                style={{ display: 'flex', alignItems: 'center', gap: 8 }}
              >
                <FiFolder />
                <span style={{ flex: 1, fontWeight: 600 }}>{company}</span>
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: 'var(--neutral-500)',
                  }}
                >
                  {data.count} PR{data.count !== 1 ? 's' : ''}
                </span>
                <span style={{ fontWeight: 700, color: 'var(--primary)' }}>
                  HK${fmt(data.total)}
                </span>
                {data.company_id && (
                  <button
                    className="btn btn-sm btn-outline-primary d-flex align-items-center gap-1"
                    onClick={() =>
                      downloadCompanyAnnualReport(data.company_id, thisYear.label)
                    }
                    title={`Download ${company} annual report`}
                  >
                    <FiDownload size={14} /> Annual Report
                  </button>
                )}
              </div>

              <table className="pro-table" style={{ marginBottom: 0 }}>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th style={{ textAlign: 'center', width: '110px' }}>PRs</th>
                    <th style={{ textAlign: 'right', width: '160px' }}>
                      Amount (HKD)
                    </th>
                    <th style={{ textAlign: 'right', width: '100px' }}>
                      % of Company
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.categories).map(([cat, catData]) => {
                    const pct =
                      data.total > 0 ? (catData.total / data.total) * 100 : 0;
                    return (
                      <tr key={cat}>
                        <td style={{ fontWeight: 500 }}>{cat}</td>
                        <td style={{ textAlign: 'center' }}>
                          <span
                            style={{
                              display: 'inline-block',
                              padding: '0.15rem 0.5rem',
                              background: 'var(--primary-light)',
                              color: 'var(--primary)',
                              borderRadius: 4,
                              fontSize: '0.75rem',
                              fontWeight: 600,
                            }}
                          >
                            {catData.count}
                          </span>
                        </td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }}>
                          HK${fmt(catData.total)}
                        </td>
                        <td
                          style={{
                            textAlign: 'right',
                            color: 'var(--neutral-500)',
                          }}
                        >
                          {pct.toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  <tr style={{ background: 'var(--neutral-50)' }}>
                    <td style={{ fontWeight: 700 }}>Total · {company}</td>
                    <td
                      style={{
                        textAlign: 'center',
                        fontWeight: 700,
                      }}
                    >
                      {data.count}
                    </td>
                    <td
                      style={{
                        textAlign: 'right',
                        fontWeight: 700,
                        color: 'var(--primary)',
                      }}
                    >
                      HK${fmt(data.total)}
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>
                      100%
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          ))}
        </>
      )}

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