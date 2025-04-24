import React, { useEffect, useState } from 'react';
import { Bar, Pie, Line } from 'react-chartjs-2';
import Chart from 'chart.js/auto';
import styles from './Visualizations.module.css';
import { Link } from 'react-router-dom';

import {
  Chart as ChartJS,
  BarElement,
  ArcElement,
  LineElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  PointElement
} from 'chart.js';

ChartJS.register(
  BarElement,
  ArcElement,
  LineElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend,
  PointElement
);

export default function Visualizations() {
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const raw = localStorage.getItem('queryGenieResult');
    if (raw) setResult(JSON.parse(raw));
  }, []);

  if (!result) {
    return <p style={{ padding: '2rem', color: 'var(--text-secondary)' }}>No data found.</p>;
  }

  const { questions, visualizations, results: dataRowsArray, summary } = result;

  const formatSummary = (summaryText: string) => {
    const lines = summaryText
      .split(/\n|\s(?=\d+\.\s)/g)
      .map(l => l.trim())
      .filter(Boolean);
    if (lines.length < 2) return <p>{summaryText}</p>;
    return (
      <ol style={{ paddingLeft: '1.5rem', marginTop: '1rem' }}>
        {lines.map((line, i) => (
          <li key={i} style={{ marginBottom: '0.75rem' }}>
            {line.replace(/^\d+\.\s*/, '')}
          </li>
        ))}
      </ol>
    );
  };

  const renderChart = (vizType: string, rows: any[], idx: number) => {
    const keys = Object.keys(rows[0] || {});
    const labelKeys = keys.filter(k => typeof rows[0][k] === 'string').slice(0, 2);
    const valueKey = keys.find(k => typeof rows[0][k] === 'number');

    const fullLabels = rows.map(r => labelKeys.map(k => r[k]).join(' | '));
    const fullValues = valueKey ? rows.map(r => r[valueKey]) : [];

    const combined = fullLabels.map((lbl, i) => ({ label: lbl, value: fullValues[i] }));
    const topCombined = combined.sort((a, b) => b.value - a.value).slice(0, 15);

    const labels = topCombined.map(item => item.label);
    const values = topCombined.map(item => item.value);

    const data = {
      labels,
      datasets: [{
        label: 'Value',
        data: values,
        backgroundColor: 'rgba(96, 165, 250, 0.6)', 
        borderColor: 'rgba(96, 165, 250, 1)',
        borderWidth: 1
      }]
    };
    
    const commonOpts = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };

    if (vizType.toLowerCase().includes('pie')) {
      return <Pie key={idx} data={data} options={commonOpts} />;
    } else if (vizType.toLowerCase().includes('line')) {
      return <Line key={idx} data={data} options={commonOpts} />;
    } else {
      return <Bar key={idx} data={data} options={commonOpts} />;
    }
  };

  return (
    <>
    <div className={styles.connectionStatus}>
      <div className={styles.connectionLabel}>connected to:</div>
      <div className={styles.dbName}>NORTHWIND-DB</div>
    </div>

    <div className={styles.hero}>
      <h1>QueryGenie</h1>
        <p className={styles.subtitle}>
          <i>AI that answers your questions before you ask.</i>
        </p>
        <p className={styles.description}>
          Here are the insights generated for your role based on the company data.
        </p>
    </div>

    <div className={styles.grid}>
      {questions.map((q: string, i: number) => {
        const rows: any[] = dataRowsArray[i] || [];
        const vizType: string = visualizations[i] || 'bar';

        return (
          <div key={i} className={styles.card}>
            <div className={styles.header}>
              <h2 className={styles.title}>
                <span className={styles.prefix}>Insight {i + 1}:</span> {q}
              </h2>
            </div>

            {rows.length === 0 ? (
              <div className={styles.textInsight}>No data available for this insight.</div>
            ) : rows.length === 1 && Object.keys(rows[0]).length === 2 ? (() => {
              const [k1, k2] = Object.entries(rows[0]);
              const statKey = typeof k1[1] === 'number' ? k1 : k2;
              const labelKey = statKey === k1 ? k2 : k1;
              return (
                <div className={styles.statCard}>
                  <div className={styles.statNumber}>{String(statKey[1])}</div>
                  <div className={styles.statLabel}>{String(labelKey[1])}</div>
                </div>
              );
            })() : (
              <div className={styles.chartContainer}>
                {renderChart(vizType, rows, i)}
              </div>
            )}
          </div>
        );
      })}

      <div className={`${styles.card} ${styles.summaryCard}`}>
        <div className={styles.header}>
          <h2 className={styles.title}>Overall Summary</h2>
        </div>
        <div className={styles.textInsight}>{formatSummary(summary)}</div>
      </div>

      <Link to="/" className={styles.backButton}>
        ← Back to Query Generator
      </Link>
    </div>
    </>
  );
}
