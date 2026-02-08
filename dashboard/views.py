"""
Dashboard Views Module

This module provides read-only analytics dashboard views.
Displays aggregated business metrics and visualizations for portfolio purposes.
"""

from django.shortcuts import render
from django.db.models import Sum, Count, Q, DecimalField, F
from django.db.models.functions import TruncMonth, TruncDate
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from orders.models import Order, OrderItem
from members.models import MemberProfile
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()


def analytics_dashboard(request):
    """
    Main analytics dashboard view.
    Displays key business metrics and charts.
    Publicly accessible for portfolio purposes.
    """
    now = timezone.now()
    today = now.date()
    this_month_start = today.replace(day=1)
    this_year_start = today.replace(month=1, day=1)
    
    # ============================================
    # REVENUE METRICS
    # ============================================
    # Total revenue (all time)
    total_revenue = Order.objects.filter(
        status__in=['paid', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total', output_field=DecimalField()))['total'] or Decimal('0.00')
    
    # Today's revenue
    today_revenue = Order.objects.filter(
        created_at__date=today,
        status__in=['paid', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total', output_field=DecimalField()))['total'] or Decimal('0.00')
    
    # This month's revenue
    monthly_revenue = Order.objects.filter(
        created_at__gte=this_month_start,
        status__in=['paid', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total', output_field=DecimalField()))['total'] or Decimal('0.00')
    
    # This year's revenue
    yearly_revenue = Order.objects.filter(
        created_at__gte=this_year_start,
        status__in=['paid', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total', output_field=DecimalField()))['total'] or Decimal('0.00')
    
    # ============================================
    # MONTHLY REVENUE TREND (Last 3 months)
    # ============================================
    # Get last 3 months including current month
    three_months_ago = (now - timedelta(days=90)).replace(day=1)
    
    # Fetch actual revenue data for months that have orders
    monthly_revenue_data = (
        Order.objects
        .filter(
            created_at__gte=three_months_ago,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        )
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(revenue=Sum('total', output_field=DecimalField()))
        .order_by('month')
    )
    
    # Create a dictionary of actual revenue by month
    revenue_by_month = {}
    for item in monthly_revenue_data:
        month_key = item['month'].strftime('%Y-%m')
        revenue_by_month[month_key] = float(item['revenue'] or 0)
    
    # Generate labels and values for last 3 months (always show 3 months)
    monthly_labels = []
    monthly_revenue_values = []
    
    for i in range(3):
        # Calculate the month (i=0 is 2 months ago, i=1 is 1 month ago, i=2 is current month)
        month_date = (now.replace(day=1) - timedelta(days=30 * (2 - i)))
        month_key = month_date.strftime('%Y-%m')
        month_str = month_date.strftime('%b %Y')
        
        monthly_labels.append(month_str)
        # Use actual revenue if available, otherwise 0
        monthly_revenue_values.append(revenue_by_month.get(month_key, 0.0))
    
    # ============================================
    # MEMBERSHIP METRICS
    # ============================================
    # Total active members
    active_members = MemberProfile.objects.filter(
        is_member=True,
        membership_expires__gte=now
    ).count()
    
    # New signups this month
    new_members_this_month = MemberProfile.objects.filter(
        membership_started__gte=this_month_start,
        is_member=True
    ).count()
    
    # Membership type breakdown
    membership_breakdown = (
        MemberProfile.objects
        .filter(is_member=True, membership_expires__gte=now)
        .values('membership_level')
        .annotate(count=Count('id'))
        .order_by('membership_level')
    )
    
    # Format for pie chart
    membership_labels = []
    membership_counts = []
    membership_colors = {
        'none': '#95a5a6',
        'basic': '#3498db',
        'premium': '#9b59b6',
    }
    membership_chart_colors = []
    
    for item in membership_breakdown:
        level = item['membership_level']
        display_name = dict(MemberProfile.MEMBERSHIP_LEVEL_CHOICES).get(level, level.title())
        membership_labels.append(display_name)
        membership_counts.append(item['count'])
        membership_chart_colors.append(membership_colors.get(level, '#95a5a6'))
    
    # Total users
    total_users = User.objects.count()
    
    # ============================================
    # PRODUCT METRICS
    # ============================================
    # Top 5 products by revenue
    top_products = (
        OrderItem.objects
        .filter(
            order__status__in=['paid', 'processing', 'shipped', 'delivered']
        )
        .values('product__name')
        .annotate(
            revenue=Sum(
                F('price') * F('quantity'),
                output_field=DecimalField()
            ),
            total_sold=Sum('quantity')
        )
        .order_by('-revenue')[:5]
    )
    
    top_product_names = [item['product__name'] for item in top_products]
    top_product_revenue = [float(item['revenue'] or 0) for item in top_products]
    
    # Low stock items (less than 10)
    low_stock_products = Product.objects.filter(
        quantity_in_stock__lt=10,
        quantity_in_stock__gt=0,
        is_active=True
    ).count()
    
    # Out of stock items
    out_of_stock_products = Product.objects.filter(
        quantity_in_stock=0,
        is_active=True
    ).count()
    
    # Total products
    total_products = Product.objects.filter(is_active=True).count()
    
    # ============================================
    # ORDER METRICS
    # ============================================
    # Total orders
    total_orders = Order.objects.count()
    
    # Orders today
    orders_today = Order.objects.filter(created_at__date=today).count()
    
    # Orders this month
    orders_this_month = Order.objects.filter(created_at__gte=this_month_start).count()
    
    # Order status breakdown
    order_status_breakdown = (
        Order.objects
        .values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )
    
    context = {
        # Revenue metrics
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        
        # Monthly revenue chart data
        'monthly_labels': monthly_labels,
        'monthly_revenue_values': monthly_revenue_values,
        
        # Membership metrics
        'active_members': active_members,
        'new_members_this_month': new_members_this_month,
        'total_users': total_users,
        'membership_labels': membership_labels,
        'membership_counts': membership_counts,
        'membership_chart_colors': membership_chart_colors,
        
        # Product metrics
        'top_product_names': top_product_names,
        'top_product_revenue': top_product_revenue,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'total_products': total_products,
        
        # Order metrics
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_this_month': orders_this_month,
        'order_status_breakdown': order_status_breakdown,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

