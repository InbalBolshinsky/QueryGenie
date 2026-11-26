import { useState, type ChangeEvent, type FormEvent } from 'react';
import type { Profile } from '../api';
import styles from './QueryForm.module.css';

const EXAMPLE: Profile = {
  company_name: 'Northwind Traders',
  company_description: 'An international distributor of specialty food and beverages, selling to restaurants and shops.',
  job_title: 'Head of Sales',
  job_responsibilities: 'Grow revenue, manage key customer accounts, and decide which products and regions to focus on.',
};

const EMPTY: Profile = { company_name: '', company_description: '', job_title: '', job_responsibilities: '' };

export default function QueryForm({ onSubmit }: { onSubmit: (profile: Profile) => void }) {
  const [form, setForm] = useState<Profile>(EMPTY);

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  return (
    <div className={styles.formContainer}>
      <form onSubmit={handleSubmit}>
        <div className={styles.formGroup}>
          <label htmlFor="company_name">Company Name</label>
          <input id="company_name" name="company_name" placeholder="Enter your company name"
            value={form.company_name} onChange={handleChange} required />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="company_description">Company Description</label>
          <textarea id="company_description" name="company_description" maxLength={4000}
            placeholder="Describe your company's main business, industry, and goals"
            value={form.company_description} onChange={handleChange} required />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="job_title">Job Title</label>
          <input id="job_title" name="job_title" placeholder="e.g., Customer Service Representative"
            value={form.job_title} onChange={handleChange} required />
        </div>

        <div className={styles.formGroup}>
          <label htmlFor="job_responsibilities">Main Responsibilities</label>
          <textarea id="job_responsibilities" name="job_responsibilities" maxLength={4000}
            placeholder="Describe your main tasks and responsibilities"
            value={form.job_responsibilities} onChange={handleChange} required />
        </div>

        <button type="submit">Generate Insights</button>
        <button type="button" className={styles.secondary} onClick={() => setForm(EXAMPLE)}>
          Fill in an example
        </button>
      </form>
    </div>
  );
}
