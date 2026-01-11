from .models import MemberProfile, MembershipPlan


def membership_context(request):
    """Add user's membership information to template context"""
    context = {}
    if request.user.is_authenticated:
        try:
            membership = request.user.membership
            context['user_membership'] = membership
            # Get the current plan object if user has an active membership
            if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
                try:
                    context['user_current_plan'] = MembershipPlan.objects.get(slug=membership.membership_level)
                except MembershipPlan.DoesNotExist:
                    context['user_current_plan'] = None
            else:
                context['user_current_plan'] = None
            # Get membership status display name
            if context['user_current_plan']:
                context['user_membership_status'] = context['user_current_plan'].name
            elif membership.membership_level and membership.membership_level != "none":
                # Try to get the plan name even if not active
                try:
                    plan = MembershipPlan.objects.get(slug=membership.membership_level)
                    context['user_membership_status'] = plan.name
                except MembershipPlan.DoesNotExist:
                    context['user_membership_status'] = "None"
            else:
                context['user_membership_status'] = "None"
        except MemberProfile.DoesNotExist:
            context['user_membership'] = None
            context['user_current_plan'] = None
            context['user_membership_status'] = "None"
    else:
        context['user_membership'] = None
        context['user_current_plan'] = None
        context['user_membership_status'] = "None"
    return context
