from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from .models import MemberProfile, MembershipPlan, UserMembership

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
            seller_plans = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
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
    
    # Get user's subscribed plans if logged in
    subscribed_plan_identifiers = set()
    if request.user.is_authenticated:
        try:
            membership, _ = MemberProfile.objects.get_or_create(user=request.user)
            active_memberships = membership.get_active_memberships()
            subscribed_plan_identifiers = {m.plan_identifier for m in active_memberships}
        except Exception:
            pass
    
    # Show platform membership plans
    return render(request, "members/membership_plans.html", {
        "plans": admin_plans,
        "content": content,
        "subscribed_plan_identifiers": subscribed_plan_identifiers,
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
    
    # Get active seller membership plans, grouped by seller
    seller_plans = []
    seller_intros = {}  # Dictionary to store intro text per seller
    try:
        from sellers.models import SellerMembershipPlan
        seller_plans = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
        # Get unique sellers and their intro texts
        for plan in seller_plans:
            seller_id = plan.seller.id
            if seller_id not in seller_intros:
                seller_intros[seller_id] = plan.seller.membership_intro_text or "Choose a seller membership plan that fits your needs."
    except (OperationalError, ProgrammingError):
        seller_plans = []
        seller_intros = {}
    except Exception:
        seller_plans = []
        seller_intros = {}
    
    # Get user's subscribed plans if logged in
    subscribed_plan_identifiers = set()
    if request.user.is_authenticated:
        try:
            membership, _ = MemberProfile.objects.get_or_create(user=request.user)
            active_memberships = membership.get_active_memberships()
            subscribed_plan_identifiers = {m.plan_identifier for m in active_memberships}
        except Exception:
            pass
    
    # Show seller membership plans
    return render(request, "members/seller_membership_plans.html", {
        "seller_plans": seller_plans,
        "seller_intros": seller_intros,
        "subscribed_plan_identifiers": subscribed_plan_identifiers,
    })

@login_required
def my_membership(request):
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)

    # Handle plan subscription from GET parameter (redirected from membership plans page)
    if request.method == "GET" and "plan" in request.GET:
        plan_slug = request.GET.get("plan", "")
        if plan_slug:
            try:
                # Check if it's a seller plan (starts with "seller_")
                if plan_slug.startswith("seller_"):
                    from sellers.models import SellerMembershipPlan
                    # Parse the full slug: seller_{seller_id}_{slug}
                    parts = plan_slug.split('_', 2)
                    if len(parts) == 3 and parts[0] == 'seller':
                        seller_id = parts[1]
                        slug = parts[2]
                        plan = get_object_or_404(SellerMembershipPlan, seller_id=seller_id, slug=slug, is_active=True, is_approved=True)
                        plan_identifier = plan.get_full_slug()
                        
                        # Check if already subscribed
                        if membership.has_membership(plan_identifier):
                            messages.info(request, f"You are already subscribed to {plan.name} plan from {plan.seller.display_name or plan.seller.user.username}.")
                        else:
                            # Subscribe to the plan
                            membership.subscribe_to_plan(plan_identifier, "seller")
                            price_text = plan.price_display
                            messages.success(request, f"Successfully subscribed to {plan.name} plan from {plan.seller.display_name or plan.seller.user.username} ({price_text})!")
                    else:
                        messages.error(request, f"Invalid seller plan format: {plan_slug}")
                else:
                    # Admin/platform membership plan
                    plan = get_object_or_404(MembershipPlan, slug=plan_slug, is_active=True)
                    
                    # Check if already subscribed
                    if membership.has_membership(plan.slug):
                        messages.info(request, f"You are already subscribed to {plan.name} plan.")
                    else:
                        # Subscribe to the plan
                        membership.subscribe_to_plan(plan.slug, "platform")
                        price_text = plan.price_display
                        messages.success(request, f"Successfully subscribed to {plan.name} plan ({price_text})!")
                # Redirect to remove the plan parameter from URL
                return redirect("members:my_membership")
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                messages.error(request, f"Error subscribing to plan: {str(e)}")
                # Log the error for debugging
                print(f"Subscription error: {error_details}")
                return redirect("members:my_membership")

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
                        plan = get_object_or_404(SellerMembershipPlan, seller_id=seller_id, slug=slug, is_active=True, is_approved=True)
                        plan_identifier = plan.get_full_slug()
                        
                        # Check if already subscribed
                        if membership.has_membership(plan_identifier):
                            messages.info(request, f"You are already subscribed to {plan.name} plan from {plan.seller.display_name or plan.seller.user.username}.")
                        else:
                            # Subscribe to the plan
                            membership.subscribe_to_plan(plan_identifier, "seller")
                            price_text = plan.price_display
                            messages.success(request, f"Successfully subscribed to {plan.name} plan from {plan.seller.display_name or plan.seller.user.username} ({price_text})!")
                    else:
                        messages.error(request, "Invalid seller plan.")
                else:
                    # Admin/platform membership plan
                    plan = get_object_or_404(MembershipPlan, slug=plan_slug, is_active=True)
                    
                    # Check if already subscribed
                    if membership.has_membership(plan.slug):
                        messages.info(request, f"You are already subscribed to {plan.name} plan.")
                    else:
                        # Subscribe to the plan
                        membership.subscribe_to_plan(plan.slug, "platform")
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
        seller_plans = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
    except Exception:
        seller_plans = []
    
    # Combine all plans for template (platform plans first, then seller plans)
    all_plans = list(admin_plans) + list(seller_plans)
    
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
        "plans": all_plans,  # Combined list for template
        "admin_plans": admin_plans,
        "seller_plans": seller_plans,
        "current_plan": current_plan,
        "current_seller_plan": current_seller_plan,
    })

