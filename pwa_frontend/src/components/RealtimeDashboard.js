import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Grid, Card, CardContent, Avatar, Chip,
  LinearProgress, Alert, IconButton, Badge, Menu, MenuItem, 
  List, ListItem, ListItemText, ListItemIcon, Divider
} from '@mui/material';
import { 
  TrendingUp, AttachMoney, ShoppingCart, Schedule, Timeline,
  Refresh, Notifications, NotificationsActive, Clear,
  Wifi, WifiOff, Circle
} from '@mui/icons-material';
import { useRealtime } from '../contexts/RealtimeContext';

const StatCard = ({ title, value, icon, color = 'primary', subtitle, trend }) => (
    <Card elevation={2} sx={{ borderRadius: 2, height: '100%' }}>
        <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Avatar sx={{ bgcolor: `${color}.main`, mr: 2, width: 40, height: 40 }}>
                        {icon}
                    </Avatar>
                    <Box>
                        <Typography variant="h6" color="text.secondary" sx={{ fontSize: '0.9rem' }}>
                            {title}
                        </Typography>
                        {subtitle && (
                            <Typography variant="caption" color="text.disabled">
                                {subtitle}
                            </Typography>
                        )}
                    </Box>
                </Box>
                {trend && (
                    <Chip 
                        label={trend} 
                        size="small" 
                        color={trend.startsWith('+') ? 'success' : 'default'}
                        sx={{ fontSize: '0.7rem' }}
                    />
                )}
            </Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: `${color}.main` }}>
                {value}
            </Typography>
        </CardContent>
    </Card>
);

