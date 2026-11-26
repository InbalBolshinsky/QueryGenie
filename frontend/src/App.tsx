import { useEffect, useState } from 'react';
import { analyze, getHealth, type AgentEvent, type Health, type Insight, type Profile } from './api';
import QueryForm from './components/QueryForm';
import AgentTrace from './components/AgentTrace';
import InsightCard from './components/InsightCard';
import styles from './App.module.css';

type Phase = 'form' | 'running' | 'done';

export default function App() {
  const [health, setHealth] = useState<Health>();
  const [phase, setPhase] = useState<Phase>('form');
  const [events, setEvents] = useState<AgentEvent[]>([]);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => undefined);
  }, []);

  const start = async (profile: Profile) => {
    setEvents([]);
    setPhase('running');
    try {
      await analyze(profile, (e) => setEvents((prev) => [...prev, e]));
    } catch (err) {
      setEvents((prev) => [...prev, { type: 'error', message: String(err) }]);
    }
    setPhase('done');
  };

  const insights: Insight[] = events.flatMap((e) => (e.type === 'insight' ? [e.insight] : []));
  const summary = events.find((e) => e.type === 'done')?.summary;
  const error = events.find((e) => e.type === 'error')?.message;

  return (
    <>
      {health && (
        <div className={styles.status}>
          <span>connected to</span> <b>{health.database}</b> <span>· agent model</span> <b>{health.model}</b>
          {!health.llm_key_set && <span className={styles.warn}> · no LLM_API_KEY set</span>}
        </div>
      )}

      <main className={styles.page}>
        <header className={styles.hero}>
          <h1>QueryGenie</h1>
          <p className={styles.subtitle}>AI that answers your questions before you ask.</p>
          {phase === 'form' && (
            <p className={styles.description}>
              Describe your company and role. An AI agent explores the database, writes and fixes its own SQL,
              and brings back the insights that matter to you.
            </p>
          )}
        </header>

        {phase === 'form' ? (
          <QueryForm onSubmit={start} />
        ) : (
          <>
            <AgentTrace events={events} running={phase === 'running'} />

            {insights.map((insight, i) => (
              <InsightCard key={i} index={i + 1} insight={insight} />
            ))}

            {summary && (
              <section className={styles.card}>
                <h2>Overall Summary</h2>
                <ul className={styles.summary}>
                  {summary.map((line, i) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </section>
            )}

            {error && <section className={`${styles.card} ${styles.error}`}>{error}</section>}

            {phase === 'done' && (
              <button className={styles.back} onClick={() => setPhase('form')}>
                ← Ask about another role
              </button>
            )}
          </>
        )}
      </main>
    </>
  );
}