@login_required
def my_subscriptions(request):
    """My Subscriptions page - shows all subscriptions in a list format"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get all active memberships
    all_user_memberships = UserMembership.objects.filter(user=request.user).order_by('-started_at')
    
    platform_memberships = []
    seller_memberships = []

    for user_membership in all_user_memberships:
        plan_obj = user_membership.get_plan_object()
        if not plan_obj:
            continue
        
        membership_data = {
            'user_membership': user_membership,
            'plan': plan_obj,
            'status': 'Active' if user_membership.is_currently_active else 'Expired',
            'next_billing': user_membership.next_billing_date,
            'auto_renew': user_membership.auto_renew,
            'expires': user_membership.expires_at,
            'started': user_membership.started_at,
        }
        
        if user_membership.plan_type == 'platform':
            platform_memberships.append(membership_data)
        else: # seller
            if hasattr(plan_obj, 'seller'):
                membership_data['seller'] = plan_obj.seller
            seller_memberships.append(membership_data)
    
    return render(request, "members/my_subscriptions.html", {
        "platform_memberships": platform_memberships,
        "seller_memberships": seller_memberships,
        "membership": membership,
        "has_memberships": len(platform_memberships) > 0 or len(seller_memberships) > 0,
    })


@login_required
def my_platform_subscriptions(request):
    """Platform Subscriptions page - shows only platform memberships"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get all active platform memberships
    active_memberships = membership.get_active_memberships().filter(plan_type='platform')
    
    platform_memberships = []
    for user_membership in active_memberships:
        plan_obj = user_membership.get_plan_object()
        if not plan_obj:
            continue
        
        platform_memberships.append({
            'user_membership': user_membership,
            'plan': plan_obj,
            'status': 'Active' if user_membership.is_currently_active else 'Expired',
            'next_billing': user_membership.next_billing_date,
            'auto_renew': user_membership.auto_renew,
            'expires': user_membership.expires_at,
            'started': user_membership.started_at,
        })
    
    return render(request, "members/my_platform_subscriptions.html", {
        "platform_memberships": platform_memberships,
        "membership": membership,
        "has_memberships": len(platform_memberships) > 0,
    })