const RealtimeDashboard = () => {
    const { connected, dashboardData, activeOrders, notifications, removeNotification, clearNotifications } = useRealtime();
    const [anchorEl, setAnchorEl] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    useEffect(() => {
        if (dashboardData) {
            setLastUpdate(new Date(dashboardData.timestamp));
        }
    }, [dashboardData]);

    const handleNotificationClick = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleNotificationClose = () => {
        setAnchorEl(null);
    };

    const formatCurrency = (amount) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    };

    const formatTime = (dateString) => {
        return new Date(dateString).toLocaleTimeString();
    };

    const getStatusColor = (status) => {
        const colors = {
            'pending_payment': 'warning',
            'paid_waiting_preparation': 'info',
            'preparing': 'primary',
            'ready_for_pickup': 'success',
            'completed': 'default'
        };
        return colors[status] || 'default';
    };

    const getStatusText = (status) => {
        const texts = {
            'pending_payment': 'Pending Payment',
            'paid_waiting_preparation': 'Waiting Prep',
            'preparing': 'Preparing',
            'ready_for_pickup': 'Ready',
            'completed': 'Completed'
        };
        return texts[status] || status;
    };

    if (!dashboardData) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="info" sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {connected ? <Wifi /> : <WifiOff />}
                        {connected ? 'Connected - Loading dashboard data...' : 'Connecting to real-time server...'}
                    </Box>
                </Alert>
                <LinearProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header with Connection Status and Notifications */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Box>
                    <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                        Real-time Dashboard
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Chip 
                            icon={connected ? <Wifi /> : <WifiOff />}
                            label={connected ? 'Connected' : 'Disconnected'}
                            color={connected ? 'success' : 'error'}
                            size="small"
                        />
                        {lastUpdate && (
                            <Typography variant="caption" color="text.secondary">
                                Last updated: {formatTime(lastUpdate)}
                            </Typography>
                        )}
                    </Box>
                </Box>
                
                <Box>
                    <IconButton 
                        onClick={handleNotificationClick}
                        color={notifications.length > 0 ? 'primary' : 'default'}
                    >
                        <Badge badgeContent={notifications.length} color="error">
                            {notifications.length > 0 ? <NotificationsActive /> : <Notifications />}
                        </Badge>
                    </IconButton>
                    
                    <Menu
                        anchorEl={anchorEl}
                        open={Boolean(anchorEl)}
                        onClose={handleNotificationClose}
                        PaperProps={{ sx: { width: 350, maxHeight: 400 } }}
                    >
                        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography variant="h6">Notifications</Typography>
                            {notifications.length > 0 && (
                                <IconButton size="small" onClick={clearNotifications}>
                                    <Clear />
                                </IconButton>
                            )}
                        </Box>
                        <Divider />
                        {notifications.length === 0 ? (
                            <MenuItem disabled>
                                <Typography variant="body2" color="text.secondary">
                                    No new notifications
                                </Typography>
                            </MenuItem>
                        ) : (
                            notifications.map((notification) => (
                                <MenuItem 
                                    key={notification.id}
                                    onClick={() => removeNotification(notification.id)}
                                >
                                    <ListItemIcon>
                                        <Circle color={notification.type === 'new_order' ? 'success' : 'info'} />
                                    </ListItemIcon>
                                    <ListItemText
                                        primary={notification.message}
                                        secondary={formatTime(notification.timestamp)}
                                    />
                                </MenuItem>
                            ))
                        )}
                    </Menu>
                </Box>
            </Box>

            {/* Key Metrics Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Today's Sales"
                        value={formatCurrency(dashboardData.today_sales || 0)}
                        icon={<AttachMoney />}
                        color="success"
                        subtitle="Total revenue"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Orders Today"
                        value={dashboardData.today_orders || 0}
                        icon={<ShoppingCart />}
                        color="primary"
                        subtitle="Completed orders"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Average Order"
                        value={formatCurrency(dashboardData.average_order_value || 0)}
                        icon={<TrendingUp />}
                        color="info"
                        subtitle="Per order"
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="Active Orders"
                        value={dashboardData.active_orders || 0}
                        icon={<Schedule />}
                        color="warning"
                        subtitle="In queue"
                    />
                </Grid>
            </Grid>

            {/* Charts and Active Orders */}
            <Grid container spacing={3}>
                {/* Hourly Sales Chart */}
                {dashboardData.hourly_sales && dashboardData.hourly_sales.length > 0 && (
                    <Grid item xs={12} md={8}>
                        <Paper sx={{ p: 3, borderRadius: 2 }}>
                            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Timeline />
                                Today's Sales by Hour
                            </Typography>
                            <Box sx={{ display: 'flex', gap: 1, overflowX: 'auto', pb: 1 }}>
                                {dashboardData.hourly_sales.map((hour) => (
                                    <Box key={hour.hour} sx={{ minWidth: 80, textAlign: 'center' }}>
                                        <Box 
                                            sx={{ 
                                                height: Math.max(20, (hour.sales / Math.max(...dashboardData.hourly_sales.map(h => h.sales))) * 100),
                                                bgcolor: 'primary.main',
                                                borderRadius: 1,
                                                mb: 1,
                                                minHeight: 20
                                            }}
                                        />
                                        <Typography variant="caption" sx={{ fontSize: '0.7rem' }}>
                                            {hour.hour}
                                        </Typography>
                                        <Typography variant="caption" display="block" sx={{ fontSize: '0.7rem', fontWeight: 'bold' }}>
                                            ${hour.sales.toFixed(0)}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Paper>
                    </Grid>
                )}

                {/* Active Orders List */}
                <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 3, borderRadius: 2, maxHeight: 400, overflow: 'auto' }}>
                        <Typography variant="h6" sx={{ mb: 2 }}>
                            Active Orders ({activeOrders.length})
                        </Typography>
                        {activeOrders.length === 0 ? (
                            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                                No active orders
                            </Typography>
                        ) : (
                            <List dense>
                                {activeOrders.map((order) => (
                                    <ListItem key={order.id} sx={{ px: 0 }}>
                                        <ListItemText
                                            primary={
                                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        Order #{order.id}
                                                    </Typography>
                                                    <Chip
                                                        label={getStatusText(order.status)}
                                                        size="small"
                                                        color={getStatusColor(order.status)}
                                                    />
                                                </Box>
                                            }
                                            secondary={
                                                <Box>
                                                    <Typography variant="caption">
                                                        {formatCurrency(order.total_amount)} • {order.items_count} items
                                                    </Typography>
                                                    <br />
                                                    <Typography variant="caption" color="text.disabled">
                                                        {formatTime(order.created_at)}
                                                    </Typography>
                                                </Box>
                                            }
                                        />
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </Paper>
                </Grid>
            </Grid>
        </Box>
    );
};

export default RealtimeDashboard;