import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Grid, Card, CardContent, CardActions, Button,
  TextField, Select, MenuItem, FormControl, InputLabel, Dialog, DialogTitle,
  DialogContent, DialogActions, Chip, Alert, CircularProgress, Switch,
  FormControlLabel, IconButton, Snackbar
} from '@mui/material';
import { Add, Edit, Delete, Percent, AttachMoney, Today, Event } from '@mui/icons-material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function DiscountManager() {
  const [discounts, setDiscounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [formData, setFormData] = useState({
    name: '', description: '', discount_type: 'percentage', discount_value: '',
    is_active: true, valid_from: '', valid_until: ''
  });

  const getAuthHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('token')}` });

  useEffect(() => {
    fetchDiscounts();
  }, []);

  const fetchDiscounts = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/discounts`, { headers: getAuthHeader() });
      if (!response.ok) throw new Error('Failed to fetch discounts');
      const data = await response.json();
      setDiscounts(data);
    } catch (err) {
      setError('Failed to fetch discounts');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const payload = { ...formData, discount_value: parseFloat(formData.discount_value) };
      const url = editingId ? `${API_BASE_URL}/api/v1/discounts/${editingId}` : `${API_BASE_URL}/api/v1/discounts`;
      const response = await fetch(url, {
        method: editingId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify(payload)
      });
      if (!response.ok) throw new Error('Failed to save discount');
      
      setSuccess(`Discount ${editingId ? 'updated' : 'created'}!`);
      setDialogOpen(false);
      resetForm();
      fetchDiscounts();
    } catch (err) {
      setError('Failed to save discount');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '', description: '', discount_type: 'percentage', discount_value: '',
      is_active: true, valid_from: '', valid_until: ''
    });
    setEditingId(null);
  };

  const handleEdit = (discount) => {
    setFormData({
        ...discount,
        valid_from: discount.valid_from ? discount.valid_from.split('T')[0] : '',
        valid_until: discount.valid_until ? discount.valid_until.split('T')[0] : '',
    });
    setEditingId(discount.id);
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure?')) return;
    try {
      await fetch(`${API_BASE_URL}/api/v1/discounts/${id}`, { method: 'DELETE', headers: getAuthHeader() });
      setSuccess('Discount deleted!');
      fetchDiscounts();
    } catch (err) {
      setError('Failed to delete discount');
    }
  };

  if (loading) return <CircularProgress />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>Discount Management</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)} sx={{ borderRadius: 25 }}>
          Create Discount
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {discounts.map(d => (
          <Grid item xs={12} sm={6} md={4} key={d.id}>
            <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>{d.name}</Typography>
                  <Chip label={d.is_active ? 'Active' : 'Inactive'} color={d.is_active ? 'success' : 'default'} size="small"/>
                </Box>
                <Typography color="text.secondary" sx={{ mb: 2 }}>{d.description}</Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {d.discount_type === 'percentage' ? <Percent color="primary" sx={{ mr: 1 }} /> : <AttachMoney color="primary" sx={{ mr: 1 }} />}
                  <Typography variant="h5" color="primary">{d.discount_type === 'percentage' ? `${d.discount_value}%` : `$${d.discount_value}`}</Typography>
                </Box>

                <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary', mb: 1 }}>
                    <Today sx={{mr: 1, fontSize: '1rem'}} />
                    <Typography variant="body2">
                        Valid from: {d.valid_from ? new Date(d.valid_from).toLocaleDateString() : 'N/A'}
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                    <Event sx={{mr: 1, fontSize: '1rem'}} />
                    <Typography variant="body2">
                        Valid until: {d.valid_until ? new Date(d.valid_until).toLocaleDateString() : 'N/A'}
                    </Typography>
                </Box>

              </CardContent>
              <CardActions>
                <Button size="small" startIcon={<Edit />} onClick={() => handleEdit(d)}>Edit</Button>
                <IconButton color="error" onClick={() => handleDelete(d.id)}><Delete /></IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); resetForm(); }}>
        <DialogTitle>{editingId ? 'Edit Discount' : 'Create Discount'}</DialogTitle>
        <DialogContent>
          <TextField autoFocus margin="dense" label="Name" fullWidth value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })}/>
          <TextField margin="dense" label="Description" fullWidth multiline rows={2} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })}/>
          <FormControl fullWidth margin="dense">
            <InputLabel>Type</InputLabel>
            <Select value={formData.discount_type} onChange={(e) => setFormData({ ...formData, discount_type: e.target.value })} label="Type">
              <MenuItem value="percentage">Percentage</MenuItem>
              <MenuItem value="fixed">Fixed Amount</MenuItem>
            </Select>
          </FormControl>
          <TextField margin="dense" label="Value" type="number" fullWidth value={formData.discount_value} onChange={(e) => setFormData({ ...formData, discount_value: e.target.value })}/>
          <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField margin="dense" label="Valid From" type="date" fullWidth value={formData.valid_from} onChange={(e) => setFormData({ ...formData, valid_from: e.target.value })} InputLabelProps={{ shrink: true }}/>
              </Grid>
              <Grid item xs={6}>
                <TextField margin="dense" label="Valid Until" type="date" fullWidth value={formData.valid_until} onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })} InputLabelProps={{ shrink: true }}/>
              </Grid>
          </Grid>
          <FormControlLabel control={<Switch checked={formData.is_active} onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}/>} label="Active"/>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
          <Button onClick={handleSubmit} variant="contained">{editingId ? 'Update' : 'Create'}</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default DiscountManager; 
