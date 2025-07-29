import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import desc, func

from app.models import (
    Category,
    Ingredient,
    MenuItem,
    Order,
    OrderDiscount,
    OrderItem,
    OrderItemDiscount,
    OrderStatus,
    StockAdjustment,
    db,
)
from app.utils.decorators import roles_required

report_bp = Blueprint("report_bp", __name__)


@report_bp.route("/sales-summary", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_sales_summary():
    """Sales summary endpoint that matches frontend expectations."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        if end_date_str:
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
        else:
            end_date = start_date + datetime.timedelta(days=1)

        # Query for orders in date range
        orders_query = Order.query.filter(
            Order.created_at >= start_date,
            Order.created_at < end_date,
            Order.status == OrderStatus.completed,
        )

        # Calculate totals
        total_sales_usd = sum(float(order.total_amount) for order in orders_query.all())
        total_orders = orders_query.count()
        average_order_value_usd = (
            total_sales_usd / total_orders if total_orders > 0 else 0
        )

        # Get top selling items
        top_items = (
            db.session.query(
                MenuItem.name.label("item_name"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.line_total_usd_at_order).label("total_revenue_usd"),
            )
            .select_from(MenuItem)
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == OrderStatus.completed,
            )
            .group_by(MenuItem.name)
            .order_by(desc("total_quantity"))
            .limit(10)
            .all()
        )

        # Get sales by category
        category_sales = (
            db.session.query(
                Category.name.label("category_name"),
                func.sum(OrderItem.line_total_usd_at_order).label("total_revenue_usd"),
            )
            .select_from(Category)
            .join(MenuItem, Category.id == MenuItem.category_id)
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status == OrderStatus.completed,
            )
            .group_by(Category.name)
            .order_by(desc("total_revenue_usd"))
            .all()
        )

        # For now, set discounts to 0 (can be enhanced later)
        total_discounts_usd = 0.00

        return (
            jsonify(
                {
                    "total_sales_usd": round(total_sales_usd, 2),
                    "total_orders": total_orders,
                    "average_order_value_usd": round(average_order_value_usd, 2),
                    "total_discounts_usd": total_discounts_usd,
                    "top_selling_items": [
                        {
                            "item_name": item.item_name,
                            "total_quantity": int(item.total_quantity),
                            "total_revenue_usd": round(
                                float(item.total_revenue_usd), 2
                            ),
                        }
                        for item in top_items
                    ],
                    "sales_by_category": [
                        {
                            "category_name": cat.category_name,
                            "total_revenue_usd": round(float(cat.total_revenue_usd), 2),
                        }
                        for cat in category_sales
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        current_app.logger.error(f"Error in sales summary: {e}")
        return jsonify({"message": "Could not generate sales summary."}), 500


@report_bp.route("/daily-sales-summary", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_daily_sales_summary():
    """
    Manager: Get a summary of today's sales with dual currency support.
    For v0.1, this is simplified to current day only.
    """
    try:
        # Get today's date range
        today_start = datetime.datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start + datetime.timedelta(days=1)

        # Query for orders created today
        todays_orders_query = Order.query.filter(
            Order.created_at >= today_start,
            Order.created_at < today_end,
            Order.status.notin_(["cancelled"]),
        )

        orders_data = []
        total_sales_today = 0
        total_orders = 0

        for order in todays_orders_query.all():
            # Calculate order total from order items
            order_total = sum(
                float(item.price) * item.quantity for item in order.order_items
            )

            orders_data.append(
                {
                    "id": order.id,
                    "user_id": order.user_id,
                    "status": (
                        order.status.value
                        if hasattr(order.status, "value")
                        else str(order.status)
                    ),
                    "payment_method": (
                        order.payment_method.value
                        if order.payment_method
                        and hasattr(order.payment_method, "value")
                        else str(order.payment_method) if order.payment_method else None
                    ),
                    "total_amount": float(order.total_amount),
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat(),
                }
            )

            # For v0.1, consider completed orders as sales
            if order.status == OrderStatus.completed:
                total_sales_today += float(order.total_amount)
                total_orders += 1

        return (
            jsonify(
                {
                    "report_date": today_start.strftime("%Y-%m-%d"),
                    "total_sales": total_sales_today,
                    "total_orders": total_orders,
                    "orders": orders_data,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating daily sales summary: {e}")
        return jsonify({"message": "Could not generate daily sales summary."}), 500


@report_bp.route("/sales-by-item", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_sales_by_item():
    """Manager: Get sales breakdown by menu item for a date range."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            # Default to today
            start_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        if end_date_str:
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
        else:
            # Default to end of today
            end_date = start_date + datetime.timedelta(days=1)

        # Query for item sales in date range
        item_sales = (
            db.session.query(
                OrderItem.menu_item_name,
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.line_total_usd_at_order).label("total_sales_usd"),
                func.sum(OrderItem.line_total_lbp_rounded_at_order).label(
                    "total_sales_lbp"
                ),
                func.sum(OrderItem.discount_amount_usd).label("total_discounts_usd"),
                func.sum(OrderItem.discount_amount_lbp).label("total_discounts_lbp"),
            )
            .join(Order)
            .filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status.notin_(["cancelled_by_user", "cancelled_by_staff"]),
            )
            .group_by(OrderItem.menu_item_name)
            .order_by(desc("total_sales_usd"))
            .all()
        )

        items_data = []
        for item in item_sales:
            items_data.append(
                {
                    "menu_item_name": item.menu_item_name,
                    "total_quantity_sold": item.total_quantity,
                    "total_sales_usd": float(item.total_sales_usd),
                    "total_sales_lbp": item.total_sales_lbp,
                    "total_discounts_usd": float(item.total_discounts_usd or 0),
                    "total_discounts_lbp": item.total_discounts_lbp or 0,
                }
            )

        return (
            jsonify(
                {
                    "report_period": f"{start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}",
                    "items": items_data,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating sales by item report: {e}")
        return jsonify({"message": "Could not generate sales by item report."}), 500


@report_bp.route("/sales-by-category", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_sales_by_category():
    """Manager: Get sales breakdown by category for a date range."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        if end_date_str:
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
        else:
            end_date = start_date + datetime.timedelta(days=1)

        # Query for category sales in date range
        category_sales = (
            db.session.query(
                Category.name.label("category_name"),
                func.sum(OrderItem.quantity).label("total_quantity"),
                func.sum(OrderItem.line_total_usd_at_order).label("total_sales_usd"),
                func.sum(OrderItem.line_total_lbp_rounded_at_order).label(
                    "total_sales_lbp"
                ),
                func.sum(OrderItem.discount_amount_usd).label("total_discounts_usd"),
                func.sum(OrderItem.discount_amount_lbp).label("total_discounts_lbp"),
            )
            .join(Order)
            .join(MenuItem)
            .join(Category)
            .filter(
                Order.created_at >= start_date,
                Order.created_at < end_date,
                Order.status.notin_(["cancelled_by_user", "cancelled_by_staff"]),
            )
            .group_by(Category.name)
            .order_by(desc("total_sales_usd"))
            .all()
        )

        categories_data = []
        for category in category_sales:
            categories_data.append(
                {
                    "category_name": category.category_name,
                    "total_quantity_sold": category.total_quantity,
                    "total_sales_usd": float(category.total_sales_usd),
                    "total_sales_lbp": category.total_sales_lbp,
                    "total_discounts_usd": float(category.total_discounts_usd or 0),
                    "total_discounts_lbp": category.total_discounts_lbp or 0,
                }
            )

        return (
            jsonify(
                {
                    "report_period": f"{start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}",
                    "categories": categories_data,
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating sales by category report: {e}")
        return jsonify({"message": "Could not generate sales by category report."}), 500


@report_bp.route("/stock-levels", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_stock_levels():
    """Manager: Get current stock levels for all ingredients."""
    try:
        ingredients = (
            Ingredient.query.filter_by(is_active=True).order_by(Ingredient.name).all()
        )

        stock_data = []
        low_stock_items = []

        for ingredient in ingredients:
            stock_info = {
                "ingredient_id": ingredient.id,
                "name": ingredient.name,
                "unit": ingredient.unit,
                "current_stock": ingredient.current_stock,
                "min_stock_alert": ingredient.min_stock_alert,
                "is_low_stock": ingredient.current_stock <= ingredient.min_stock_alert,
            }
            stock_data.append(stock_info)

            if stock_info["is_low_stock"]:
                low_stock_items.append(stock_info)

        return (
            jsonify(
                {
                    "ingredients": stock_data,
                    "low_stock_count": len(low_stock_items),
                    "low_stock_items": low_stock_items,
                    "generated_at": datetime.datetime.utcnow().isoformat(),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating stock levels report: {e}")
        return jsonify({"message": "Could not generate stock levels report."}), 500


@report_bp.route("/stock-movements", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_stock_movements():
    """Manager: Get stock movement history for a date range."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")
        ingredient_id = request.args.get("ingredient_id", type=int)

        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        if end_date_str:
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
        else:
            end_date = start_date + datetime.timedelta(days=1)

        # Build query
        query = StockAdjustment.query.filter(
            StockAdjustment.created_at >= start_date,
            StockAdjustment.created_at < end_date,
        )

        if ingredient_id:
            query = query.filter(StockAdjustment.ingredient_id == ingredient_id)

        adjustments = query.order_by(desc(StockAdjustment.created_at)).all()

        movements_data = []
        for adjustment in adjustments:
            movements_data.append(
                {
                    "adjustment_id": adjustment.id,
                    "ingredient_name": adjustment.ingredient.name,
                    "ingredient_unit": adjustment.ingredient.unit,
                    "change_amount": adjustment.change_amount,
                    "reason": adjustment.reason,
                    "user_name": adjustment.user.full_name or adjustment.user.username,
                    "created_at": adjustment.created_at.isoformat(),
                }
            )

        return (
            jsonify(
                {
                    "report_period": f"{start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}",
                    "movements": movements_data,
                    "total_movements": len(movements_data),
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating stock movements report: {e}")
        return jsonify({"message": "Could not generate stock movements report."}), 500


@report_bp.route("/discount-usage", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_discount_usage():
    """Manager: Get discount usage report for a date range."""
    try:
        # Get date range from query parameters
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if start_date_str:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        else:
            start_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        if end_date_str:
            end_date = datetime.datetime.strptime(
                end_date_str, "%Y-%m-%d"
            ) + datetime.timedelta(days=1)
        else:
            end_date = start_date + datetime.timedelta(days=1)

        # Query order-level discounts
        order_discounts = (
            db.session.query(
                OrderDiscount.discount_name,
                func.count(OrderDiscount.id).label("usage_count"),
                func.sum(OrderDiscount.discount_amount_usd).label("total_discount_usd"),
                func.sum(OrderDiscount.discount_amount_lbp).label("total_discount_lbp"),
            )
            .filter(
                OrderDiscount.created_at >= start_date,
                OrderDiscount.created_at < end_date,
            )
            .group_by(OrderDiscount.discount_name)
            .all()
        )

        # Query item-level discounts
        item_discounts = (
            db.session.query(
                OrderItemDiscount.discount_name,
                func.count(OrderItemDiscount.id).label("usage_count"),
                func.sum(OrderItemDiscount.discount_amount_usd).label(
                    "total_discount_usd"
                ),
                func.sum(OrderItemDiscount.discount_amount_lbp).label(
                    "total_discount_lbp"
                ),
            )
            .filter(
                OrderItemDiscount.created_at >= start_date,
                OrderItemDiscount.created_at < end_date,
            )
            .group_by(OrderItemDiscount.discount_name)
            .all()
        )

        # Combine and format results
        discount_summary = {}

        for discount in order_discounts:
            discount_summary[discount.discount_name] = {
                "discount_name": discount.discount_name,
                "order_level_usage": discount.usage_count,
                "item_level_usage": 0,
                "total_usage": discount.usage_count,
                "total_discount_usd": float(discount.total_discount_usd),
                "total_discount_lbp": discount.total_discount_lbp,
            }

        for discount in item_discounts:
            if discount.discount_name in discount_summary:
                discount_summary[discount.discount_name][
                    "item_level_usage"
                ] = discount.usage_count
                discount_summary[discount.discount_name][
                    "total_usage"
                ] += discount.usage_count
                discount_summary[discount.discount_name]["total_discount_usd"] += float(
                    discount.total_discount_usd
                )
                discount_summary[discount.discount_name][
                    "total_discount_lbp"
                ] += discount.total_discount_lbp
            else:
                discount_summary[discount.discount_name] = {
                    "discount_name": discount.discount_name,
                    "order_level_usage": 0,
                    "item_level_usage": discount.usage_count,
                    "total_usage": discount.usage_count,
                    "total_discount_usd": float(discount.total_discount_usd),
                    "total_discount_lbp": discount.total_discount_lbp,
                }

        # Convert to list and sort by total discount amount
        discounts_data = sorted(
            list(discount_summary.values()),
            key=lambda x: x["total_discount_usd"],
            reverse=True,
        )

        # Calculate totals
        total_discount_usd = sum(d["total_discount_usd"] for d in discounts_data)
        total_discount_lbp = sum(d["total_discount_lbp"] for d in discounts_data)
        total_applications = sum(d["total_usage"] for d in discounts_data)

        return (
            jsonify(
                {
                    "report_period": f"{start_date.strftime('%Y-%m-%d')} to {(end_date - datetime.timedelta(days=1)).strftime('%Y-%m-%d')}",
                    "discounts": discounts_data,
                    "summary": {
                        "total_discount_usd": total_discount_usd,
                        "total_discount_lbp": total_discount_lbp,
                        "total_applications": total_applications,
                        "unique_discounts_used": len(discounts_data),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating discount usage report: {e}")
        return jsonify({"message": "Could not generate discount usage report."}), 500


@report_bp.route("/hourly-sales", methods=["GET"])
@jwt_required()
@roles_required("manager")
def get_hourly_sales():
    """Manager: Get hourly sales breakdown for a specific date."""
    try:
        # Get date from query parameters
        date_str = request.args.get("date")

        if date_str:
            target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        else:
            target_date = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        date_start = target_date
        date_end = target_date + datetime.timedelta(days=1)

        # Query orders for the date and group by hour
        hourly_data = []
        for hour in range(24):
            hour_start = date_start + datetime.timedelta(hours=hour)
            hour_end = hour_start + datetime.timedelta(hours=1)

            hour_orders = Order.query.filter(
                Order.created_at >= hour_start,
                Order.created_at < hour_end,
                Order.status.notin_(["cancelled_by_user", "cancelled_by_staff"]),
            ).all()

            hour_sales_usd = sum(
                float(order.final_total_usd)
                for order in hour_orders
                if order.status != "pending_payment"
            )
            hour_sales_lbp = sum(
                order.final_total_lbp_rounded
                for order in hour_orders
                if order.status != "pending_payment"
            )
            order_count = len(
                [order for order in hour_orders if order.status != "pending_payment"]
            )

            hourly_data.append(
                {
                    "hour": hour,
                    "hour_range": f"{hour:02d}:00-{(hour+1):02d}:00",
                    "orders_count": order_count,
                    "sales_usd": hour_sales_usd,
                    "sales_lbp": hour_sales_lbp,
                }
            )

        return (
            jsonify(
                {
                    "report_date": target_date.strftime("%Y-%m-%d"),
                    "hourly_breakdown": hourly_data,
                    "daily_totals": {
                        "total_orders": sum(h["orders_count"] for h in hourly_data),
                        "total_sales_usd": sum(h["sales_usd"] for h in hourly_data),
                        "total_sales_lbp": sum(h["sales_lbp"] for h in hourly_data),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Error generating hourly sales report: {e}")
        return jsonify({"message": "Could not generate hourly sales report."}), 500


# Future reports for post-v0.1 could include:
# - Shift reconciliation details
# - COGS and profitability
# - Cost entry summaries
