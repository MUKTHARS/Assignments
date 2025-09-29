import React, { useState } from 'react';

const QueryInput = ({ onSubmit, loading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) {
      onSubmit(query.trim());
      setQuery('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-input-form">
      <div className="input-group">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about your sales data... (e.g., What is this week's total revenue?)"
          disabled={loading}
        />
        <button type="submit" disabled={!query.trim() || loading}>
          {loading ? 'Processing...' : 'Ask'}
        </button>
      </div>
    </form>
  );
};

export default QueryInput;