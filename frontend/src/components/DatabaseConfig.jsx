import React, { useState, useEffect } from 'react';
import { updateDatabaseConfig, getHealth } from '../services/api.js';

const DatabaseConfig = ({ onConfigUpdate }) => {
  const [config, setConfig] = useState({
    database_type: 'postgres',
    connection_url: ''
  });
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    checkCurrentConfig();
  }, []);

  const checkCurrentConfig = async () => {
    try {
      const health = await getHealth();
      setStatus(`Current database: ${health.database_type}, Status: ${health.initialized ? 'Initialized' : 'Not Initialized'}`);
    } catch (error) {
      setStatus('Unable to connect to API');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await updateDatabaseConfig(config);
      setStatus('Configuration updated successfully! Reinitializing database...');
      
      // Wait a bit for reinitialization
      setTimeout(() => {
        checkCurrentConfig();
        onConfigUpdate();
      }, 2000);
      
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleReinitialize = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/reinitialize', {
        method: 'POST'
      });
      
      if (response.ok) {
        setStatus('Database reinitialized successfully!');
        checkCurrentConfig();
      } else {
        setStatus('Error reinitializing database');
      }
    } catch (error) {
      setStatus('Error reinitializing database');
    }
  };

  return (
    <div className="database-config">
      <h2>Database Configuration</h2>
      
      <div className="current-status">
        <h4>Current Status</h4>
        <p>{status}</p>
        <button onClick={handleReinitialize} className="reinit-btn">
          Reinitialize Database
        </button>
      </div>

      <form onSubmit={handleSubmit} className="config-form">
        <div className="form-group">
          <label htmlFor="database_type">Database Type:</label>
          <select
            id="database_type"
            value={config.database_type}
            onChange={(e) => setConfig({...config, database_type: e.target.value})}
          >
            <option value="postgres">PostgreSQL</option>
            <option value="mongodb">MongoDB</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="connection_url">Connection URL:</label>
          <input
            type="text"
            id="connection_url"
            value={config.connection_url}
            onChange={(e) => setConfig({...config, connection_url: e.target.value})}
            placeholder={
              config.database_type === 'postgres' 
                ? 'postgresql://user:password@localhost:5432/shopping_db'
                : 'mongodb://localhost:27017/shopping_db'
            }
            required
          />
        </div>

        <div className="form-help">
          <h4>Example URLs:</h4>
          <ul>
            <li><strong>PostgreSQL:</strong> postgresql://username:password@localhost:5432/database_name</li>
            <li><strong>MongoDB:</strong> mongodb://localhost:27017/database_name</li>
          </ul>
        </div>

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'Updating...' : 'Update Configuration'}
        </button>
      </form>
    </div>
  );
};

export default DatabaseConfig;