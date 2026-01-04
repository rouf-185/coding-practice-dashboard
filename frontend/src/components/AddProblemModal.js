import React, { useState } from 'react';
import { problemService } from '../services/problemService';
import './AddProblemModal.css';

const AddProblemModal = ({ isOpen, onClose, onSuccess }) => {
  const [leetcodeUrl, setLeetcodeUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await problemService.addProblem(leetcodeUrl);
      setLeetcodeUrl('');
      onSuccess();
      onClose();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add problem. Please check the URL and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setLeetcodeUrl('');
      setError('');
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add Problem</h2>
          <button className="modal-close" onClick={handleClose} disabled={loading}>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          {error && <div className="error-message">{error}</div>}
          <div className="form-group">
            <label htmlFor="leetcodeUrl">Leetcode Problem URL</label>
            <input
              type="url"
              id="leetcodeUrl"
              value={leetcodeUrl}
              onChange={(e) => setLeetcodeUrl(e.target.value)}
              placeholder="https://leetcode.com/problems/four-divisors/description/"
              required
              disabled={loading}
            />
          </div>
          <div className="modal-actions">
            <button type="button" onClick={handleClose} disabled={loading} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary">
              {loading ? 'Adding...' : 'Add Problem'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProblemModal;