@login_required
def my_seller_subscriptions(request):
    """Seller Subscriptions page - shows only seller memberships"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get all active seller memberships
    active_memberships = membership.get_active_memberships().filter(plan_type='seller')
    
    seller_memberships = []
    for user_membership in active_memberships:
        plan_obj = user_membership.get_plan_object()
        if not plan_obj:
            continue
        
        membership_data = {
            'user_membership': user_membership,
            'plan': plan_obj,
            'status': 'Active' if user_membership.is_currently_active else 'Expired',
            'next_billing': user_membership.next_billing_date,
            'auto_renew': user_membership.auto_renew,
            'expires': user_membership.expires_at,
            'started': user_membership.started_at,
        }
        
        if hasattr(plan_obj, 'seller'):
            membership_data['seller'] = plan_obj.seller
        seller_memberships.append(membership_data)
    
    return render(request, "members/my_seller_subscriptions.html", {
        "seller_memberships": seller_memberships,
        "membership": membership,
        "has_memberships": len(seller_memberships) > 0,
    })


@login_required
def manage_subscription(request):
    """Manage subscription page - shows all memberships (platform and seller) and allows managing them"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get specific membership to manage from query parameter
    membership_id = request.GET.get('membership_id') or request.POST.get('membership_id')
    selected_membership = None
    if membership_id:
        try:
            selected_membership = UserMembership.objects.get(id=membership_id, user=request.user)
        except UserMembership.DoesNotExist:
            messages.error(request, "Membership not found.")
            return redirect("members:my_subscriptions")

    if request.method == "POST":
        # Handle cancel subscription for specific membership
        if "cancel_membership" in request.POST:
            membership_id = request.POST.get("membership_id")
            try:
                user_membership = UserMembership.objects.get(id=membership_id, user=request.user)
                user_membership.cancel()
                plan_obj = user_membership.get_plan_object()
                plan_name = plan_obj.name if plan_obj else "membership"
                messages.info(request, f"Auto-renewal has been cancelled for {plan_name}. Your membership stays active until {user_membership.expires_at.date()}.")
            except UserMembership.DoesNotExist:
                messages.error(request, "Membership not found.")
            return redirect(f"{reverse('members:manage_subscription')}?membership_id={membership_id}")

        # Handle resume subscription for specific membership
        if "resume_membership" in request.POST:
            membership_id = request.POST.get("membership_id")
            try:
                user_membership = UserMembership.objects.get(id=membership_id, user=request.user)
                user_membership.resume()
                plan_obj = user_membership.get_plan_object()
                plan_name = plan_obj.name if plan_obj else "membership"
                messages.success(request, f"Auto-renewal has been resumed for {plan_name}. Your membership will be billed automatically.")
            except UserMembership.DoesNotExist:
                messages.error(request, "Membership not found.")
            return redirect(f"{reverse('members:manage_subscription')}?membership_id={membership_id}")
        
        # Handle plan change/update
        if "update_plan" in request.POST:
            membership_id = request.POST.get("membership_id")
            new_plan_slug = request.POST.get("plan_slug")
            plan_type = request.POST.get("plan_type")
            
            if membership_id and new_plan_slug:
                try:
                    user_membership = UserMembership.objects.get(id=membership_id, user=request.user)
                    # Check if already subscribed to the new plan
                    if membership.has_membership(new_plan_slug):
                        messages.info(request, "You are already subscribed to this plan.")
                    else:
                        # Cancel old membership and subscribe to new plan
                        user_membership.cancel()
                        membership.subscribe_to_plan(new_plan_slug, plan_type)
                        plan_obj = membership.get_active_memberships().filter(plan_identifier=new_plan_slug).first().get_plan_object()
                        plan_name = plan_obj.name if plan_obj else "new plan"
                        messages.success(request, f"Plan updated to {plan_name}. Your membership will change immediately.")
                        # Redirect to the new membership's manage page
                        new_membership = membership.get_active_memberships().filter(plan_identifier=new_plan_slug).first()
                        if new_membership:
                            return redirect(f"{reverse('members:manage_subscription')}?membership_id={new_membership.id}")
                except UserMembership.DoesNotExist:
                    messages.error(request, "Membership not found.")
            return redirect(f"{reverse('members:manage_subscription')}?membership_id={membership_id}")

    # If a specific membership_id is provided, show only that membership
    # Otherwise, redirect to my_subscriptions to select one
    if membership_id and selected_membership:
        active_memberships = [selected_membership]
    else:
        # If no membership_id provided, redirect to my_subscriptions
        return redirect("members:my_subscriptions")
    
    # Get all available plans (excluding already subscribed ones)
    subscribed_identifiers = {m.plan_identifier for m in active_memberships}
    admin_plans = MembershipPlan.objects.filter(is_active=True).exclude(slug__in=subscribed_identifiers).order_by('display_order', 'name')
    seller_plans = []
    try:
        from sellers.models import SellerMembershipPlan
        all_seller_plans = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
        seller_plans = [p for p in all_seller_plans if p.get_full_slug() not in subscribed_identifiers]
    except Exception:
        seller_plans = []
    
    # Also get all plans (including subscribed ones) for the change plan dropdown
    all_admin_plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
    all_seller_plans_list = []
    try:
        from sellers.models import SellerMembershipPlan
        all_seller_plans_list = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
    except Exception:
        pass

    return render(request, "members/manage_subscription.html", {
        "profile": membership,
        "active_memberships": active_memberships,
        "selected_membership": selected_membership,
        "admin_plans": admin_plans,
        "seller_plans": seller_plans,
        "all_admin_plans": all_admin_plans,
        "all_seller_plans": all_seller_plans_list,
        "has_memberships": len(active_memberships) > 0,
    })


