import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function EnhancedMenuOptionsManager({ menuItemId }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // New option form state
  const [newOption, setNewOption] = useState({
    name: '',
    is_required: false,
    sort_order: 0,
    choices: []
  });
  
  // Quick choice add state
  const [quickChoice, setQuickChoice] = useState({
    choice_name: '',
    price_modifier: 0,
    is_default: false,
    sort_order: 0
  });

  const getAuthHeader = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const fetchOptions = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options`, 
        { headers: getAuthHeader() }
      );
      setOptions(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to fetch options.');
    } finally {
      setLoading(false);
    }
  }, [menuItemId]);

  useEffect(() => {
    fetchOptions();
  }, [fetchOptions]);

  const showMessage = (message, isError = false) => {
    if (isError) {
      setError(message);
      setSuccess('');
    } else {
      setSuccess(message);
      setError('');
    }
    setTimeout(() => {
      setError('');
      setSuccess('');
    }, 3000);
  };

  const handleCreateCompleteOption = async (e) => {
    e.preventDefault();
    if (!newOption.name.trim()) {
      showMessage('Option name is required.', true);
      return;
    }

    try {
      await axios.post(
        `${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options`,
        newOption,
        { headers: getAuthHeader() }
      );
      showMessage('Option created successfully with all choices!');
      setNewOption({ name: '', is_required: false, sort_order: 0, choices: [] });
      fetchOptions();
    } catch (err) {
      showMessage(err.response?.data?.message || 'Failed to create option.', true);
    }
  };

  const addChoiceToNewOption = () => {
    if (!quickChoice.choice_name.trim()) {
      showMessage('Choice name is required.', true);
      return;
    }

    const newChoices = [...newOption.choices, { ...quickChoice }];
    setNewOption({ ...newOption, choices: newChoices });
    setQuickChoice({ choice_name: '', price_modifier: 0, is_default: false, sort_order: newChoices.length });
    showMessage('Choice added to option! Add more or create the option.');
  };

  const removeChoiceFromNewOption = (index) => {
    const newChoices = newOption.choices.filter((_, i) => i !== index);
    setNewOption({ ...newOption, choices: newChoices });
  };

  const handleDeleteOption = async (optionId) => {
    if (!window.confirm('Delete this option and all its choices?')) return;
    if (!optionId) {
      showMessage('Cannot delete option with an invalid ID.', true);
      return;
    }
    
    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options/${optionId}`,
        { headers: getAuthHeader() }
      );
      showMessage('Option deleted successfully!');
      fetchOptions();
    } catch (err) {
      showMessage(err.response?.data?.message || 'Failed to delete option.', true);
    }
  };

  const handleAddChoiceToExistingOption = async (optionId) => {
    const choice = {
      choice_name: quickChoice.choice_name.trim(),
      price_modifier: quickChoice.price_modifier,
      is_default: quickChoice.is_default,
      sort_order: quickChoice.sort_order
    };

    if (!choice.choice_name) {
      showMessage('Choice name is required.', true);
      return;
    }

    try {
      await axios.post(
        `${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options/${optionId}/choices`,
        choice,
        { headers: getAuthHeader() }
      );
      showMessage('Choice added to option!');
      setQuickChoice({ choice_name: '', price_modifier: 0, is_default: false, sort_order: 0 });
      fetchOptions();
    } catch (err) {
      showMessage(err.response?.data?.message || 'Failed to add choice.', true);
    }
  };

  const handleDeleteChoice = async (optionId, choiceId) => {
    if (!window.confirm('Delete this choice?')) return;
    if (!optionId || !choiceId) {
      showMessage('Cannot delete choice with an invalid ID.', true);
      return;
    }
    
    try {
      await axios.delete(
        `${API_BASE_URL}/api/v1/menu-items/${menuItemId}/options/${optionId}/choices/${choiceId}`,
        { headers: getAuthHeader() }
      );
      showMessage('Choice deleted successfully!');
      fetchOptions();
    } catch (err) {
      showMessage(err.response?.data?.message || 'Failed to delete choice.', true);
    }
  };

  if (loading) return <div>Loading options...</div>;

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <h3>Enhanced Menu Options & Choices</h3>
      
      {error && (
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', backgroundColor: '#ffebee', borderRadius: '4px' }}>
          {error}
        </div>
      )}
      
      {success && (
        <div style={{ color: 'green', marginBottom: '10px', padding: '10px', backgroundColor: '#e8f5e8', borderRadius: '4px' }}>
          {success}
        </div>
      )}

      {/* Enhanced Option Creation Form */}
      <div style={{ border: '1px solid #ddd', padding: '20px', marginBottom: '20px', borderRadius: '8px', backgroundColor: '#f9f9f9' }}>
        <h4>Create New Option with Choices</h4>
        <p style={{ color: '#666', fontSize: '14px' }}>
          Create a complete option with multiple choices in one go! Perfect for Size, Temperature, etc.
        </p>
        
        <form onSubmit={handleCreateCompleteOption}>
          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Option Name (e.g., "Size", "Temperature", "Milk Type"):
            </label>
            <input
              type="text"
              value={newOption.name}
              onChange={(e) => setNewOption({ ...newOption, name: e.target.value })}
              placeholder="Enter option name..."
              style={{ width: '100%', padding: '8px', border: '1px solid #ccc', borderRadius: '4px' }}
              required
            />
          </div>

          <div style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              <input
                type="checkbox"
                checked={newOption.is_required}
                onChange={(e) => setNewOption({ ...newOption, is_required: e.target.checked })}
              />
              Required (customers must choose)
            </label>
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
              Sort Order:
              <input
                type="number"
                value={newOption.sort_order}
                onChange={(e) => setNewOption({ ...newOption, sort_order: parseInt(e.target.value) })}
                style={{ width: '60px', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }}
              />
            </label>
          </div>

          {/* Add choices to new option */}
          <div style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '15px', borderRadius: '4px', backgroundColor: 'white' }}>
            <h5>Add Choices to This Option:</h5>
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center', marginBottom: '10px', flexWrap: 'wrap' }}>
              <input
                type="text"
                placeholder="Choice name (e.g., Small, Hot, Oat Milk)"
                value={quickChoice.choice_name}
                onChange={(e) => setQuickChoice({ ...quickChoice, choice_name: e.target.value })}
                style={{ padding: '6px', border: '1px solid #ccc', borderRadius: '4px', minWidth: '150px' }}
              />
              <input
                type="number"
                step="0.01"
                placeholder="Price adjustment ($)"
                value={quickChoice.price_modifier}
                onChange={(e) => setQuickChoice({ ...quickChoice, price_modifier: parseFloat(e.target.value) || 0 })}
                style={{ padding: '6px', border: '1px solid #ccc', borderRadius: '4px', width: '120px' }}
              />
              <label style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
                <input
                  type="checkbox"
                  checked={quickChoice.is_default}
                  onChange={(e) => setQuickChoice({ ...quickChoice, is_default: e.target.checked })}
                />
                Default
              </label>
              <button type="button" onClick={addChoiceToNewOption} style={{ padding: '6px 12px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px' }}>
                Add Choice
              </button>
            </div>

            {newOption.choices.length > 0 && (
              <div>
                <h6>Choices to be created:</h6>
                <ul style={{ listStyle: 'none', padding: 0 }}>
                  {newOption.choices.map((choice, index) => (
                    <li key={index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px', backgroundColor: '#f0f0f0', marginBottom: '5px', borderRadius: '4px' }}>
                      <span>
                        <strong>{choice.choice_name}</strong> 
                        {choice.price_modifier !== 0 && ` (+$${choice.price_modifier.toFixed(2)})`}
                        {choice.is_default && ' (Default)'}
                      </span>
                      <button 
                        type="button" 
                        onClick={() => removeChoiceFromNewOption(index)}
                        style={{ background: 'red', color: 'white', border: 'none', borderRadius: '4px', padding: '2px 8px', fontSize: '12px' }}
                      >
                        Remove
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <button type="submit" style={{ padding: '10px 20px', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            Create Complete Option {newOption.choices.length > 0 && `with ${newOption.choices.length} choices`}
          </button>
        </form>
      </div>

      {/* Existing Options Display */}
      <div>
        <h4>Existing Options</h4>
        {options.length === 0 ? (
          <p style={{ color: '#666' }}>No options created yet. Create your first option above!</p>
        ) : (
          options.map((option) => (
            <div key={option.id} style={{ border: '1px solid #ddd', padding: '15px', marginBottom: '15px', borderRadius: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                <h5 style={{ margin: 0 }}>
                  {option.name} 
                  {option.is_required && <span style={{ color: 'red' }}> *</span>}
                  <span style={{ color: '#666', fontSize: '12px', marginLeft: '10px' }}>
                    (Order: {option.sort_order})
                  </span>
                </h5>
                <button 
                  onClick={() => handleDeleteOption(option.id)}
                  style={{ background: 'red', color: 'white', border: 'none', borderRadius: '4px', padding: '5px 10px', cursor: loading ? 'not-allowed' : 'pointer' }}
                  disabled={loading}
                >
                  Delete Option
                </button>
              </div>

              {/* Choices for this option */}
              <div style={{ marginLeft: '20px' }}>
                <h6>Choices:</h6>
                {option.choices && option.choices.length > 0 ? (
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {option.choices.map((choice) => (
                      <li key={choice.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px', backgroundColor: '#f9f9f9', marginBottom: '5px', borderRadius: '4px' }}>
                        <span>
                          <strong>{choice.choice_name}</strong>
                          {choice.price_modifier !== 0 && ` (+$${parseFloat(choice.price_modifier).toFixed(2)})`}
                          {choice.is_default && <span style={{ color: 'green' }}> (Default)</span>}
                          <span style={{ color: '#666', fontSize: '12px' }}> (Order: {choice.sort_order})</span>
                        </span>
                        <button 
                          onClick={() => handleDeleteChoice(option.id, choice.id)}
                          style={{ background: 'orange', color: 'white', border: 'none', borderRadius: '4px', padding: '2px 8px', fontSize: '12px', cursor: loading ? 'not-allowed' : 'pointer' }}
                          disabled={loading}
                        >
                          Delete
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: '#666', fontSize: '14px' }}>No choices yet.</p>
                )}

                {/* Quick add choice to existing option */}
                <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
                  <strong>Add Choice to "{option.name}":</strong>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '5px', flexWrap: 'wrap' }}>
                    <input
                      type="text"
                      placeholder="Choice name"
                      value={quickChoice.choice_name}
                      onChange={(e) => setQuickChoice({ ...quickChoice, choice_name: e.target.value })}
                      style={{ padding: '4px', border: '1px solid #ccc', borderRadius: '4px', minWidth: '120px' }}
                    />
                    <input
                      type="number"
                      step="0.01"
                      placeholder="Price +/-"
                      value={quickChoice.price_modifier}
                      onChange={(e) => setQuickChoice({ ...quickChoice, price_modifier: parseFloat(e.target.value) || 0 })}
                      style={{ padding: '4px', border: '1px solid #ccc', borderRadius: '4px', width: '80px' }}
                    />
                    <label style={{ display: 'flex', alignItems: 'center', gap: '3px', fontSize: '14px' }}>
                      <input
                        type="checkbox"
                        checked={quickChoice.is_default}
                        onChange={(e) => setQuickChoice({ ...quickChoice, is_default: e.target.checked })}
                      />
                      Default
                    </label>
                    <button 
                      onClick={() => handleAddChoiceToExistingOption(option.id)}
                      style={{ padding: '4px 8px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}
                    >
                      Add
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default EnhancedMenuOptionsManager;
