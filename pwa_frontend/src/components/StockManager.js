import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Tabs, Tab, Grid, Card, CardContent, Button,
  TextField, Select, MenuItem, FormControl, InputLabel, Dialog, DialogTitle,
  DialogContent, DialogActions, Chip, Alert, CircularProgress, Table, 
  TableBody, TableCell, TableContainer, TableHead, TableRow, IconButton, Snackbar, Divider
} from '@mui/material';
import { Add, Edit, Inventory, TrendingUp, TrendingDown, History } from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function IngredientsTab() {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [usage, setUsage] = useState([]);
  const [formData, setFormData] = useState({
    name: '', unit: '', cost_per_unit_usd: '', reorder_level: '', current_stock: ''
  });

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  useEffect(() => {
    fetchIngredients();
  }, []);

  const fetchIngredients = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/ingredients`, { headers: getAuthHeader() });
      if (!response.ok) throw new Error('Failed to fetch ingredients');
      const data = await response.json();
      setIngredients(data);
    } catch (err) {
      setError('Failed to fetch ingredients');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const url = editingId ? `${API_BASE_URL}/api/v1/ingredients/${editingId}` : `${API_BASE_URL}/api/v1/ingredients`;
      const response = await fetch(url, {
        method: editingId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify(formData)
      });
      if (!response.ok) throw new Error('Failed to save ingredient');
      
      setSuccess(`Ingredient ${editingId ? 'updated' : 'created'}!`);
      setDialogOpen(false);
      resetForm();
      fetchIngredients();
    } catch (err) {
      setError('Failed to save ingredient');
    }
  };

  const resetForm = () => {
    setFormData({ name: '', unit: '', cost_per_unit_usd: '', reorder_level: '', current_stock: '' });
    setEditingId(null);
    setUsage([]);
  };

  const handleEdit = (ingredient) => {
    setFormData(ingredient);
    setEditingId(ingredient.id);
    fetch(`${API_BASE_URL}/api/v1/ingredients/${ingredient.id}/usage`, { headers: getAuthHeader() })
      .then(res => res.json())
      .then(data => setUsage(data))
      .catch(() => setUsage([]));
    setDialogOpen(true);
  };

  if (loading) return <CircularProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Manage Ingredients</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)} sx={{ borderRadius: 25 }}>
          Add Ingredient
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Grid container spacing={2}>
        {ingredients.map(ing => (
          <Grid item xs={12} sm={6} md={4} key={ing.id}>
            <Card elevation={2} sx={{ borderRadius: 2 }}>
              <CardContent>
                <Typography variant="h6">{ing.name}</Typography>
                <Typography color="text.secondary">Unit: {ing.unit}</Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', my: 1 }}>
                  <Typography variant="h4" sx={{ mr: 1, fontWeight: 'bold' }}>{ing.current_stock}</Typography>
                  <Typography variant="h6" color="text.secondary">{ing.unit}</Typography>
                </Box>
                {ing.current_stock <= ing.reorder_level && (
                    <Chip label="Low Stock" color="warning" size="small" icon={<TrendingDown />} />
                )}
                <Divider sx={{my: 2}} />
                <Button size="small" onClick={() => handleEdit(ing)} startIcon={<Edit />}>Manage</Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); resetForm(); }}>
        <DialogTitle>{editingId ? 'Edit Ingredient' : 'Add Ingredient'}</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" label="Name" fullWidth value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} />
          <FormControl fullWidth margin="dense">
            <InputLabel>Unit</InputLabel>
            <Select
              value={formData.unit}
              label="Unit"
              onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            >
              <MenuItem value="kg">kg</MenuItem>
              <MenuItem value="liter">liter</MenuItem>
              <MenuItem value="piece">piece</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Cost per Unit ($)" type="number" fullWidth value={formData.cost_per_unit_usd} onChange={(e) => setFormData({ ...formData, cost_per_unit_usd: e.target.value })} />
          <TextField margin="dense" label="Reorder Level" type="number" fullWidth value={formData.reorder_level} onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })} />
          {editingId && (
            usage.length > 0 ? (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>Used in menu items:</Typography>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {usage.map(item => <li key={item.id}>{item.name}</li>)}
                </ul>
              </Box>
            ) : (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                Not used in any menu items.
              </Typography>
            )
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">{editingId ? 'Update' : 'Create'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

function StockAdjustmentsTab() {
  const [adjustments, setAdjustments] = useState([]);
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    ingredient_id: '', adjustment_type: 'manual', quantity_change: '', reason: ''
  });

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [adjRes, ingRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/stock/adjustments`, { headers: getAuthHeader() }),
        fetch(`${API_BASE_URL}/api/v1/ingredients`, { headers: getAuthHeader() })
      ]);
      const adjData = await adjRes.json();
      const ingData = await ingRes.json();
      setAdjustments(adjData);
      setIngredients(ingData);
    } catch (err) {
      setError('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/stock/adjust`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify(formData)
      });
      setDialogOpen(false);
      fetchData();
    } catch (err) {
      setError('Failed to create adjustment');
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">Adjustment History</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)} sx={{borderRadius: 25}}>New Adjustment</Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <TableContainer component={Paper} elevation={2} sx={{borderRadius: 2}}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Ingredient</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Change</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>User</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(Array.isArray(adjustments) ? adjustments : []).map((adj) => (
              <TableRow key={adj.id}>
                <TableCell>{new Date(adj.created_at).toLocaleDateString()}</TableCell>
                <TableCell>{adj.ingredient_name}</TableCell>
                <TableCell><Chip label={adj.adjustment_type} size="small" /></TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', color: adj.quantity_change > 0 ? 'success.main' : 'error.main' }}>
                    {adj.quantity_change > 0 ? <TrendingUp sx={{ mr: 1 }} /> : <TrendingDown sx={{ mr: 1 }} />}
                    {adj.quantity_change} {adj.ingredient_unit}
                  </Box>
                </TableCell>
                <TableCell>{adj.reason}</TableCell>
                <TableCell>{adj.user_name}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
        <DialogTitle>New Stock Adjustment</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Ingredient</InputLabel>
            <Select value={formData.ingredient_id} onChange={(e) => setFormData({ ...formData, ingredient_id: e.target.value })} label="Ingredient">
              {ingredients.map(ing => <MenuItem key={ing.id} value={ing.id}>{ing.name}</MenuItem>)}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Type</InputLabel>
            <Select value={formData.adjustment_type} onChange={(e) => setFormData({ ...formData, adjustment_type: e.target.value })} label="Type">
              <MenuItem value="manual">Manual</MenuItem>
              <MenuItem value="restock">Restock</MenuItem>
              <MenuItem value="waste">Waste/Loss</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Quantity Change (+/-)" type="number" fullWidth value={formData.quantity_change} onChange={(e) => setFormData({ ...formData, quantity_change: e.target.value })}/>
          <TextField margin="dense" label="Reason" fullWidth multiline rows={2} value={formData.reason} onChange={(e) => setFormData({ ...formData, reason: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default function StockManager() {
  const [tab, setTab] = useState(0);

  return (
    <Box>
      <Tabs value={tab} onChange={(e, val) => setTab(val)} indicatorColor="primary" textColor="primary" sx={{ mb: 3 }}>
        <Tab label="Ingredients" icon={<Inventory />} iconPosition="start" />
        <Tab label="Adjustments" icon={<History />} iconPosition="start" />
      </Tabs>
      {tab === 0 && <IngredientsTab />}
      {tab === 1 && <StockAdjustmentsTab />}
    </Box>
  );
} 
