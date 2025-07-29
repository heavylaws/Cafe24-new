from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room, rooms
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app import socketio, db
from app.models import Order, User, OrderStatus, UserRole
from app.utils.decorators import roles_required
from datetime import datetime, timedelta
import logging

# Store connected users and their roles
connected_users = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection to WebSocket"""
    try:
        # Verify JWT token from query params for websocket authentication
        token = request.args.get('token')
        if not token:
            logging.warning("WebSocket connection attempted without token")
            return False
        
        # Manual JWT verification for WebSocket
        try:
            from flask_jwt_extended import decode_token
            decoded_token = decode_token(token)
            user_id = decoded_token['sub']
            
            # Get user info
            user = User.query.get(user_id)
            if not user:
                logging.warning(f"WebSocket connection attempted with invalid user: {user_id}")
                return False
            
            # Store user info for this session
            connected_users[request.sid] = {
                'user_id': user_id,
                'username': user.username,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
            }
            
            # Join role-based rooms
            join_room(f"role_{user.role.value if hasattr(user.role, 'value') else str(user.role)}")
            join_room(f"user_{user_id}")
            
            logging.info(f"User {user.username} connected to WebSocket")
            emit('connection_established', {
                'status': 'connected',
                'user': user.username,
                'role': user.role.value if hasattr(user.role, 'value') else str(user.role)
            })
            
            # Send initial dashboard data based on role
            if user.role in [UserRole.manager, UserRole.cashier]:
                emit_real_time_dashboard_data()
            
        except Exception as e:
            logging.error(f"JWT verification failed for WebSocket: {e}")
            return False
            
    except Exception as e:
        logging.error(f"WebSocket connection error: {e}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    if request.sid in connected_users:
        user_info = connected_users[request.sid]
        logging.info(f"User {user_info['username']} disconnected from WebSocket")
        del connected_users[request.sid]

@socketio.on('subscribe_to_analytics')
def handle_analytics_subscription(data):
    """Handle subscription to real-time analytics"""
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    user_info = connected_users[request.sid]
    if user_info['role'] not in ['manager', 'cashier']:
        emit('error', {'message': 'Insufficient permissions'})
        return
    
    join_room('analytics_subscribers')
    emit('analytics_subscribed', {'status': 'subscribed'})
    
    # Send initial analytics data
    emit_real_time_dashboard_data()

@socketio.on('subscribe_to_orders')
def handle_orders_subscription(data):
    """Handle subscription to real-time order updates"""
    if request.sid not in connected_users:
        emit('error', {'message': 'Not authenticated'})
        return
    
    join_room('order_subscribers')
    emit('orders_subscribed', {'status': 'subscribed'})
    
    # Send current active orders
    emit_active_orders()

def emit_real_time_dashboard_data():
    """Emit real-time dashboard data to subscribed clients"""
    try:
        # Calculate today's metrics
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get today's completed orders
        today_orders = Order.query.filter(
            Order.created_at >= today_start,
            Order.created_at < today_end,
            Order.status == OrderStatus.completed
        ).all()
        
        total_sales = sum(float(order.total_amount) for order in today_orders)
        total_orders = len(today_orders)
        average_order_value = total_sales / total_orders if total_orders > 0 else 0
        
        # Get active orders count
        active_orders = Order.query.filter(
            Order.status.in_([
                OrderStatus.paid_waiting_preparation,
                OrderStatus.preparing,
                OrderStatus.ready_for_pickup
            ])
        ).count()
        
        # Get hourly sales for today
        hourly_sales = []
        current_hour = datetime.utcnow().hour
        
        for hour in range(max(0, current_hour - 6), current_hour + 1):
            hour_start = today_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_orders = Order.query.filter(
                Order.created_at >= hour_start,
                Order.created_at < hour_end,
                Order.status == OrderStatus.completed
            ).all()
            
            hour_sales = sum(float(order.total_amount) for order in hour_orders)
            hourly_sales.append({
                'hour': f"{hour:02d}:00",
                'sales': hour_sales,
                'orders': len(hour_orders)
            })
        
        dashboard_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'today_sales': round(total_sales, 2),
            'today_orders': total_orders,
            'average_order_value': round(average_order_value, 2),
            'active_orders': active_orders,
            'hourly_sales': hourly_sales
        }
        
        socketio.emit('dashboard_update', dashboard_data, room='analytics_subscribers')
        
    except Exception as e:
        logging.error(f"Error emitting dashboard data: {e}")

def emit_active_orders():
    """Emit current active orders to subscribed clients"""
    try:
        active_orders = Order.query.filter(
            Order.status.in_([
                OrderStatus.pending_payment,
                OrderStatus.paid_waiting_preparation,
                OrderStatus.preparing,
                OrderStatus.ready_for_pickup
            ])
        ).order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in active_orders:
            orders_data.append({
                'id': order.id,
                'status': order.status.value if hasattr(order.status, 'value') else str(order.status),
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'user_id': order.user_id,
                'items_count': len(order.order_items)
            })
        
        socketio.emit('active_orders_update', {
            'timestamp': datetime.utcnow().isoformat(),
            'orders': orders_data
        }, room='order_subscribers')
        
    except Exception as e:
        logging.error(f"Error emitting active orders: {e}")

def emit_order_status_change(order_id, new_status, old_status=None):
    """Emit order status change to all relevant clients"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return
        
        update_data = {
            'order_id': order_id,
            'new_status': new_status,
            'old_status': old_status,
            'timestamp': datetime.utcnow().isoformat(),
            'order_details': {
                'id': order.id,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'user_id': order.user_id
            }
        }
        
        # Emit to order subscribers
        socketio.emit('order_status_changed', update_data, room='order_subscribers')
        
        # Emit to analytics subscribers if order affects metrics
        if new_status in ['completed', 'cancelled']:
            emit_real_time_dashboard_data()
        
        # Also emit updated active orders
        emit_active_orders()
        
    except Exception as e:
        logging.error(f"Error emitting order status change: {e}")

