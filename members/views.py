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
    """Public view to show membership plans. Redirects to login when Subscribe is clicked."""
    from django.db import OperationalError, ProgrammingError
    
    # If user is authenticated, redirect to the full membership page
    if request.user.is_authenticated:
        return redirect("members:my_membership")
    
    if request.method == "POST":
        # If user tries to subscribe without being logged in, redirect to login
        # Pass the plan_slug as a parameter so we can redirect to the correct subscription
        plan_slug = request.POST.get("plan_slug", "")
        login_url = reverse("account_login")
        next_url = reverse("members:my_membership")
        if plan_slug:
            next_url = f"{next_url}?plan={plan_slug}"
        return redirect(f"{login_url}?next={next_url}")
    
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
        
        # Get active membership plans
        plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
        
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - show static content only
        plans = []
        content = None
    except Exception:
        # Any other database error - show static content
        plans = []
        content = None
    
    # Show public membership plans
    return render(request, "members/membership_plans.html", {
        "plans": plans,
        "content": content
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
            try:
                plan = get_object_or_404(MembershipPlan, slug=plan_slug, is_active=True)
                membership.start_monthly_membership(level=plan.slug)
                price_text = plan.price_display
                messages.success(request, f"Successfully subscribed to {plan.name} plan ({price_text})!")
            except Exception as e:
                messages.error(request, "Error subscribing to plan. Please try again.")
            return redirect("members:my_membership")

    # Get active membership plans
    plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')
    
    return render(request, "members/my_membership.html", {
        "profile": membership,
        "plans": plans
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

    # Get current plan
    current_plan = None
    if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
        try:
            current_plan = MembershipPlan.objects.get(slug=membership.membership_level)
        except MembershipPlan.DoesNotExist:
            current_plan = None

    # Get all active plans for dropdown
    plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'name')

    return render(request, "members/manage_subscription.html", {
        "profile": membership,
        "current_plan": current_plan,
        "plans": plans
    })
