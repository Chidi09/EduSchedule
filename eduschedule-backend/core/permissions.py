import logging
from fastapi import HTTPException, Depends
from core.dependencies import get_current_user, supabase

logger = logging.getLogger(__name__)

# Define plan limits for each resource
PLAN_LIMITS = {
    "free": {
        "teachers": 5,
        "rooms": 3,
        "subjects": 5,
        "classes": 3,
        "timetables_per_month": 2
    },
    "pro": {
        "teachers": 50,
        "rooms": 20,
        "subjects": 30,
        "classes": 20,
        "timetables_per_month": 20
    },
    "enterprise": {
        "teachers": 9999,
        "rooms": 9999,
        "subjects": 9999,
        "classes": 9999,
        "timetables_per_month": 9999
    }
}


def check_plan_limits(resource: str):
    """
    Dependency factory to check if user has reached their plan limits.

    Args:
        resource: The resource type to check ('teachers', 'rooms', 'subjects', 'classes', 'timetables_per_month')

    Returns:
        A dependency function that returns the current user if within limits, otherwise raises HTTPException
    """
    async def _check_limits(user=Depends(get_current_user)):
        try:
            # 1. Get User Profile and Plan
            profile_response = supabase.table('profiles').select('plan').eq('id', user.id).single().execute()

            if not profile_response.data:
                logger.warning(f"Profile not found for user {user.id}")
                raise HTTPException(
                    status_code=500,
                    detail="User profile not found"
                )

            plan = profile_response.data.get('plan', 'free')

            # Validate plan
            if plan not in PLAN_LIMITS:
                logger.warning(f"Invalid plan '{plan}' for user {user.id}")
                plan = 'free'

            limit = PLAN_LIMITS[plan].get(resource, 0)

            # 2. Count Current Usage
            table_name = resource if resource != 'timetables_per_month' else 'timetables'

            count_response = supabase.table(table_name).select('*', count='exact').eq('user_id', user.id).execute()
            current_count = count_response.count or 0

            # 3. Check if at limit
            if current_count >= limit:
                resource_display = resource.replace('_', ' ').title()
                logger.info(f"User {user.id} ({plan} plan) reached limit for {resource}: {current_count}/{limit}")

                raise HTTPException(
                    status_code=403,
                    detail=f"Plan limit reached for {resource_display.lower()}. You have {current_count}/{limit}. "
                           f"Upgrade to Pro to add more {resource.lower()}."
                )

            logger.debug(f"User {user.id} ({plan} plan) using {current_count}/{limit} {resource}")
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking plan limits for user {user.id}: {str(e)}")
            # Fail open - allow the request if we can't check limits
            # In production, you might want to fail closed instead
            return user

    return _check_limits


async def get_user_plan(user=Depends(get_current_user)) -> str:
    """Get the current user's plan."""
    try:
        profile_response = supabase.table('profiles').select('plan').eq('id', user.id).single().execute()
        if profile_response.data:
            return profile_response.data.get('plan', 'free')
        return 'free'
    except Exception as e:
        logger.error(f"Error fetching user plan: {str(e)}")
        return 'free'


def get_plan_limits(plan: str) -> dict:
    """Get limits for a specific plan."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])


def get_user_usage(user_id: str) -> dict:
    """Get the current user's resource usage across all limits."""
    try:
        usage = {}
        for resource in ['teachers', 'rooms', 'subjects', 'classes']:
            table_name = resource
            response = supabase.table(table_name).select('*', count='exact').eq('user_id', user_id).execute()
            usage[resource] = response.count or 0
        return usage
    except Exception as e:
        logger.error(f"Error fetching user usage: {str(e)}")
        return {}
