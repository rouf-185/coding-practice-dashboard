import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { problemService } from '../services/problemService';
import { authService } from '../services/authService';
import ProblemCard from '../components/ProblemCard';
import AddProblemModal from '../components/AddProblemModal';
import './Dashboard.css';

const Dashboard = () => {
  const [problems, setProblems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadUser();
    loadProblems();
  }, []);

  const loadUser = async () => {
    try {
      const userData = await authService.getUserInfo();
      setUser(userData);
    } catch (err) {
      navigate('/login');
    }
  };

  const loadProblems = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await problemService.getPracticeProblems();
      setProblems(data);
    } catch (err) {
      setError('Failed to load problems. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkDone = async (problemId) => {
    try {
      await problemService.markAsDone(problemId);
      // Remove the problem from the list after marking as done
      setProblems(problems.filter(p => p.id !== problemId));
    } catch (err) {
      setError('Failed to mark problem as done. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      await authService.logout();
      navigate('/login');
    } catch (err) {
      navigate('/login');
    }
  };

  const handleAddSuccess = () => {
    loadProblems();
  };

  // Group problems by category
  const groupedProblems = problems.reduce((acc, problem) => {
    const category = problem.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(problem);
    return acc;
  }, {});

  if (loading && !user) {
    return <div className="dashboard-loading">Loading...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>CodingFlashcard</h1>
        <div className="header-actions">
          <button onClick={() => setIsModalOpen(true)} className="btn-add-problem">
            Add Problem
          </button>
          {user && (
            <div className="user-info">
              <span>{user.username}</span>
              <button onClick={handleLogout} className="btn-logout">
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      <main className="dashboard-content">
        {error && <div className="error-banner">{error}</div>}
        
        {loading ? (
          <div className="loading-message">Loading problems...</div>
        ) : problems.length === 0 ? (
          <div className="empty-state">
            <h2>No problems to practice today!</h2>
            <p>Add a problem to get started with your spaced repetition practice.</p>
            <button onClick={() => setIsModalOpen(true)} className="btn-primary">
              Add Your First Problem
            </button>
          </div>
        ) : (
          <div className="problems-container">
            {Object.entries(groupedProblems).map(([category, categoryProblems]) => (
              <div key={category} className="problem-category">
                <h2 className="category-title">{category}</h2>
                <div className="problem-list">
                  {categoryProblems.map(problem => (
                    <ProblemCard
                      key={problem.id}
                      problem={problem}
                      onMarkDone={handleMarkDone}
                    />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <AddProblemModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleAddSuccess}
      />
    </div>
  );
};

export default Dashboard;

