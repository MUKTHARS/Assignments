import React, { useState, useEffect } from 'react';
import AnalyticsDashboard from './components/AnalyticsDashboard.jsx';
import DatabaseConfig from './components/DatabaseConfig.jsx';
import './styles/App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('checking');
  const [apiDetails, setApiDetails] = useState(null);
  const [currentDatabase, setCurrentDatabase] = useState('mongodb');
  const [theme, setTheme] = useState(() => {
    // Get theme from localStorage or default to 'light'
    return localStorage.getItem('theme') || 'light';
  });

  useEffect(() => {
    checkApiHealth();
  }, []);

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);
    // Save theme to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const checkApiHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        setApiStatus('healthy');
        setApiDetails(data);
      } else {
        setApiStatus('unhealthy');
        setApiDetails(null);
      }
    } catch (error) {
      setApiStatus('unhealthy');
      setApiDetails(null);
    }
  };

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛍️ Sapple Store</h1>
        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === 'light' ? '🌙 Dark Mode' : '☀️ Light Mode'}
        </button>
      </header>
      
      <nav className="app-nav">
        <button 
          className={currentView === 'dashboard' ? 'active' : ''}
          onClick={() => setCurrentView('dashboard')}
        >
          Ask Here
        </button>
        <button 
          className={currentView === 'config' ? 'active' : ''}
          onClick={() => setCurrentView('config')}
        >
          Database Configuration
        </button>
      </nav>
      
      <main className="app-main">
        {currentView === 'dashboard' && <AnalyticsDashboard />}
        {currentView === 'config' && <DatabaseConfig onConfigUpdate={checkApiHealth} />}
      </main>
    </div>
  );
}

export default App;