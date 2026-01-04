import React from 'react';
import './ProblemCard.css';

const ProblemCard = ({ problem, onMarkDone }) => {
  const getDifficultyColor = (difficulty) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return '#4caf50';
      case 'medium':
        return '#ff9800';
      case 'hard':
        return '#f44336';
      default:
        return '#999';
    }
  };

  return (
    <div className="problem-card">
      <div className="problem-header">
        <h3 className="problem-title">{problem.title}</h3>
        <span
          className="difficulty-badge"
          style={{ backgroundColor: getDifficultyColor(problem.difficulty) }}
        >
          {problem.difficulty.toUpperCase()}
        </span>
      </div>
      <div className="problem-actions">
        <a
          href={problem.leetcode_url}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-leetcode"
        >
          View on Leetcode
        </a>
        <button onClick={() => onMarkDone(problem.id)} className="btn-done">
          Done
        </button>
      </div>
    </div>
  );
};

export default ProblemCard;

