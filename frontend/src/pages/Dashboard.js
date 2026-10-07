import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FiUploadCloud, FiFolder, FiFileText,
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
  const byCategory = stats?.by_category_this_year || {};

  const fmt = (n) =>
    Number(n || 0).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });

  return (
    <div>
      {/* Page header */}
      <div className="page-header mb-4">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of payment requisitions</p>
      </div>

      {/* ---------- 5 stat cards ---------- */}
      <div className="row g-3 mb-4">
        {/* 1. Amount Paid · Last Month */}
        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {lastMonth.label}</div>
            <div className="stat-value success">
              HK${fmt(lastMonth.total)}
            </div>
          </div>
        </div>

        {/* 2. Requisitions · This Month */}
        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Requisitions · {thisMonth.label}</div>
            <div className="stat-value primary">{thisMonth.count}</div>
          </div>
        </div>

        {/* 3. Amount Paid · This Month */}
        <div className="col-lg-4 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {thisMonth.label}</div>
            <div className="stat-value success">
              HK${fmt(thisMonth.total)}
            </div>
          </div>
        </div>

        {/* 4. Requisitions · This Year */}
        <div className="col-lg-6 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Requisitions · {thisYear.label}</div>
            <div className="stat-value primary">{thisYear.count}</div>
          </div>
        </div>

        {/* 5. Amount Paid · This Year */}
        <div className="col-lg-6 col-md-6">
          <div className="stat-card h-100">
            <div className="stat-label">Amount Paid · {thisYear.label}</div>
            <div className="stat-value success">
              HK${fmt(thisYear.total)}
            </div>
          </div>
        </div>
      </div>

      {/* ---------- Quick actions ---------- */}
      <div className="pro-card mb-4">
        <div className="pro-card-header">
          <span>Quick Actions</span>
        </div>
        <div className="pro-card-body">
          <div className="d-flex gap-3 flex-wrap">
            <Link
              to="/upload"
              className="btn btn-primary d-flex align-items-center gap-2"
            >
              <FiUploadCloud size={16} /> Upload Document
            </Link>
            <Link
              to="/requisitions"
              className="btn btn-outline-primary d-flex align-items-center gap-2"
            >
              <FiFolder size={16} /> Browse Requisitions
            </Link>
            <Link
              to="/requisitions"
              className="btn btn-outline-primary d-flex align-items-center gap-2"
            >
              <FiFileText size={16} /> View All PRs
            </Link>
          </div>
        </div>
      </div>

      {/* ---------- Breakdown by company (this year) ---------- */}
      {Object.keys(byCompany).length > 0 && (
        <div className="pro-card mb-4">
          <div className="pro-card-header">
            <span>Companies · {thisYear.label}</span>
          </div>
          <table className="pro-table">
            <thead>
              <tr>
                <th>Company</th>
                <th style={{ textAlign: 'center' }}>PRs</th>
                <th style={{ textAlign: 'right' }}>Amount (HKD)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(byCompany)
                .sort((a, b) => b[1].total - a[1].total)
                .map(([company, data]) => (
                  <tr key={company}>
                    <td style={{ fontWeight: 500 }}>{company}</td>
                    <td style={{ textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '0.15rem 0.5rem',
                          background: 'var(--neutral-100)',
                          borderRadius: 4,
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {data.count}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>
                      HK${fmt(data.total)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ---------- Breakdown by category (this year) ---------- */}
      {Object.keys(byCategory).length > 0 && (
        <div className="pro-card mb-4">
          <div className="pro-card-header">
            <span>Categories · {thisYear.label}</span>
          </div>
          <table className="pro-table">
            <thead>
              <tr>
                <th>Category</th>
                <th style={{ textAlign: 'center' }}>PRs</th>
                <th style={{ textAlign: 'right' }}>Amount (HKD)</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(byCategory)
                .sort((a, b) => b[1].total - a[1].total)
                .map(([cat, data]) => (
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
                        {data.count}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>
                      HK${fmt(data.total)}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default Dashboard;