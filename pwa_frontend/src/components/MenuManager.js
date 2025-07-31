import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import EnhancedMenuOptionsManager from './EnhancedMenuOptionsManager';
import RecipeManager from './RecipeManager';
import {
  Stepper, Step, StepLabel, Button, TextField, Select, MenuItem as MuiMenuItem,
  Checkbox, FormControlLabel, Box, Typography, Paper, CircularProgress,
  Alert, Grid, Card, CardContent, CardActions, IconButton, Stack, Switch, Chip
} from '@mui/material';
import { Add, Edit, Delete, CheckCircle, ArrowForward, ArrowBack } from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const steps = ['Basic Info', 'Recipe', 'Options & Choices', 'Review & Save'];

// Helper function to process the flat category list from the API
const flattenCategories = (categories = []) => {
  return categories.map(category => ({
    ...category,
    displayName: category.path, // Use the pre-computed path from the API
    level: (category.path.match(/>/g) || []).length // Calculate level based on path depth
  }));
};

function MenuManager() {
  const [menuItems, setMenuItems] = useState([]);
  const [categories, setCategories] = useState([]); // This will now store the flat list
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState({
    name: '', 
    description: '', 
    base_price_usd: '', 
    category_id: null, 
    is_active: true, 
    image_url: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [createdItemId, setCreatedItemId] = useState(null);
  const [isFormVisible, setIsFormVisible] = useState(false);

  const getAuthHeader = useCallback(() => {
    const token = localStorage.getItem('token');
    console.log('Auth Token being sent:', token);
    return { Authorization: `Bearer ${token}` };
  }, []);

  const sleep = useCallback(ms => new Promise(resolve => setTimeout(resolve, ms)), []);

  const fetchData = useCallback(async (retries = 3) => {
    try {
      setLoading(true);
      await sleep(100); 
      const res = await axios.get(`${API_BASE_URL}/api/v1/menu/active`, { 
        headers: getAuthHeader() 
      });
      
      const { menu_items, categories } = res.data;

      setMenuItems(menu_items);
      
      const flatCategories = flattenCategories(categories);
      setCategories(flatCategories);

    } catch (err) {
      if (err.response?.status === 422 && retries > 0) {
        console.log(`Fetch failed with 422, retrying... ${retries - 1} attempts left.`);
        await sleep(500); // Wait a bit longer before retrying
        return fetchData(retries - 1);
      }
      setError('Failed to fetch menu data.');
      console.error(err); // Log the actual error for debugging
    } finally {
      setLoading(false);
    }
  }, [getAuthHeader, sleep]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ ...formData, [name]: type === 'checkbox' ? checked : value });
  };

  const handleNext = async () => {
    if (activeStep === 0) {
      if (!formData.name.trim() || !formData.base_price_usd || !formData.category_id) {
        setError('Please fill in all required fields.');
        return;
      }
      try {
        const payload = { ...formData, base_price_usd: parseFloat(formData.base_price_usd) };
        const url = editingId ? `${API_BASE_URL}/api/v1/menu-items/${editingId}` : `${API_BASE_URL}/api/v1/menu-items`;
        const method = editingId ? 'put' : 'post';
        
        const res = await axios[method](url, payload, { headers: getAuthHeader() });
        
        setCreatedItemId(editingId || res.data.id);
        setSuccess('Basic info saved. Now define the recipe.');
        setActiveStep(1); // Move to Recipe step
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to save menu item.');
      }
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBack = () => setActiveStep((prev) => prev - 1);

  const handleReset = () => {
    setFormData({ 
      name: '', 
      description: '', 
      base_price_usd: '', 
      category_id: null, 
      is_active: true, 
      image_url: ''
    });
    setEditingId(null);
    setCreatedItemId(null);
    setActiveStep(0);
    setError('');
    setSuccess('');
    setIsFormVisible(false);
    fetchData(); // Refresh list
  };

  const handleEdit = (item) => {
    setFormData({
      name: item.name,
      description: item.description,
      base_price_usd: item.base_price_usd,
      category_id: item.category_id, 
      is_active: item.is_active,
      image_url: item.image_url || ''
    });
    setEditingId(item.id);
    setCreatedItemId(item.id); // allow editing options immediately
    setIsFormVisible(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id) => {
    if (window.confirm('Are you sure you want to delete this menu item?')) {
      try {
        await axios.delete(`${API_BASE_URL}/api/v1/menu-items/${id}`, { headers: getAuthHeader() });
        setSuccess('Menu item deleted!');
        fetchData();
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to delete item.');
      }
    }
  };

  const toggleAvailability = async (item) => {
    try {
          const updatedItem = { ...item, is_active: !item.is_active };
          await axios.put(`${API_BASE_URL}/api/v1/menu-items/${item.id}`, updatedItem, { headers: getAuthHeader() });
          setSuccess(`Item availability updated!`);
          fetchData();
      } catch(err) {
          setError('Failed to update availability.')
      }
  }

  if (loading) return <CircularProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Menu Management</Typography>
        <Button 
          variant="contained" 
          startIcon={<Add />}
                onClick={() => {
              handleReset();
              setIsFormVisible(true);
          }}
          sx={{ borderRadius: 25, px: 3 }}
        >
          Add Menu Item
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {isFormVisible && (
        <Paper elevation={3} sx={{ p: 3, mb: 4, borderRadius: 3 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>{editingId ? 'Edit Item' : 'Create New Item'}</Typography>
          <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {steps.map(label => <Step key={label}><StepLabel>{label}</StepLabel></Step>)}
          </Stepper>

          {activeStep === 0 && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}><TextField label="Name" name="name" value={formData.name} onChange={handleInputChange} required fullWidth /></Grid>
              <Grid item xs={12} sm={3}><TextField label="Price (USD)" name="base_price_usd" type="number" value={formData.base_price_usd} onChange={handleInputChange} required fullWidth /></Grid>
              <Grid item xs={12} sm={3}><TextField label="Icon (Emoji)" name="image_url" value={formData.image_url} onChange={handleInputChange} fullWidth helperText="e.g., ☕" /></Grid>
              <Grid item xs={12}><TextField label="Description" name="description" value={formData.description} onChange={handleInputChange} fullWidth multiline rows={2} /></Grid>
              <Grid item xs={12} sm={6}>
                <Select 
                  label="Category" 
                  name="category_id" 
                  value={formData.category_id || ''} 
                  onChange={handleInputChange} 
                  required 
                  fullWidth 
                  displayEmpty
                >
                  <MuiMenuItem value=""><em>Select a category</em></MuiMenuItem>
                  {categories.map(cat => (
                    <MuiMenuItem 
                      key={cat.id} 
                      value={cat.id}
                      sx={{ pl: `${cat.level * 1.5 + 1}rem` }}
                    >
                      {cat.displayName}
                    </MuiMenuItem>
                  ))}
                </Select>
              </Grid>
              <Grid item xs={12} sm={6}><FormControlLabel control={<Checkbox checked={formData.is_active} onChange={handleInputChange} name="is_active" />} label="Available for ordering" /></Grid>
            </Grid>
          )}

          {activeStep === 1 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>Define Recipe</Typography>
              <Typography variant="body2" color="text.secondary" sx={{mb: 2}}>Specify the ingredients and quantities used to make this item. This will be used for automatic stock deduction.</Typography>
              <RecipeManager menuItemId={createdItemId} />
            </Box>
          )}

          {activeStep === 2 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>Add Options & Choices</Typography>
              <EnhancedMenuOptionsManager menuItemId={createdItemId} />
            </Box>
          )}
          
          {activeStep === 3 && (
            <Box sx={{ textAlign: 'center', p: 4 }}>
                <CheckCircle color="success" sx={{fontSize: 64, mb: 2}} />
                <Typography variant="h5" sx={{ mb: 2 }}>Item Saved!</Typography>
                <Typography color="text.secondary">The menu item and its options have been saved successfully.</Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
            {activeStep !== 3 ? (
                <Button onClick={handleBack} disabled={activeStep === 0} startIcon={<ArrowBack />}>Back</Button>
            ) : <Box />}
            {activeStep < 2 ? ( // Show Next for first 2 steps
                <Button variant="contained" onClick={handleNext} endIcon={<ArrowForward />}>Next</Button>
            ) : activeStep === 2 ? ( // Show Finish on Options step
                <Button variant="contained" onClick={() => setActiveStep(3)} endIcon={<CheckCircle />}>Finish & Review</Button>
            ) : (
                <Button variant="contained" onClick={handleReset}>Close Form</Button>
            )}
          </Box>
        </Paper>
      )}

      <div className="menu-items-container">
        <h3>Menu Items</h3>
        <Grid container spacing={3}>
          {menuItems.map(item => (
            <Grid xs={12} sm={6} md={4} key={item.id}>
              <Card elevation={2} sx={{ height: '100%', display: 'flex', flexDirection: 'column', borderRadius: 2 }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>{item.image_url && `${item.image_url} `}{item.name}</Typography>
                      <Chip label={item.is_active ? 'Active' : 'Inactive'} color={item.is_active ? 'success' : 'default'} size="small"/>
                  </Box>
                  <Typography color="text.secondary" sx={{ mb: 1 }}>{(() => { const cat = categories.find(c => c.id === item.category_id); if(!cat) return ''; const parts = cat.displayName.split('>'); return parts[parts.length-1].trim(); })()}</Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>{item.description}</Typography>
                  <Typography variant="h5" color="primary" sx={{ fontWeight: 'bold' }}>${(parseFloat(item.base_price_usd) || 0).toFixed(2)}</Typography>
                </CardContent>
                <CardActions sx={{ justifyContent: 'space-between', px: 2, pb: 2 }}>
                  <FormControlLabel control={<Switch checked={item.is_active} onChange={() => toggleAvailability(item)} />} label="Active" />
                  <Stack direction="row">
                      <IconButton onClick={() => handleEdit(item)}><Edit /></IconButton>
                      <IconButton onClick={() => handleDelete(item.id)} color="error"><Delete /></IconButton>
                  </Stack>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      </div>
    </Box>
  );
}

export default MenuManager;
