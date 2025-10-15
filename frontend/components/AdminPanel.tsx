'use client';
import React from 'react';
import { apiIngest, apiMetrics } from '../lib/api';
import type { MetricsData } from '../lib/types';
import styles from './AdminPanel.module.css';

export default function AdminPanel() {
  const [metrics, setMetrics] = React.useState<MetricsData | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [successMessage, setSuccessMessage] = React.useState<string>('');

  const refresh = async () => {
    const m = await apiMetrics();
    setMetrics(m);
  };

  const ingest = async () => {
    setBusy(true);
    setSuccessMessage('');
    try {
      const result = await apiIngest();
      await refresh();
      setSuccessMessage(`✅ Successfully ingested ${result.indexed_docs} documents (${result.indexed_chunks} chunks)`);
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setSuccessMessage(`❌ Error: ${errorMessage}`);
      setTimeout(() => setSuccessMessage(''), 5000);
    } finally {
      setBusy(false);
    }
  };

  React.useEffect(() => { refresh(); }, []);

  return (
    <div className={`card ${styles.adminContainer}`}>
      <h2>Admin</h2>
      <div className={styles.buttonContainer}>
        <button onClick={ingest} disabled={busy} className={styles.adminButton}>
          {busy ? 'Indexing...' : 'Ingest sample docs'}
        </button>
        <button onClick={refresh} className={styles.adminButton}>Refresh metrics</button>
      </div>
      {successMessage && (
        <div className={`${styles.successMessage} ${successMessage.includes('✅') ? styles.successMessageSuccess : styles.successMessageError}`}>
          {successMessage}
        </div>
      )}
      {metrics && (
        <div className={`code ${styles.metricsContainer}`}>
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
