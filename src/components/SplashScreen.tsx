import React, { useEffect, useState } from 'react';
import './SplashScreen.css';

interface SplashScreenProps {
  onComplete: () => void;
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Iniciando aplicação...');

  useEffect(() => {
    const steps = [
      { progress: 20, status: 'Carregando recursos...', delay: 300 },
      { progress: 40, status: 'Conectando ao banco de dados...', delay: 400 },
      { progress: 60, status: 'Verificando autenticação...', delay: 300 },
      { progress: 80, status: 'Preparando interface...', delay: 400 },
      { progress: 100, status: 'Pronto!', delay: 300 },
    ];

    let currentStep = 0;

    const runStep = () => {
      if (currentStep < steps.length) {
        const step = steps[currentStep];
        setTimeout(() => {
          setProgress(step.progress);
          setStatus(step.status);
          currentStep++;
          runStep();
        }, step.delay);
      } else {
        setTimeout(() => {
          onComplete();
        }, 500);
      }
    };

    runStep();
  }, [onComplete]);

  return (
    <div className="splash-screen">
      <div className="splash-content">
        <div className="logo-container">
          <img src="/cummins.ico" alt="Cummins Logo" className="splash-logo bounce" />
        </div>
        <h1 className="splash-title">Suppliers Scorecard</h1>
        <div className="progress-container">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }}></div>
          </div>
          <p className="progress-status">{status}</p>
        </div>
      </div>
    </div>
  );
};

export default SplashScreen;
