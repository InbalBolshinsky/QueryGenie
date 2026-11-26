import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './QueryForm.module.css';
import React from 'react';

export default function QueryForm() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    company_name: '',
    company_description: '',
    job_title: '',
    job_responsibilities: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('pendingFormData', JSON.stringify(form));
    navigate('/loader');
  };
  

  return (
    <>
      <div className={styles.connectionStatus}>
        <div className={styles.connectionLabel}>connected to:</div>
        <div className={styles.dbName}>NORTHWIND-DB</div>
      </div>
  
      <div className={styles.container}>
        <div className={styles.hero}>
          <h1>QueryGenie</h1>
          <p className={styles.subtitle}>
            <i>AI that answers your questions before you ask.</i>
          </p>
          <p className={styles.description}>
            Transform your business insights
            <br />
            with our AI-powered query generation platform.
          </p>
        </div>
  
        <div className={styles.formContainer}>
          <form onSubmit={handleSubmit}>
            <div className={styles.formGroup}>
              <label htmlFor="company_name">Company Name</label>
              <input
                id="company_name"
                name="company_name"
                type="text"
                placeholder="Enter your company name"
                value={form.company_name}
                onChange={handleChange}
                required
              />
            </div>
  
            <div className={styles.formGroup}>
              <label htmlFor="company_description">Company Description</label>
              <textarea
                id="company_description"
                name="company_description"
                placeholder="Describe your company's main business, industry, and goals"
                maxLength={4000}
                value={form.company_description}
                onChange={handleChange}
                required
              />
            </div>
  
            <div className={styles.formGroup}>
              <label htmlFor="job_title">Job Title</label>
              <input
                id="job_title"
                name="job_title"
                type="text"
                placeholder="e.g., Customer Service Representative"
                value={form.job_title}
                onChange={handleChange}
                required
              />
            </div>
  
            <div className={styles.formGroup}>
              <label htmlFor="job_responsibilities">Main Responsibilities</label>
              <textarea
                id="job_responsibilities"
                name="job_responsibilities"
                placeholder="Describe your main tasks and responsibilities"
                maxLength={4000}
                value={form.job_responsibilities}
                onChange={handleChange}
                required
              />
            </div>
  
            <button type="submit">Generate Insights</button>
          </form>
        </div>
      </div>
    </>
  );
}  