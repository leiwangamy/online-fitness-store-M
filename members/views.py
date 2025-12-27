from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .models import MemberProfile

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

        if "subscribe_basic" in request.POST:
            membership.start_monthly_membership(level="basic")
            messages.success(request, f"Successfully subscribed to BASIC plan for $39/month!")
            return redirect("members:my_membership")

        if "subscribe_premium" in request.POST:
            membership.start_monthly_membership(level="premium")
            messages.success(request, f"Successfully subscribed to PREMIUM plan for $79/month!")
            return redirect("members:my_membership")

        if "switch_to_basic" in request.POST and membership.is_active_member:
            membership.membership_level = "basic"
            membership.save(update_fields=["membership_level"])
            messages.success(request, "Membership plan switched to BASIC. Your membership will change immediately.")
            return redirect("members:my_membership")

        if "switch_to_premium" in request.POST and membership.is_active_member:
            membership.membership_level = "premium"
            membership.save(update_fields=["membership_level"])
            messages.success(request, "Membership plan switched to PREMIUM. Your membership will change immediately.")
            return redirect("members:my_membership")

    return render(request, "members/my_membership.html", {"profile": membership, "basic_price": 39, "premium_price": 79})
