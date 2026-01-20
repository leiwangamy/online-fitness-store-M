from django.db import OperationalError, ProgrammingError


def membership_context(request):
    """Add user's membership information to template context"""
    context = {
        'user_membership': None,
        'user_current_plan': None,
        'user_current_seller_plan': None,
        'user_membership_status': "None",
        'user_seller_membership_status': "None",
        'has_platform_membership': False,
        'has_seller_membership': False,
    }
    
    try:
        from .models import MemberProfile, MembershipPlan
        
        if request.user.is_authenticated:
            try:
                membership = request.user.membership
                context['user_membership'] = membership
                # Get the current plan object if user has an active membership
                if membership.is_active_member and membership.membership_level and membership.membership_level != "none":
                    # Check if it's a seller plan (starts with "seller_")
                    if membership.membership_level.startswith("seller_"):
                        try:
                            from sellers.models import SellerMembershipPlan
                            # Parse the full slug: seller_{seller_id}_{slug}
                            parts = membership.membership_level.split('_', 2)
                            if len(parts) == 3:
                                seller_id = parts[1]
                                slug = parts[2]
                                seller_plan = SellerMembershipPlan.objects.get(seller_id=seller_id, slug=slug)
                                context['user_current_seller_plan'] = seller_plan
                                seller_name = seller_plan.seller.display_name or seller_plan.seller.user.username
                                context['user_seller_membership_status'] = f"{seller_name} Membership"
                                context['has_seller_membership'] = True
                        except Exception:
                            context['user_current_seller_plan'] = None
                    else:
                        # Platform/admin membership plan
                        try:
                            context['user_current_plan'] = MembershipPlan.objects.get(slug=membership.membership_level)
                            context['user_membership_status'] = context['user_current_plan'].name
                            context['has_platform_membership'] = True
                        except MembershipPlan.DoesNotExist:
                            context['user_current_plan'] = None
                else:
                    context['user_current_plan'] = None
                    context['user_current_seller_plan'] = None
            except MemberProfile.DoesNotExist:
                context['user_membership'] = None
                context['user_current_plan'] = None
                context['user_membership_status'] = "None"
    except (OperationalError, ProgrammingError):
        # Database tables don't exist - return default values
        pass
    except Exception:
        # Any other error - return default values
        pass
    
    return context
