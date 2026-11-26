import 'chart.js/auto';
import { Bar, Line, Pie } from 'react-chartjs-2';
import type { Insight } from '../api';
import styles from '../App.module.css';

const COLORS = ['#60A5FA', '#FCD34D', '#34D399', '#F472B6', '#A78BFA', '#FB923C', '#22D3EE', '#F87171'];

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: '#CBD5E1' }, grid: { color: 'rgba(255,255,255,0.05)' } },
    y: { ticks: { color: '#CBD5E1' }, grid: { color: 'rgba(255,255,255,0.08)' } },
  },
};

function Chart({ insight }: { insight: Insight }) {
  const { chart, rows, columns, label_column = '', value_column = '' } = insight;

  if (chart === 'number') {
    const value = rows[0][value_column];
    return <div className={styles.bigNumber}>{typeof value === 'number' ? value.toLocaleString() : value}</div>;
  }

  if (chart === 'table') {
    return (
      <div className={styles.tableWrap}>
        <table>
          <thead>
            <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
          </thead>
          <tbody>
            {rows.slice(0, 15).map((row, i) => (
              <tr key={i}>{columns.map((c) => <td key={c}>{String(row[c] ?? '')}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  const data = {
    labels: rows.map((r) => String(r[label_column])),
    datasets: [{
      label: value_column,
      data: rows.map((r) => Number(r[value_column])),
      backgroundColor: chart === 'pie' ? COLORS : 'rgba(96, 165, 250, 0.6)',
      borderColor: chart === 'pie' ? '#1E293B' : '#60A5FA',
      borderWidth: chart === 'line' ? 2 : 1,
      tension: 0.3,
    }],
  };

  return (
    <div className={styles.chart}>
      {chart === 'pie' ? (
        <Pie data={data} options={{ ...options, scales: {}, plugins: { legend: { position: 'right', labels: { color: '#CBD5E1' } } } }} />
      ) : chart === 'line' ? (
        <Line data={data} options={options} />
      ) : (
        <Bar data={data} options={options} />
      )}
    </div>
  );
}

export default function InsightCard({ insight, index }: { insight: Insight; index: number }) {
  return (
    <section className={styles.card}>
      <h2>
        <span className={styles.prefix}>Insight {index}:</span> {insight.question}
      </h2>
      <p className={styles.takeaway}>{insight.takeaway}</p>
      <Chart insight={insight} />
      <details className={styles.sql}>
        <summary>SQL</summary>
        <code>{insight.sql}</code>
      </details>
    </section>
  );
}
