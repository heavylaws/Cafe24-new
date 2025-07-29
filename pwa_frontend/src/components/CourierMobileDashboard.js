import React, { useState, useEffect } from 'react';
import { 
  Box, Paper, Typography, List, ListItem, ListItemText, Chip, 
  CircularProgress, Alert, Button, Card, CardContent, Avatar,
  Badge, IconButton, AppBar, Toolbar, BottomNavigation, 
  BottomNavigationAction, Fab, SwipeableDrawer, Divider,
  useTheme, useMediaQuery
} from '@mui/material';
import { 
  LocalShipping, Assignment, History, Notifications, 
  CheckCircle, AccessTime, NavigationRounded, PhoneRounded,
  Refresh, MenuRounded
} from '@mui/icons-material';
import { useRealtime } from '../contexts/RealtimeContext';

const CourierMobileDashboard = ({ user, onLogout }) => {
  const [bottomNavValue, setBottomNavValue] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { connected, activeOrders, notifications } = useRealtime();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  // Filter orders relevant to courier
  const deliveryOrders = activeOrders.filter(order => 
    order.status === 'ready_for_pickup' || order.status === 'completed'
  );

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
    } catch (err) {
      console.error('Failed to update order status:', err);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      'ready_for_pickup': 'warning',
      'completed': 'success'
    };
    return colors[status] || 'default';
  };

  const OrderCard = ({ order }) => (
    <Card 
      sx={{ 
        mb: 2, 
        borderRadius: 3,
        boxShadow: theme.shadows[2],
        '&:hover': { boxShadow: theme.shadows[4] }
      }}
    >
      <CardContent sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ bgcolor: theme.palette.primary.main, width: 32, height: 32 }}>
              <Assignment fontSize="small" />
            </Avatar>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Order #{order.id}
            </Typography>
          </Box>
          <Chip
            label={order.status === 'ready_for_pickup' ? 'Ready' : 'Completed'}
            color={getStatusColor(order.status)}
            size="small"
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AccessTime fontSize="small" />
            Ordered: {formatTime(order.created_at)}
          </Typography>
          <Typography variant="h6" color="primary.main" sx={{ fontWeight: 'bold' }}>
            {formatCurrency(order.total_amount)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {order.items_count} items
          </Typography>
        </Box>

        {order.status === 'ready_for_pickup' && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              variant="contained"
              color="success"
              size="small"
              startIcon={<CheckCircle />}
              onClick={() => handleUpdateStatus(order.id, 'completed')}
              fullWidth
              sx={{ borderRadius: 2 }}
            >
              Mark as Delivered
            </Button>
            <IconButton 
              color="primary"
              sx={{ border: 1, borderColor: 'primary.main' }}
            >
              <NavigationRounded />
            </IconButton>
            <IconButton 
              color="primary"
              sx={{ border: 1, borderColor: 'primary.main' }}
            >
              <PhoneRounded />
            </IconButton>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const DeliveryTab = () => (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
          Delivery Queue
        </Typography>
        <Badge badgeContent={deliveryOrders.length} color="primary">
          <LocalShipping />
        </Badge>
      </Box>

      {!connected && (
        <Alert severity="warning" sx={{ mb: 2, borderRadius: 2 }}>
          Offline mode - Orders may not be real-time
        </Alert>
      )}

      {deliveryOrders.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <LocalShipping sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No deliveries ready
          </Typography>
          <Typography variant="body2" color="text.disabled">
            New orders will appear here automatically
          </Typography>
        </Card>
      ) : (
        deliveryOrders.map(order => (
          <OrderCard key={order.id} order={order} />
        ))
      )}
    </Box>
  );

  const StatsTab = () => {
    const todayCompleted = deliveryOrders.filter(order => 
      order.status === 'completed' && 
      new Date(order.created_at).toDateString() === new Date().toDateString()
    ).length;

    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
          Today's Stats
        </Typography>
        
        <Card sx={{ mb: 3, borderRadius: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h3" color="primary.main" sx={{ fontWeight: 'bold' }}>
                  {todayCompleted}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Deliveries Completed
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                <CheckCircle fontSize="large" />
              </Avatar>
            </Box>
          </CardContent>
        </Card>

        <Card sx={{ mb: 3, borderRadius: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Box>
                <Typography variant="h3" color="warning.main" sx={{ fontWeight: 'bold' }}>
                  {deliveryOrders.filter(o => o.status === 'ready_for_pickup').length}
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Pending Deliveries
                </Typography>
              </Box>
              <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                <LocalShipping fontSize="large" />
              </Avatar>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const NotificationsTab = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 3 }}>
        Notifications
      </Typography>
      
      {notifications.length === 0 ? (
        <Card sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Notifications sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            No new notifications
          </Typography>
        </Card>
      ) : (
        <List>
          {notifications.map(notification => (
            <React.Fragment key={notification.id}>
              <ListItem sx={{ px: 0, py: 2 }}>
                <ListItemText
                  primary={notification.message}
                  secondary={formatTime(notification.timestamp)}
                />
                <Chip 
                  label={notification.type.replace('_', ' ')} 
                  size="small"
                  color={notification.type === 'new_order' ? 'success' : 'info'}
                />
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      )}
    </Box>
  );

  return (
    <Box sx={{ 
      minHeight: '100vh', 
      bgcolor: 'background.default',
      pb: isMobile ? 8 : 0 
    }}>
      {/* Mobile App Bar */}
      <AppBar position="sticky" sx={{ bgcolor: 'primary.main' }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setDrawerOpen(true)}
          >
            <MenuRounded />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            Courier Dashboard
          </Typography>
          <Badge badgeContent={notifications.length} color="error">
            <IconButton color="inherit">
              <Notifications />
            </IconButton>
          </Badge>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ pb: isMobile ? 8 : 0 }}>
        {bottomNavValue === 0 && <DeliveryTab />}
        {bottomNavValue === 1 && <StatsTab />}
        {bottomNavValue === 2 && <NotificationsTab />}
      </Box>

      {/* Bottom Navigation */}
      {isMobile && (
        <BottomNavigation
          value={bottomNavValue}
          onChange={(event, newValue) => setBottomNavValue(newValue)}
          sx={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 1000,
            borderTop: 1,
            borderColor: 'divider'
          }}
        >
          <BottomNavigationAction 
            label="Deliveries" 
            icon={<Badge badgeContent={deliveryOrders.length} color="primary"><LocalShipping /></Badge>} 
          />
          <BottomNavigationAction label="Stats" icon={<Assignment />} />
          <BottomNavigationAction 
            label="Notifications" 
            icon={<Badge badgeContent={notifications.length} color="error"><Notifications /></Badge>} 
          />
        </BottomNavigation>
      )}

      {/* Refresh FAB */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: isMobile ? 80 : 16,
          right: 16,
          zIndex: 1000
        }}
        size="small"
      >
        <Refresh />
      </Fab>

      {/* Side Drawer */}
      <SwipeableDrawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onOpen={() => setDrawerOpen(true)}
      >
        <Box sx={{ width: 250, p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            {user.full_name || user.username}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Courier
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Button
            fullWidth
            variant="outlined"
            color="error"
            onClick={onLogout}
          >
            Logout
          </Button>
        </Box>
      </SwipeableDrawer>
    </Box>
  );
};

export default CourierMobileDashboard;