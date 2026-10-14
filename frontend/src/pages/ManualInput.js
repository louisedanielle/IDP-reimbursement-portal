import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiEdit3, FiAlertCircle } from 'react-icons/fi';
import { createManualDocument } from '../services/api';

function ManualInput() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    // When the page loads, create an empty document and jump to Review
    let cancelled = false;

    (async () => {
      try {
        const result = await createManualDocument();
        if (cancelled) return;
        navigate(`/review?doc=${result.document_id}`, { replace: true });
      } catch (err) {
        if (cancelled) return;
        setError(err.response?.data?.detail || err.message);
      }
    })();

    return () => { cancelled = true; };
  }, [navigate]);

  return (
    <div className="empty-state">
      {error ? (
        <div style={{ color: 'var(--danger)' }}>
          <FiAlertCircle size={32} />
          <div className="mt-3">Failed to open manual input: {error}</div>
          <button className="btn btn-outline-primary mt-3" onClick={() => navigate(-1)}>
            Go back
          </button>
        </div>
      ) : (
        <>
          <FiEdit3 size={40} style={{ color: 'var(--primary)' }} />
          <div className="mt-3">Opening manual input...</div>
          <div className="spinner-border text-primary mt-3" role="status" />
        </>
      )}
    </div>
  );
}

export default ManualInput;