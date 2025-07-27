import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  Box, Typography, List, ListItem, ListItemText, TextField, Button,
  IconButton, Select, MenuItem, FormControl, InputLabel, Paper,
  CircularProgress, Alert, Chip, Divider, Stack
} from '@mui/material';
import { Add, Delete } from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function RecipeManager({ menuItemId }) {
  const [recipe, setRecipe] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [newIngredientId, setNewIngredientId] = useState('');
  const [newIngredientAmount, setNewIngredientAmount] = useState('');

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  const fetchRecipe = useCallback(async () => {
    if (!menuItemId) return;
    try {
      const res = await axios.get(`${API_BASE_URL}/api/v1/recipes/${menuItemId}/recipe`, { headers: getAuthHeader() });
      setRecipe(res.data);
    } catch (err) {
      setError('Failed to fetch recipe.');
    }
  }, [menuItemId]);

  const fetchIngredients = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/v1/ingredients`, { headers: getAuthHeader() });
      setIngredients(res.data);
    } catch (err) {
      setError('Failed to fetch ingredients list.');
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchRecipe(), fetchIngredients()]).finally(() => setLoading(false));
  }, [fetchRecipe, fetchIngredients]);

  const handleAddIngredient = () => {
    if (!newIngredientId || !newIngredientAmount) {
        setError('Please select an ingredient and enter an amount.');
        return;
    }
    const ingredient = ingredients.find(i => i.id === newIngredientId);
    if (ingredient && !recipe.find(r => r.ingredient_id === newIngredientId)) {
        setRecipe([...recipe, {
            ingredient_id: newIngredientId,
            ingredient_name: ingredient.name,
            amount: parseFloat(newIngredientAmount),
            unit: ingredient.unit
        }]);
        setNewIngredientId('');
        setNewIngredientAmount('');
        setError('');
    } else {
        setError('Ingredient is already in the recipe.');
    }
  };

  const handleRemoveIngredient = (ingredientId) => {
    setRecipe(recipe.filter(r => r.ingredient_id !== ingredientId));
  };
  
  const handleSaveRecipe = async () => {
    try {
      setSuccess('');
      setError('');
      const payload = recipe.map(({ ingredient_id, amount }) => ({ ingredient_id, amount }));
      await axios.post(`${API_BASE_URL}/api/v1/recipes/${menuItemId}/recipe`, payload, { headers: getAuthHeader() });
      setSuccess('Recipe saved successfully!');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save recipe.');
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <Box>
        {error && <Alert severity="error" sx={{mb: 2}} onClose={() => setError('')}>{error}</Alert>}
        {success && <Alert severity="success" sx={{mb: 2}} onClose={() => setSuccess('')}>{success}</Alert>}

        <Paper variant="outlined" sx={{p: 2}}>
            <Typography variant="h6" sx={{mb: 2}}>Current Recipe</Typography>
            {recipe.length > 0 ? (
                <List>
                    {recipe.map(r => (
                        <ListItem key={r.ingredient_id} secondaryAction={
                            <IconButton edge="end" color="error" onClick={() => handleRemoveIngredient(r.ingredient_id)}>
                                <Delete />
                            </IconButton>
                        }>
                            <ListItemText primary={r.ingredient_name} secondary={`${r.amount} ${r.unit}`} />
                        </ListItem>
                    ))}
                </List>
            ) : (
                <Typography color="text.secondary" sx={{textAlign: 'center', p: 2}}>
                    No ingredients defined for this item.
                </Typography>
            )}
        </Paper>

        <Divider sx={{my: 3}}><Chip label="Add Ingredient" /></Divider>
        
        <Stack direction={{xs: 'column', sm: 'row'}} spacing={2} sx={{mb: 2}}>
            <FormControl fullWidth>
                <InputLabel>Ingredient</InputLabel>
                <Select
                    value={newIngredientId}
                    label="Ingredient"
                    onChange={e => setNewIngredientId(e.target.value)}
                >
                    {ingredients.map(ing => (
                        <MenuItem key={ing.id} value={ing.id}>{ing.name} ({ing.unit})</MenuItem>
                    ))}
                </Select>
            </FormControl>
            <TextField
                label="Amount"
                type="number"
                value={newIngredientAmount}
                onChange={e => setNewIngredientAmount(e.target.value)}
                fullWidth
            />
            <Button variant="outlined" onClick={handleAddIngredient} startIcon={<Add/>}>
                Add
            </Button>
        </Stack>

        <Button variant="contained" color="primary" onClick={handleSaveRecipe} fullWidth sx={{mt: 2}}>
            Save Recipe
        </Button>
    </Box>
  );
}

export default RecipeManager; 
