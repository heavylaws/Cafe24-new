import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function MenuItemOptionsManager({ menuItemId }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [newOption, setNewOption] = useState({ name: '', display_order: 0 });
  const [editingOptionId, setEditingOptionId] = useState(null);
  const [editOption, setEditOption] = useState({ name: '', display_order: 0 });
  const [newChoice, setNewChoice] = useState({});
  const [editingChoiceId, setEditingChoiceId] = useState(null);
  const [editChoice, setEditChoice] = useState({});

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  useEffect(() => {
    fetchOptions();
    // eslint-disable-next-line
  }, [menuItemId]);

  const fetchOptions = async () => {
    setLoading(true);
    setError('');
    try {
      // Fetch options and their choices for this menu item
      const res = await axios.get(`${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options`, { headers: getAuthHeader() });
      setOptions(res.data);
    } catch (err) {
      setError('Failed to fetch options.');
    } finally {
      setLoading(false);
    }
  };

  // Option CRUD
  const handleAddOption = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    if (!newOption.name.trim()) {
      setError('Option name is required.');
      return;
    }
    try {
      await axios.post(`${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options`, newOption, { headers: getAuthHeader() });
      setSuccess('Option added!');
      setNewOption({ name: '', display_order: 0 });
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to add option.');
    }
  };

  const handleEditOption = (option) => {
    setEditingOptionId(option.option_id);
    setEditOption({ name: option.option_name, display_order: option.display_order || 0 });
  };

  const handleUpdateOption = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await axios.put(`${API_BASE_URL}/api/v1/options/${editingOptionId}`, editOption, { headers: getAuthHeader() });
      setSuccess('Option updated!');
      setEditingOptionId(null);
      setEditOption({ name: '', display_order: 0 });
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update option.');
    }
  };

  const handleDeleteOption = async (optionId) => {
    if (!window.confirm('Delete this option and all its choices?')) return;
    setError('');
    setSuccess('');
    try {
      await axios.delete(`${API_BASE_URL}/api/v1/options/${optionId}`, { headers: getAuthHeader() });
      setSuccess('Option deleted!');
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete option.');
    }
  };

  // Choice CRUD
  const handleAddChoice = async (e, optionId) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    const choice = newChoice[optionId];
    if (!choice || !choice.choice_name || choice.price_usd === undefined) {
      setError('Choice name and price are required.');
      return;
    }
    try {
      await axios.post(`${API_BASE_URL}/api/v1/options/${optionId}/choices`, choice, { headers: getAuthHeader() });
      setSuccess('Choice added!');
      setNewChoice({ ...newChoice, [optionId]: { choice_name: '', price_usd: 0, display_order: 0 } });
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to add choice.');
    }
  };

  const handleEditChoice = (optionId, choice) => {
    setEditingChoiceId(choice.choice_id);
    setEditChoice({ choice_name: choice.choice_name, price_usd: choice.price_usd, display_order: choice.display_order || 0 });
  };

  const handleUpdateChoice = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    try {
      await axios.put(`${API_BASE_URL}/api/v1/choices/${editingChoiceId}`, editChoice, { headers: getAuthHeader() });
      setSuccess('Choice updated!');
      setEditingChoiceId(null);
      setEditChoice({});
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to update choice.');
    }
  };

  const handleDeleteChoice = async (choiceId) => {
    if (!window.confirm('Delete this choice?')) return;
    setError('');
    setSuccess('');
    try {
      await axios.delete(`${API_BASE_URL}/api/v1/choices/${choiceId}`, { headers: getAuthHeader() });
      setSuccess('Choice deleted!');
      fetchOptions();
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to delete choice.');
    }
  };

  if (loading) return <div>Loading options...</div>;

  return (
    <div style={{ marginTop: 20, marginBottom: 20, padding: 10, border: '1px solid #eee', borderRadius: 8 }}>
      <h4>Options & Choices</h4>
      {success && <div style={{ color: 'green', marginBottom: 8 }}>{success}</div>}
      {error && <div style={{ color: 'red', marginBottom: 8 }}>{error}</div>}
      <form onSubmit={handleAddOption} style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Option name (e.g., Size, Syrup)"
          value={newOption.name}
          onChange={e => setNewOption({ ...newOption, name: e.target.value })}
          required
          style={{ marginRight: 8 }}
        />
        <input
          type="number"
          placeholder="Display order"
          value={newOption.display_order}
          onChange={e => setNewOption({ ...newOption, display_order: Number(e.target.value) })}
          style={{ width: 100, marginRight: 8 }}
        />
        <button type="submit">Add Option</button>
      </form>
      {options.length === 0 && <div>No options defined for this item.</div>}
      {options.map(option => (
        <div key={option.option_id} style={{ marginBottom: 16, padding: 8, border: '1px solid #ddd', borderRadius: 6 }}>
          {editingOptionId === option.option_id ? (
            <form onSubmit={handleUpdateOption} style={{ marginBottom: 8 }}>
              <input
                type="text"
                value={editOption.name}
                onChange={e => setEditOption({ ...editOption, name: e.target.value })}
                required
                style={{ marginRight: 8 }}
              />
              <input
                type="number"
                value={editOption.display_order}
                onChange={e => setEditOption({ ...editOption, display_order: Number(e.target.value) })}
                style={{ width: 100, marginRight: 8 }}
              />
              <button type="submit">Save</button>
              <button type="button" onClick={() => setEditingOptionId(null)} style={{ marginLeft: 8 }}>Cancel</button>
            </form>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <strong>{option.option_name}</strong>
              <span style={{ marginLeft: 12, color: '#888' }}>(Order: {option.display_order})</span>
              <button style={{ marginLeft: 12 }} onClick={() => handleEditOption(option)}>Edit</button>
              <button style={{ marginLeft: 8, color: 'red' }} onClick={() => handleDeleteOption(option.option_id)}>Delete</button>
            </div>
          )}
          <div style={{ marginLeft: 16 }}>
            <form onSubmit={e => handleAddChoice(e, option.option_id)} style={{ marginBottom: 8 }}>
              <input
                type="text"
                placeholder="Choice name (e.g., Large, Chocolate)"
                value={newChoice[option.option_id]?.choice_name || ''}
                onChange={e => setNewChoice({ ...newChoice, [option.option_id]: { ...newChoice[option.option_id], choice_name: e.target.value } })}
                required
                style={{ marginRight: 8 }}
              />
              <input
                type="number"
                placeholder="Price (USD)"
                value={newChoice[option.option_id]?.price_usd || 0}
                onChange={e => setNewChoice({ ...newChoice, [option.option_id]: { ...newChoice[option.option_id], price_usd: Number(e.target.value) } })}
                required
                style={{ width: 100, marginRight: 8 }}
              />
              <input
                type="number"
                placeholder="Display order"
                value={newChoice[option.option_id]?.display_order || 0}
                onChange={e => setNewChoice({ ...newChoice, [option.option_id]: { ...newChoice[option.option_id], display_order: Number(e.target.value) } })}
                style={{ width: 100, marginRight: 8 }}
              />
              <button type="submit">Add Choice</button>
            </form>
            {option.choices && option.choices.length > 0 ? (
              <ul style={{ listStyle: 'none', paddingLeft: 0 }}>
                {option.choices.map(choice => (
                  <li key={choice.choice_id} style={{ marginBottom: 6 }}>
                    {editingChoiceId === choice.choice_id ? (
                      <form onSubmit={handleUpdateChoice} style={{ display: 'inline-block' }}>
                        <input
                          type="text"
                          value={editChoice.choice_name}
                          onChange={e => setEditChoice({ ...editChoice, choice_name: e.target.value })}
                          required
                          style={{ marginRight: 8 }}
                        />
                        <input
                          type="number"
                          value={editChoice.price_usd}
                          onChange={e => setEditChoice({ ...editChoice, price_usd: Number(e.target.value) })}
                          required
                          style={{ width: 100, marginRight: 8 }}
                        />
                        <input
                          type="number"
                          value={editChoice.display_order}
                          onChange={e => setEditChoice({ ...editChoice, display_order: Number(e.target.value) })}
                          style={{ width: 100, marginRight: 8 }}
                        />
                        <button type="submit">Save</button>
                        <button type="button" onClick={() => setEditingChoiceId(null)} style={{ marginLeft: 8 }}>Cancel</button>
                      </form>
                    ) : (
                      <>
                        <span>{choice.choice_name} (${(parseFloat(choice.price_usd) || 0).toFixed(2)}) (Order: {choice.display_order})</span>
                        <button style={{ marginLeft: 8 }} onClick={() => handleEditChoice(option.option_id, choice)}>Edit</button>
                        <button style={{ marginLeft: 8, color: 'red' }} onClick={() => handleDeleteChoice(choice.choice_id)}>Delete</button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div style={{ color: '#888' }}>No choices for this option.</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

export default MenuItemOptionsManager; 
