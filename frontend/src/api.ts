export interface Profile {
  company_name: string;
  company_description: string;
  job_title: string;
  job_responsibilities: string;
}

export interface Insight {
  question: string;
  takeaway: string;
  sql: string;
  chart: 'bar' | 'line' | 'pie' | 'number' | 'table';
  label_column?: string;
  value_column?: string;
  columns: string[];
  rows: Record<string, string | number | null>[];
}

export type AgentEvent =
  | { type: 'thought'; text: string }
  | { type: 'query'; sql: string; ok: boolean; rows?: number; error?: string }
  | { type: 'insight'; insight: Insight }
  | { type: 'done'; summary: string[] }
  | { type: 'error'; message: string };

export interface Health {
  database: string;
  model: string;
  llm_key_set: boolean;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch('/api/health');
  return res.json();
}

/** Starts the agent and calls onEvent for every step it streams back (newline-delimited JSON). */
export async function analyze(profile: Profile, onEvent: (e: AgentEvent) => void): Promise<void> {
  const res = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  if (!res.ok || !res.body) throw new Error(`Server error (${res.status})`);

  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    const lines = buffer.split('\n');
    buffer = lines.pop()!;
    lines.filter(Boolean).forEach((line) => onEvent(JSON.parse(line)));
  }
}
