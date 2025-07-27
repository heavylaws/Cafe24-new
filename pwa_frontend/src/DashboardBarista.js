import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, List, ListItem, ListItemText, Chip, CircularProgress, Alert, AppBar, Button, Snackbar } from '@mui/material';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function BaristaOrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingId, setUpdatingId] = useState(null);
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/api/v1/orders/for-barista`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch orders');
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      setError('Failed to fetch barista orders.');
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (orderId, newStatus) => {
    setUpdatingId(orderId);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/api/v1/orders/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (!res.ok) throw new Error('Failed to update order status');
      setSuccess('Order status updated!');
      fetchOrders();
    } catch (err) {
      setError('Failed to update order status.');
    } finally {
      setUpdatingId(null);
    }
  };

  if (loading) return <Box sx={{ textAlign: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Orders to Prepare</Typography>
      {orders.length === 0 ? <Typography>No orders to prepare.</Typography> : (
        <List>
          {orders.map(order => (
            <ListItem key={order.order_id} alignItems="flex-start" sx={{ mb: 2, borderBottom: '1px solid #eee' }}>
              <ListItemText
                primary={<>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Order #{order.order_number}</Typography>
                  <Chip label={order.status} size="small" sx={{ ml: 1 }} />
                </>}
                secondary={<>
                  <Typography variant="body2" color="text.secondary">Placed: {new Date(order.created_at).toLocaleString()}</Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>{order.items_summary}</Typography>
                  {order.status === 'paid_waiting_preparation' && (
                    <Box sx={{ mt: 1 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        onClick={() => handleStatusUpdate(order.order_id, 'preparing')}
                        disabled={updatingId === order.order_id}
                      >
                        {updatingId === order.order_id ? <CircularProgress size={18} /> : 'Mark as In Progress'}
                      </Button>
                    </Box>
                  )}
                  {order.status === 'preparing' && (
                    <Box sx={{ mt: 1 }}>
                      <Button
                        variant="contained"
                        color="success"
                        size="small"
                        onClick={() => handleStatusUpdate(order.order_id, 'ready_for_pickup')}
                        disabled={updatingId === order.order_id}
                      >
                        {updatingId === order.order_id ? <CircularProgress size={18} /> : 'Mark as Ready'}
                      </Button>
                    </Box>
                  )}
                </>}
              />
            </ListItem>
          ))}
        </List>
      )}
      <Snackbar open={!!success} autoHideDuration={2000} onClose={() => setSuccess('')} anchorOrigin={{ vertical: 'top', horizontal: 'center' }}>
        <Alert onClose={() => setSuccess('')} severity="success" sx={{ width: '100%' }}>{success}</Alert>
      </Snackbar>
    </Paper>
  );
}

function DashboardBarista({ user, onLogout }) {
  return (
    <div style={{ padding: '20px' }}>
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        paddingBottom: '10px',
        borderBottom: '1px solid #eee'
      }}>
      <h2>Barista Dashboard</h2>
        <div>
          <span style={{ marginRight: '15px' }}>Welcome, {user.full_name || user.username}!</span>
          <button
            onClick={onLogout}
            style={{
              padding: '5px 15px',
              backgroundColor: '#dc3545',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
      </header>
      <Box sx={{ width: '100%', bgcolor: 'background.paper', borderRadius: 2, boxShadow: 1, mb: 2 }}>
        <BaristaOrdersList />
      </Box>
    </div>
  );
}

export default DashboardBarista; 
