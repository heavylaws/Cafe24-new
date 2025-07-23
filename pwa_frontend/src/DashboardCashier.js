import React, { useState, useEffect } from 'react';
import OrderPlacement from './components/OrderPlacement';
import { 
  Tabs, Tab, Box, AppBar, Paper, Typography, 
  Chip, CircularProgress, Alert, Button, Snackbar, Container, Avatar, Stack
} from '@mui/material';
import { ShoppingCart, History, Add, CheckCircle } from '@mui/icons-material';

function ActiveOrdersList() {
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

  const handleMarkAsPaid = async (orderId) => {
    setUpdatingId(orderId);
    setError('');
    setSuccess('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5000'}/api/v1/orders/${orderId}/status`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ status: 'paid_waiting_preparation', payment_method: 'cash' })
      });
      if (!res.ok) throw new Error('Failed to update order status');
      setSuccess('Order marked as paid!');
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
    <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <ShoppingCart sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          Active Orders
        </Typography>
      </Box>
      
      {orders.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <ShoppingCart sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No active orders
          </Typography>
          <Typography color="text.secondary">
            New orders will appear here automatically
          </Typography>
        </Box>
      ) : (
        <Stack spacing={2}>
          {orders.map(order => (
            <Paper key={order.order_id} elevation={2} sx={{ p: 2, borderRadius: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Order #{order.order_number}
                  </Typography>
                  <Chip 
                    label={order.status} 
                    size="small" 
                    color={order.status === 'pending_payment' ? 'warning' : 'info'}
                    sx={{ mt: 1 }}
                  />
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                    ${(parseFloat(order.final_total_usd) || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {order.final_total_lbp ? order.final_total_lbp.toLocaleString() : '0'} LBP
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Placed: {new Date(order.created_at).toLocaleString()}
              </Typography>

              {order.subtotal_usd && order.subtotal_usd !== order.final_total_usd && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" color="success.main">
                    Subtotal: ${(parseFloat(order.subtotal_usd) || 0).toFixed(2)} ({order.subtotal_lbp?.toLocaleString()} LBP)
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    Discount: -${((parseFloat(order.subtotal_usd) || 0) - (parseFloat(order.final_total_usd) || 0)).toFixed(2)} 
                    ({order.discount_total_lbp ? order.discount_total_lbp.toLocaleString() : '0'} LBP)
                  </Typography>
                </Box>
              )}

              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Items:</Typography>
                <Stack spacing={1}>
                  {order.items?.map((item, idx) => (
                    <Box key={idx} sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ width: 32, height: 32, mr: 1, fontSize: '1rem' }}>
                        {item.quantity}
                      </Avatar>
                      <Typography variant="body2">
                        {item.menu_item_name}
                        {item.chosen_option_choice_name ? ` (${item.chosen_option_choice_name})` : ''}
                        {(parseFloat(item.item_discount_amount_usd) || 0) > 0 && (
                          <Chip 
                            label={`-$${(parseFloat(item.item_discount_amount_usd) || 0).toFixed(2)}`}
                            size="small" 
                            color="success"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Box>

              {order.status === 'pending_payment' && (
                <Button
                  variant="contained"
                  color="success"
                  onClick={() => handleMarkAsPaid(order.order_id)}
                  disabled={updatingId === order.order_id}
                  startIcon={updatingId === order.order_id ? <CircularProgress size={18} /> : <CheckCircle />}
                  sx={{ borderRadius: 25 }}
                >
                  {updatingId === order.order_id ? 'Processing...' : 'Mark as Paid'}
                </Button>
              )}
            </Paper>
          ))}
        </Stack>
      )}
      
      <Snackbar open={!!success} autoHideDuration={2000} onClose={() => setSuccess('')}>
        <Alert onClose={() => setSuccess('')} severity="success">{success}</Alert>
      </Snackbar>
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
    <Paper elevation={3} sx={{ p: 3, borderRadius: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <History sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          Order History
        </Typography>
      </Box>
      
      {orders.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <History sx={{ fontSize: 64, opacity: 0.3, mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No completed orders
          </Typography>
          <Typography color="text.secondary">
            Completed orders will appear here
          </Typography>
        </Box>
      ) : (
        <Stack spacing={2}>
          {orders.map(order => (
            <Paper key={order.order_id} elevation={1} sx={{ p: 2, borderRadius: 2, opacity: 0.8 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                    Order #{order.order_number}
                  </Typography>
                  <Chip 
                    label={order.status} 
                    size="small" 
                    color="success"
                    sx={{ mt: 1 }}
                  />
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h6" color="primary" sx={{ fontWeight: 'bold' }}>
                    ${(parseFloat(order.final_total_usd) || 0).toFixed(2)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {order.final_total_lbp ? order.final_total_lbp.toLocaleString() : '0'} LBP
                  </Typography>
                </Box>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Completed: {new Date(order.updated_at || order.created_at).toLocaleString()}
              </Typography>

              {order.subtotal_usd && order.subtotal_usd !== order.final_total_usd && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="body2" color="success.main">
                    Subtotal: ${(parseFloat(order.subtotal_usd) || 0).toFixed(2)} ({order.subtotal_lbp?.toLocaleString()} LBP)
                  </Typography>
                  <Typography variant="body2" color="success.main">
                    Discount: -${((parseFloat(order.subtotal_usd) || 0) - (parseFloat(order.final_total_usd) || 0)).toFixed(2)} 
                    ({order.discount_total_lbp ? order.discount_total_lbp.toLocaleString() : '0'} LBP)
                  </Typography>
                </Box>
              )}

              <Box>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>Items:</Typography>
                <Stack spacing={1}>
                  {order.items?.map((item, idx) => (
                    <Box key={idx} sx={{ display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ width: 32, height: 32, mr: 1, fontSize: '1rem' }}>
                        {item.quantity}
                      </Avatar>
                      <Typography variant="body2">
                        {item.menu_item_name}
                        {item.chosen_option_choice_name ? ` (${item.chosen_option_choice_name})` : ''}
                        {(parseFloat(item.item_discount_amount_usd) || 0) > 0 && (
                          <Chip 
                            label={`-$${(parseFloat(item.item_discount_amount_usd) || 0).toFixed(2)}`}
                            size="small" 
                            color="success"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              </Box>
            </Paper>
          ))}
        </Stack>
      )}
    </Paper>
  );
}

function DashboardCashier({ user, onLogout }) {
  const [tab, setTab] = useState(0);
  const handleTabChange = (event, newValue) => setTab(newValue);

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      p: 2 
    }}>
      <Container maxWidth="xl">
        {/* Header */}
        <Paper elevation={3} sx={{ 
          p: 3, 
          mb: 3,
          borderRadius: 3,
          background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
          color: 'white'
        }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                💰 Cashier Dashboard
              </Typography>
              <Typography variant="h6" sx={{ opacity: 0.9 }}>
                Welcome, {user.full_name || user.username}!
              </Typography>
            </Box>
            <Button 
              onClick={onLogout} 
              variant="outlined"
              sx={{
                color: 'white',
                borderColor: 'white',
                borderRadius: 25,
                px: 3,
                '&:hover': {
                  borderColor: 'white',
                  backgroundColor: 'rgba(255,255,255,0.1)'
                }
              }}
            >
              Logout
            </Button>
          </Box>
        </Paper>

        {/* Main Content */}
        <Paper elevation={3} sx={{ borderRadius: 3, overflow: 'hidden' }}>
          <AppBar position="static" color="default" elevation={0}>
            <Tabs
              value={tab}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              <Tab 
                label="New Order" 
                icon={<Add />}
                sx={{ py: 2 }}
              />
              <Tab 
                label="Active Orders" 
                icon={<ShoppingCart />}
                sx={{ py: 2 }}
              />
              <Tab 
                label="Order History" 
                icon={<History />}
                sx={{ py: 2 }}
              />
            </Tabs>
          </AppBar>
          
          <Box sx={{ minHeight: '70vh' }}>
            {tab === 0 && <OrderPlacement userRole="cashier" />}
            {tab === 1 && <Box sx={{ p: 3 }}><ActiveOrdersList /></Box>}
            {tab === 2 && <Box sx={{ p: 3 }}><CompletedOrdersList /></Box>}
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}

export default DashboardCashier; 
