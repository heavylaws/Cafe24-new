import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { io } from 'socket.io-client';

const RealtimeContext = createContext();

export const useRealtime = () => {
    const context = useContext(RealtimeContext);
    if (!context) {
        throw new Error('useRealtime must be used within a RealtimeProvider');
    }
    return context;
};

export const RealtimeProvider = ({ children }) => {
    const [socket, setSocket] = useState(null);
    const [connected, setConnected] = useState(false);
    const [dashboardData, setDashboardData] = useState(null);
    const [activeOrders, setActiveOrders] = useState([]);
    const [notifications, setNotifications] = useState([]);

    const connectSocket = useCallback(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            console.log('No token available for WebSocket connection');
            return;
        }

        const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
        
        const newSocket = io(API_BASE_URL, {
            query: { token },
            transports: ['websocket', 'polling'],
            timeout: 20000,
            forceNew: true
        });

        newSocket.on('connect', () => {
            console.log('Connected to WebSocket server');
            setConnected(true);
            setSocket(newSocket);
        });

        newSocket.on('disconnect', () => {
            console.log('Disconnected from WebSocket server');
            setConnected(false);
        });

        newSocket.on('connection_established', (data) => {
            console.log('WebSocket connection established:', data);
            // Subscribe to relevant updates based on user role
            if (data.role === 'manager' || data.role === 'cashier') {
                newSocket.emit('subscribe_to_analytics');
            }
            newSocket.emit('subscribe_to_orders');
        });

        newSocket.on('dashboard_update', (data) => {
            console.log('Dashboard update received:', data);
            setDashboardData(data);
        });

        newSocket.on('active_orders_update', (data) => {
            console.log('Active orders update received:', data);
            setActiveOrders(data.orders || []);
        });

        newSocket.on('order_status_changed', (data) => {
            console.log('Order status changed:', data);
            // Add notification
            setNotifications(prev => [{
                id: Date.now(),
                type: 'order_status',
                message: `Order #${data.order_id} status changed to ${data.new_status}`,
                timestamp: data.timestamp,
                data: data
            }, ...prev.slice(0, 9)]); // Keep only last 10 notifications
        });

        newSocket.on('new_order', (data) => {
            console.log('New order received:', data);
            // Add notification
            setNotifications(prev => [{
                id: Date.now(),
                type: 'new_order',
                message: `New order #${data.order_id} received`,
                timestamp: data.timestamp,
                data: data
            }, ...prev.slice(0, 9)]);
        });

        newSocket.on('analytics_subscribed', (data) => {
            console.log('Subscribed to analytics updates');
        });

        newSocket.on('orders_subscribed', (data) => {
            console.log('Subscribed to order updates');
        });

        newSocket.on('error', (error) => {
            console.error('WebSocket error:', error);
        });

        newSocket.on('connect_error', (error) => {
            console.error('WebSocket connection error:', error);
        });

        return newSocket;
    }, []);

    const disconnectSocket = useCallback(() => {
        if (socket) {
            socket.disconnect();
            setSocket(null);
            setConnected(false);
        }
    }, [socket]);

    const clearNotifications = useCallback(() => {
        setNotifications([]);
    }, []);

    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    useEffect(() => {
        // Connect when component mounts if we have a token
        const token = localStorage.getItem('token');
        if (token) {
            const newSocket = connectSocket();
            setSocket(newSocket);

            return () => {
                if (newSocket) {
                    newSocket.disconnect();
                }
            };
        }
    }, [connectSocket]);

    // Reconnect when token changes (login/logout)
    useEffect(() => {
        const handleStorageChange = (e) => {
            if (e.key === 'token') {
                if (e.newValue) {
                    // Token added - connect
                    if (!socket || !connected) {
                        const newSocket = connectSocket();
                        setSocket(newSocket);
                    }
                } else {
                    // Token removed - disconnect
                    disconnectSocket();
                    setDashboardData(null);
                    setActiveOrders([]);
                    setNotifications([]);
                }
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [socket, connected, connectSocket, disconnectSocket]);

    const value = {
        socket,
        connected,
        dashboardData,
        activeOrders,
        notifications,
        connectSocket,
        disconnectSocket,
        clearNotifications,
        removeNotification
    };

    return (
        <RealtimeContext.Provider value={value}>
            {children}
        </RealtimeContext.Provider>
    );
};

export default RealtimeProvider;