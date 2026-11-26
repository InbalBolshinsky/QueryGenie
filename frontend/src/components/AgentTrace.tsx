import { Lottie } from 'lottie-react';
import genie from '../assets/genie.json';
import type { AgentEvent } from '../api';
import styles from '../App.module.css';

/** Live log of what the agent is thinking and which queries it runs. */
export default function AgentTrace({ events, running }: { events: AgentEvent[]; running: boolean }) {
  const steps = events.filter((e) => e.type === 'thought' || e.type === 'query' || e.type === 'insight');
  const queries = events.filter((e) => e.type === 'query');

  return (
    <section className={styles.card}>
      <div className={styles.traceHeader}>
        {running && <Lottie src={genie} className={styles.genie} autoplay loop />}
        <div>
          <h2>{running ? 'The Genie is working…' : 'How the Genie got here'}</h2>
          <p className={styles.muted}>
            {queries.length} queries run · {queries.filter((q) => q.type === 'query' && !q.ok).length} self-corrected
          </p>
        </div>
      </div>

      <details open={running} className={styles.trace}>
        <summary>Agent steps ({steps.length})</summary>
        <ol>
          {steps.map((e, i) => (
            <li key={i} className={styles[e.type]}>
              {e.type === 'thought' && <span>💭 {e.text}</span>}
              {e.type === 'query' && (
                <>
                  <span>{e.ok ? `✅ Query returned ${e.rows} rows` : `⚠️ Query failed: ${e.error}`}</span>
                  <code>{e.sql}</code>
                </>
              )}
              {e.type === 'insight' && <span>📊 Saved insight: {e.insight.question}</span>}
            </li>
          ))}
        </ol>
      </details>
    </section>
  );
}
