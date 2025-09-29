import React, { useState, useEffect } from 'react';
import AnalyticsDashboard from './components/AnalyticsDashboard.jsx';
import DatabaseConfig from './components/DatabaseConfig.jsx';
import './styles/App.css';

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('checking');
  const [apiDetails, setApiDetails] = useState(null);

  useEffect(() => {
    checkApiHealth();
  }, []);

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>🛍️ Shopping Analytics Dashboard</h1>
        <div className="status-indicator">
          API Status: 
          <span className={`status ${apiStatus}`}>
            {apiStatus === 'healthy' ? '✅ Healthy' : '❌ Unhealthy'}
          </span>
          {apiDetails && (
            <span className="api-details">
              | DB: {apiDetails.database_type} | Port: {apiDetails.port || 8000}
            </span>
          )}
        </div>
      </header>

      <nav className="app-nav">
        <button 
          className={currentView === 'dashboard' ? 'active' : ''}
          onClick={() => setCurrentView('dashboard')}
        >
          Analytics Dashboard
        </button>
        <button 
          className={currentView === 'config' ? 'active' : ''}
          onClick={() => setCurrentView('config')}
        >
          Database Configuration
        </button>
        <button 
          className="refresh-btn"
          onClick={checkApiHealth}
        >
          🔄 Refresh Status
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