@login_required
def manage_seller_subscription(request):
    """Manage seller subscription page - shows seller memberships and allows managing them"""
    membership, _ = MemberProfile.objects.get_or_create(user=request.user)
    
    # Get specific membership to manage from query parameter
    membership_id = request.GET.get('membership_id')
    selected_membership = None
    if membership_id:
        try:
            selected_membership = UserMembership.objects.get(id=membership_id, user=request.user, plan_type='seller')
        except UserMembership.DoesNotExist:
            messages.error(request, "Membership not found.")
            return redirect("members:manage_seller_subscription")

    if request.method == "POST":
        # Handle cancel subscription for specific membership
        if "cancel_membership" in request.POST:
            membership_id = request.POST.get("membership_id")
            try:
                user_membership = UserMembership.objects.get(id=membership_id, user=request.user, plan_type='seller')
                user_membership.cancel()
                plan_obj = user_membership.get_plan_object()
                plan_name = plan_obj.name if plan_obj else "membership"
                messages.info(request, f"Auto-renewal has been cancelled for {plan_name}. Your membership stays active until {user_membership.expires_at.date()}.")
            except UserMembership.DoesNotExist:
                messages.error(request, "Membership not found.")
            return redirect("members:manage_seller_subscription")

        # Handle resume subscription for specific membership
        if "resume_membership" in request.POST:
            membership_id = request.POST.get("membership_id")
            try:
                user_membership = UserMembership.objects.get(id=membership_id, user=request.user, plan_type='seller')
                user_membership.resume()
                plan_obj = user_membership.get_plan_object()
                plan_name = plan_obj.name if plan_obj else "membership"
                messages.success(request, f"Auto-renewal has been resumed for {plan_name}. Your membership will be billed automatically.")
            except UserMembership.DoesNotExist:
                messages.error(request, "Membership not found.")
            return redirect("members:manage_seller_subscription")

    # Get all active seller memberships
    active_memberships = membership.get_active_memberships().filter(plan_type='seller')
    
    # Get all available seller plans (excluding already subscribed ones)
    subscribed_identifiers = {m.plan_identifier for m in active_memberships}
    seller_plans = []
    try:
        from sellers.models import SellerMembershipPlan
        all_seller_plans = SellerMembershipPlan.objects.filter(is_active=True, is_approved=True).select_related('seller').order_by('seller__display_name', 'display_order', 'name')
        seller_plans = [p for p in all_seller_plans if p.get_full_slug() not in subscribed_identifiers]
    except Exception:
        seller_plans = []

    return render(request, "members/manage_seller_subscription.html", {
        "profile": membership,
        "active_memberships": active_memberships,
        "selected_membership": selected_membership,
        "seller_plans": seller_plans,
        "has_memberships": active_memberships.exists(),
    })
