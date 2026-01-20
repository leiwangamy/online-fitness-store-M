from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from .models import MemberProfile, MembershipPlan

# Import MembershipPlanContent with fallback if model doesn't exist yet
try:
    from core.models import MembershipPlanContent
except ImportError:
    MembershipPlanContent = None

def membership_plans(request):
    """Public view to show membership plans. Allows both logged in and logged out users to view plans."""
    from django.db import OperationalError, ProgrammingError
    from django.contrib import messages
    
    # Handle POST requests (subscription attempts)
    if request.method == "POST":
        if not request.user.is_authenticated:
            # If user tries to subscribe without being logged in, redirect to login
            plan_slug = request.POST.get("plan_slug", "")
            login_url = reverse("account_login")
            next_url = reverse("members:membership_plans")
            if plan_slug:
                next_url = f"{next_url}?plan={plan_slug}"
            return redirect(f"{login_url}?next={next_url}")
        else:
            # User is logged in - handle subscription
            plan_slug = request.POST.get("plan_slug", "")
            if plan_slug:
                # Redirect to my_membership with plan parameter to handle subscription
                return redirect(f"{reverse('members:my_membership')}?plan={plan_slug}")
            else:
                # Redirect to manage subscription page
                return redirect("members:manage_subscription")
    
    # Get content from model (singleton pattern) with fallback
    content = None
    plans = []
    
    try:
        # Get content from model
        try:
            if MembershipPlanContent and hasattr(MembershipPlanContent, 'objects'):
                content = MembershipPlanContent.get_instance()
        except (AttributeError, Exception):
            content = None
        
        # Check if platform membership should be shown
        show_platform = True
        try:
            from core.models import AdminSettings
            admin_settings = AdminSettings.get_instance()
            # Use new field if available, fallback to old field for migration
            show_platform = getattr(admin_settings, 'show_platform_membership', admin_settings.show_membership_functions)
        except Exception:
            pass
        
        # Get active membership plans (admin plans) - only if platform membership is enabled
        admin_plans = []
        if show_platform:
            admin_plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
        
        # Get active seller membership plans (always shown)
        seller_plans = []
        try:
            from sellers.models import SellerMembershipPlan
            seller_plans = SellerMembershipPlan.objects.filter(is_active=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
        except Exception:
            seller_plans = []
        
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - show static content only
        admin_plans = []
        seller_plans = []
        content = None
    except Exception:
        # Any other database error - show static content
        admin_plans = []
        seller_plans = []
        content = None
    
    # Get user's current membership status if logged in
    current_membership = None
    current_plan = None
    is_member = False
    
    if request.user.is_authenticated:
        try:
            current_membership = request.user.membership
            is_member = current_membership.is_active_member
            if is_member and current_membership.membership_level and current_membership.membership_level != "none":
                # Check if it's a platform membership (not seller)
                if not current_membership.membership_level.startswith("seller_"):
                    try:
                        current_plan = MembershipPlan.objects.get(slug=current_membership.membership_level)
                    except MembershipPlan.DoesNotExist:
                        current_plan = None
        except Exception:
            pass
    
    # Show platform membership plans
    return render(request, "members/membership_plans.html", {
        "plans": admin_plans,
        "content": content,
        "current_membership": current_membership,
        "current_plan": current_plan,
        "is_member": is_member,
    })


def seller_membership_plans(request):
    """Public view to show seller membership plans"""
    from django.db import OperationalError, ProgrammingError
    
    # Check if seller membership should be shown
    show_seller = True
    try:
        from core.models import AdminSettings
        admin_settings = AdminSettings.get_instance()
        show_seller = getattr(admin_settings, 'show_seller_membership', True)
    except Exception:
        pass
    
    # If seller membership is disabled, return 404
    if not show_seller:
        from django.http import Http404
        raise Http404("Seller membership is not available.")
    
    # Handle POST requests (subscription attempts)
    if request.method == "POST":
        if not request.user.is_authenticated:
            # If user tries to subscribe without being logged in, redirect to login
            plan_slug = request.POST.get("plan_slug", "")
            login_url = reverse("account_login")
            next_url = reverse("members:seller_membership_plans")
            if plan_slug:
                next_url = f"{next_url}?plan={plan_slug}"
            return redirect(f"{login_url}?next={next_url}")
        else:
            # User is logged in - handle subscription
            plan_slug = request.POST.get("plan_slug", "")
            if plan_slug:
                # Redirect to my_membership with plan parameter to handle subscription
                return redirect(f"{reverse('members:my_membership')}?plan={plan_slug}")
            else:
                # Redirect to manage subscription page
                return redirect("members:manage_subscription")
    
    # Get active seller membership plans
    seller_plans = []
    try:
        from sellers.models import SellerMembershipPlan
        seller_plans = SellerMembershipPlan.objects.filter(is_active=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
    except (OperationalError, ProgrammingError):
        seller_plans = []
    except Exception:
        seller_plans = []
    
    # Get user's current seller membership status if logged in
    current_membership = None
    current_seller_plan = None
    is_member = False
    
    if request.user.is_authenticated:
        try:
            current_membership = request.user.membership
            is_member = current_membership.is_active_member
            if is_member and current_membership.membership_level and current_membership.membership_level != "none":
                # Check if it's a seller membership
                if current_membership.membership_level.startswith("seller_"):
                    try:
                        from sellers.models import SellerMembershipPlan
                        # Parse the full slug: seller_{seller_id}_{slug}
                        parts = current_membership.membership_level.split('_', 2)
                        if len(parts) == 3:
                            seller_id = parts[1]
                            slug = parts[2]
                            current_seller_plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
                    except Exception:
                        current_seller_plan = None
        except Exception:
            pass
    
    # Show seller membership plans
    return render(request, "members/seller_membership_plans.html", {
        "seller_plans": seller_plans,
        "current_membership": current_membership,
        "current_seller_plan": current_seller_plan,
        "is_member": is_member,
    })

@login_required
def my_membership(request):
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if "resume_membership" in request.POST and membership.is_active_member:
            membership.auto_renew = True
            if membership.membership_expires:
                membership.next_billing_date = (membership.membership_expires + timedelta(days=1)).date()
            membership.save()
            messages.success(request, "Auto-renewal has been resumed. Your membership will be billed automatically.")
            return redirect("members:my_membership")

        if "cancel_membership" in request.POST and membership.is_active_member:
            membership.auto_renew = False
            membership.next_billing_date = None
            membership.save()
            messages.info(request, "Auto-renewal has been cancelled. Your membership stays active until the period ends.")
            return redirect("members:my_membership")

        # Handle dynamic plan subscriptions
        if "subscribe_plan" in request.POST:
            plan_slug = request.POST.get("plan_slug")
            plan_type = request.POST.get("plan_type", "admin")
            
            try:
                if plan_type == "seller":
                    # Seller membership plan - plan_slug is the full slug (seller_X_slug)
                    from sellers.models import SellerMembershipPlan
                    # Parse the full slug: seller_{seller_id}_{slug}
                    parts = plan_slug.split('_', 2)  # Split into max 3 parts
                    if len(parts) == 3 and parts[0] == 'seller':
                        seller_id = parts[1]
                        slug = parts[2]
                        plan = get_object_or_404(SellerMembershipPlan, seller_id=seller_id, slug=slug, is_active=True)
                        # Use full slug for seller plans
                        membership.start_monthly_membership(level=plan.get_full_slug())
                        price_text = plan.price_display
                        messages.success(request, f"Successfully subscribed to {plan.name} plan from {plan.seller.display_name or plan.seller.user.username} ({price_text})!")
                    else:
                        messages.error(request, "Invalid seller plan.")
                else:
                    # Admin membership plan
                    plan = get_object_or_404(MembershipPlan, slug=plan_slug, is_active=True)
                    membership.start_monthly_membership(level=plan.slug)
                    price_text = plan.price_display
                    messages.success(request, f"Successfully subscribed to {plan.name} plan ({price_text})!")
            except Exception as e:
                messages.error(request, "Error subscribing to plan. Please try again.")
            return redirect("members:my_membership")

    # Get active membership plans (admin and seller)
    admin_plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
    seller_plans = []
    try:
        from sellers.models import SellerMembershipPlan
        seller_plans = SellerMembershipPlan.objects.filter(is_active=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
    except Exception:
        seller_plans = []
    
    # Get current plan info
    current_plan = None
    current_seller_plan = None
    if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
        if membership.membership_level.startswith("seller_"):
            try:
                from sellers.models import SellerMembershipPlan
                parts = membership.membership_level.split('_')
                if len(parts) >= 3:
                    seller_id = parts[1]
                    slug = '_'.join(parts[2:])
                    current_seller_plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
            except Exception:
                current_seller_plan = None
        else:
            try:
                current_plan = MembershipPlan.objects.get(slug=membership.membership_level)
            except MembershipPlan.DoesNotExist:
                current_plan = None
    
    return render(request, "members/my_membership.html", {
        "profile": membership,
        "admin_plans": admin_plans,
        "seller_plans": seller_plans,
        "current_plan": current_plan,
        "current_seller_plan": current_seller_plan,
    })

@login_required
def my_subscriptions(request):
    """My Subscriptions page - shows all memberships (platform and seller) in a unified view"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get platform membership info
    platform_membership = None
    if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
        if not membership.membership_level.startswith("seller_"):
            try:
                current_plan = MembershipPlan.objects.get(slug=membership.membership_level)
                platform_membership = {
                    'plan': current_plan,
                    'status': 'Active' if membership.is_active_member else 'Inactive',
                    'next_billing': membership.next_billing_date,
                    'auto_renew': membership.auto_renew,
                    'expires': membership.membership_expires,
                }
            except MembershipPlan.DoesNotExist:
                pass
    
    # Get seller membership info
    seller_membership = None
    if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
        if membership.membership_level.startswith("seller_"):
            try:
                from sellers.models import SellerMembershipPlan
                # Parse the full slug: seller_{seller_id}_{slug}
                parts = membership.membership_level.split('_', 2)
                if len(parts) == 3:
                    seller_id = parts[1]
                    slug = parts[2]
                    current_seller_plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
                    seller_membership = {
                        'plan': current_seller_plan,
                        'seller': current_seller_plan.seller,
                        'status': 'Active' if membership.is_active_member else 'Inactive',
                        'next_billing': membership.next_billing_date,
                        'auto_renew': membership.auto_renew,
                        'expires': membership.membership_expires,
                    }
            except Exception:
                pass
    
    return render(request, "members/my_subscriptions.html", {
        "platform_membership": platform_membership,
        "seller_membership": seller_membership,
        "membership": membership,
    })


@login_required
def manage_subscription(request):
    """Manage subscription page - shows current subscription, plan change, and actions"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Handle plan update
        if "update_plan" in request.POST:
            plan_slug = request.POST.get("plan_slug")
            if plan_slug and membership.is_active_member:
                try:
                    plan = get_object_or_404(MembershipPlan, slug=plan_slug, is_active=True)
                    membership.membership_level = plan.slug
                    membership.save(update_fields=["membership_level"])
                    messages.success(request, f"Plan updated to {plan.name}. Your membership will change immediately.")
                except Exception as e:
                    messages.error(request, "Error updating plan. Please try again.")
            return redirect("members:manage_subscription")

        # Handle cancel subscription
        if "cancel_membership" in request.POST and membership.is_active_member:
            membership.auto_renew = False
            membership.next_billing_date = None
            membership.save()
            messages.info(request, "Auto-renewal has been cancelled. Your membership stays active until the period ends.")
            return redirect("members:manage_subscription")

        # Handle resume subscription
        if "resume_membership" in request.POST and membership.is_active_member:
            membership.auto_renew = True
            if membership.membership_expires:
                membership.next_billing_date = (membership.membership_expires + timedelta(days=1)).date()
            membership.save()
            messages.success(request, "Auto-renewal has been resumed. Your membership will be billed automatically.")
            return redirect("members:manage_subscription")

    # Get current plan (could be admin or seller plan)
    current_plan = None
    current_seller_plan = None
    if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
        # Check if it's a seller plan (starts with "seller_")
        if membership.membership_level.startswith("seller_"):
            try:
                from sellers.models import SellerMembershipPlan
                # Extract seller_id and slug from membership_level
                parts = membership.membership_level.split('_')
                if len(parts) >= 3:
                    seller_id = parts[1]
                    slug = '_'.join(parts[2:])
                    current_seller_plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
            except Exception:
                current_seller_plan = None
        else:
            try:
                current_plan = MembershipPlan.objects.get(slug=membership.membership_level)
            except MembershipPlan.DoesNotExist:
                current_plan = None

    # Get all active plans for dropdown
    admin_plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
    seller_plans = []
    try:
        from sellers.models import SellerMembershipPlan
        seller_plans = SellerMembershipPlan.objects.filter(is_active=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
    except Exception:
        seller_plans = []

    return render(request, "members/manage_subscription.html", {
        "profile": membership,
        "current_plan": current_plan,
        "current_seller_plan": current_seller_plan,
        "admin_plans": admin_plans,
        "seller_plans": seller_plans
    })
