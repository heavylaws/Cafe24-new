import React, { useState, useEffect } from 'react';
import OrderPlacement from './components/OrderPlacement';
import { Tabs, Tab, Box, AppBar, Paper, Typography, List, ListItem, ListItemText, Chip, CircularProgress, Alert, Button } from '@mui/material';

function ActiveOrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

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
      const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/orders/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch orders');
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      setError('Failed to fetch active orders.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/orders/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });
      if (!res.ok) {
        throw new Error('Failed to update order status');
      }
      fetchOrders(); // Refresh the list
    } catch (err) {
      setError(err.message || 'Failed to update order status.');
    }
  };

  if (loading) return <Box sx={{ textAlign: 'center', mt: 4 }}><CircularProgress /> </Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Active Orders</Typography>
      {orders.length === 0 ? <Typography>No active orders.</Typography> : (
        <List>
          {orders.map(order => (
            <ListItem key={order.order_id} alignItems="flex-start" sx={{ mb: 2, borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between' }}>
              <ListItemText
                primary={<>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Order #{order.order_number}</Typography>
                  <Chip label={order.status} size="small" sx={{ ml: 1 }} />
                  <span style={{ float: 'right', fontWeight: 500 }}>${(parseFloat(order.final_total_usd) || 0).toFixed(2)}</span>
                </>}
                secondary={<>
                  <Typography variant="body2" color="text.secondary">Placed: {new Date(order.created_at).toLocaleString()}</Typography>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {order.items && order.items.map((item, idx) => (
                      <li key={idx}>{item.quantity}x {item.menu_item_name}{item.chosen_option_choice_name ? ` (${item.chosen_option_choice_name})` : ''}</li>
                    ))}
                  </ul>
                </>}
              />
              {order.status === 'ready_for_pickup' && (
                <Button
                  variant="contained"
                  color="primary"
                  size="small"
                  onClick={() => handleUpdateStatus(order.order_id, 'completed')}
                  sx={{ ml: 2, alignSelf: 'center' }}
                >
                  Mark as Completed
                </Button>
              )}
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
}

function CompletedOrdersList() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/orders/completed`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch orders');
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      setError('Failed to fetch completed orders.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Box sx={{ textAlign: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Order History</Typography>
      {orders.length === 0 ? <Typography>No completed orders.</Typography> : (
        <List>
          {orders.map(order => (
            <ListItem key={order.order_id} alignItems="flex-start" sx={{ mb: 2, borderBottom: '1px solid #eee' }}>
              <ListItemText
                primary={<>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Order #{order.order_number}</Typography>
                  <Chip label={order.status} size="small" sx={{ ml: 1 }} />
                  <span style={{ float: 'right', fontWeight: 500 }}>${(parseFloat(order.final_total_usd) || 0).toFixed(2)}</span>
                </>}
                secondary={<>
                  <Typography variant="body2" color="text.secondary">Placed: {new Date(order.created_at).toLocaleString()}</Typography>
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {order.items && order.items.map((item, idx) => (
                      <li key={idx}>{item.quantity}x {item.menu_item_name}{item.chosen_option_choice_name ? ` (${item.chosen_option_choice_name})` : ''}</li>
                    ))}
                  </ul>
                </>}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  );
}

function DashboardCourier({ user, onLogout }) {
  const [tab, setTab] = useState(0);
  const handleTabChange = (event, newValue) => setTab(newValue);

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
      <h2>Courier Dashboard</h2>
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
        <AppBar position="static" color="default" elevation={0} sx={{ borderRadius: 2 }}>
          <Tabs
            value={tab}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
            aria-label="courier dashboard tabs"
          >
            <Tab label="New Order" />
            <Tab label="Active Orders" />
            <Tab label="Order History" />
          </Tabs>
        </AppBar>
        <Box sx={{ p: 3 }}>
          {tab === 0 && <OrderPlacement userRole="courier" />}
          {tab === 1 && <ActiveOrdersList />}
          {tab === 2 && <CompletedOrdersList />}
        </Box>
      </Box>
    </div>
  );
}

export default DashboardCourier; 
