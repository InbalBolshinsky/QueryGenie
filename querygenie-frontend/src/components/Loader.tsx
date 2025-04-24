import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Lottie from 'lottie-react';
import animationData from '../assets/genie.json';
import styles from './Loader.module.css';

export default function Loader() {
  const navigate = useNavigate();

  useEffect(() => {
    const raw = localStorage.getItem('pendingFormData');
    if (!raw) {
      console.error('No form data!');
      navigate('/');
      return;
    }
    const payload = JSON.parse(raw);

    (async () => {
      try {
        const resp = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const errText = await resp.text();
          throw new Error(errText || 'Server error');
        }
        const result = await resp.json();

        if (result.error) {
          throw new Error(result.error);
        }

        localStorage.setItem('queryGenieResult', JSON.stringify(result));
        navigate('/visualizations');
      } catch (err) {
        console.error(err);
        alert('Failed to generate insights');
        navigate('/');
      }
    })();
  }, [navigate]);

  return (
    <div className={styles.overlay}>
      <div className={styles.animation}>
        {animationData && (
          <Lottie
            animationData={animationData}
            loop={true}
            autoPlay={true}
            style={{ width: '100%', height: '100%' }}
          />
          
        )}
         <div className="animate-pulse text-sm text-gray-400">
         ✨ Summoning your business insights...<br />
          Hang tight while the Genie works its magic! ✨
        </div>
      </div>
    </div>
  );
}