def emit_new_order(order_id):
    """Emit new order notification"""
    try:
        order = Order.query.get(order_id)
        if not order:
            return
        
        new_order_data = {
            'order_id': order_id,
            'timestamp': datetime.utcnow().isoformat(),
            'order_details': {
                'id': order.id,
                'status': order.status.value if hasattr(order.status, 'value') else str(order.status),
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'user_id': order.user_id,
                'items_count': len(order.order_items)
            }
        }
        
        # Emit to all relevant users
        socketio.emit('new_order', new_order_data, room='order_subscribers')
        
        # Update dashboard data
        emit_real_time_dashboard_data()
        emit_active_orders()
        
    except Exception as e:
        logging.error(f"Error emitting new order: {e}")

# Blueprint for real-time API endpoints
realtime_bp = Blueprint('realtime_bp', __name__)

@realtime_bp.route('/dashboard/live-stats', methods=['GET'])
@jwt_required()
@roles_required('manager', 'cashier')
def get_live_dashboard_stats():
    """Get current dashboard statistics"""
    try:
        # This endpoint provides the same data as WebSocket for HTTP clients
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        today_orders = Order.query.filter(
            Order.created_at >= today_start,
            Order.created_at < today_end,
            Order.status == OrderStatus.completed
        ).all()
        
        total_sales = sum(float(order.total_amount) for order in today_orders)
        total_orders = len(today_orders)
        
        active_orders = Order.query.filter(
            Order.status.in_([
                OrderStatus.paid_waiting_preparation,
                OrderStatus.preparing,
                OrderStatus.ready_for_pickup
            ])
        ).count()
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'today_sales': round(total_sales, 2),
            'today_orders': total_orders,
            'average_order_value': round(total_sales / total_orders if total_orders > 0 else 0, 2),
            'active_orders': active_orders
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting live dashboard stats: {e}")
        return jsonify({'message': 'Could not fetch live dashboard stats'}), 500

@realtime_bp.route('/orders/active-live', methods=['GET'])
@jwt_required()
def get_active_orders_live():
    """Get current active orders (HTTP endpoint)"""
    try:
        active_orders = Order.query.filter(
            Order.status.in_([
                OrderStatus.pending_payment,
                OrderStatus.paid_waiting_preparation,
                OrderStatus.preparing,
                OrderStatus.ready_for_pickup
            ])
        ).order_by(Order.created_at.desc()).all()
        
        orders_data = []
        for order in active_orders:
            orders_data.append({
                'id': order.id,
                'status': order.status.value if hasattr(order.status, 'value') else str(order.status),
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat(),
                'user_id': order.user_id,
                'items_count': len(order.order_items)
            })
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'orders': orders_data
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting active orders: {e}")
        return jsonify({'message': 'Could not fetch active orders'}), 500