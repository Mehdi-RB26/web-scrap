// File: frontend/src/App.jsx

import React, { useState, useEffect } from 'react';
import './App.css'; // We'll add some styles here

function App() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data from our backend API
    fetch('http://localhost:8000/api/articles')
      .then(response => response.json())
      .then(data => {
        setArticles(data);
        setLoading(false);
      })
      .catch(error => {
        console.error("Error fetching articles:", error);
        setLoading(false);
      });
  }, []); // The empty array ensures this runs only once

  if (loading) {
    return <div className="loading"><h1>Loading...</h1></div>;
  }

  return (
    <div className="app-container">
      <h1>Scraped Articles</h1>
      <div className="articles-list">
        {articles.map(article => (
          <div className="article-card" key={article._id}>
            <img src={article.thumbnail_url} alt={article.title} />
            <div className="card-content">
              <h2>
                <a href={article.url} target="_blank" rel="noopener noreferrer">
                  {article.title}
                </a>
              </h2>
              <p>{article.summary}</p>
              <small>{article.author} - {article.publication_date}</small>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;