import React, { useState } from 'react';
import QueryInput from './QueryInput.jsx';
import { processQuery } from '../services/api.js';

const AnalyticsDashboard = () => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  const handleQuerySubmit = async (query) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await processQuery(query);
      setResults(response);
      
      // Add to history
      setHistory(prev => [{
        query,
        response: response.response,
        timestamp: new Date().toLocaleString()
      }, ...prev.slice(0, 9)]); // Keep last 10 items
      
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    "What is the total revenue for this week?",
    "Show me today's sales",
    "What is the monthly revenue trend for the past 6 months?",
    "Show me orders for customer 1"
  ];

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Analytics Dashboard</h2>
        <p>Ask natural language questions about your sales data</p>
      </div>

      <QueryInput onSubmit={handleQuerySubmit} loading={loading} />

      <div className="sample-queries">
        <h4>Try these sample queries:</h4>
        <div className="sample-query-list">
          {sampleQueries.map((query, index) => (
            <button
              key={index}
              className="sample-query"
              onClick={() => handleQuerySubmit(query)}
              disabled={loading}
            >
              {query}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Processing your query...</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <h3>Error</h3>
          <p>{error}</p>
        </div>
      )}

      {results && (
        <div className="results">
          <div className="results-header">
            <h3>Results</h3>
            <div className="result-meta">
              <span className="intent">Intent: {results.intent}</span>
              <span className="confidence">
                Confidence: {(results.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="natural-response">
            <h4>Response:</h4>
            <p>{results.response}</p>
          </div>

          {results.data && (
            <div className="raw-data">
              <h4>Raw Data:</h4>
              <pre>{JSON.stringify(results.data, null, 2)}</pre>
            </div>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="query-history">
          <h3>Recent Queries</h3>
          {history.map((item, index) => (
            <div key={index} className="history-item">
              <div className="history-query">
                <strong>Q:</strong> {item.query}
              </div>
              <div className="history-response">
                <strong>A:</strong> {item.response}
              </div>
              <div className="history-timestamp">{item.timestamp}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;