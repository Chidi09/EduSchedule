from fastapi import HTTPException, status
from typing import List, Optional
from core.dependencies import supabase

class RBACError(HTTPException):
    """Custom exception for RBAC violations"""
    def __init__(self, detail: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class RolePermissions:
    """Define what each role can do"""
    ADMIN = [
        "create_teacher",
        "delete_teacher",
        "manage_school",
        "view_all_data",
        "create_timetable",
        "delete_timetable",
        "manage_subjects",
        "manage_rooms",
        "manage_classes"
    ]

    TEACHER = [
        "view_own_schedule",
        "update_own_preferences",
        "view_students",
        "view_subjects"
    ]

    STUDENT = [
        "view_own_schedule",
        "view_timetable"
    ]

def get_user_profile(user_id: str) -> dict:
    """Get user profile with role and school information"""
    try:
        response = supabase.table('profiles').select(
            "id, role, school_id, email, name"
        ).eq('id', user_id).single().execute()

        if not response.data:
            raise RBACError("User profile not found")

        return response.data
    except Exception as e:
        raise RBACError(f"Failed to get user profile: {str(e)}")

def require_role(user: dict, allowed_roles: List[str]) -> dict:
    """Ensure user has one of the allowed roles"""
    user_role = user.get('role')

    if not user_role:
        raise RBACError("User role not defined")

    if user_role not in allowed_roles:
        raise RBACError(f"Access denied. Required roles: {', '.join(allowed_roles)}")

    return user

def require_admin(user: dict) -> dict:
    """Shortcut to require admin role"""
    return require_role(user, ['admin'])

def require_admin_or_teacher(user: dict) -> dict:
    """Allow both admins and teachers"""
    return require_role(user, ['admin', 'teacher'])

def require_same_school(user: dict, target_school_id: Optional[str] = None) -> dict:
    """Ensure user belongs to the same school as the target resource"""
    user_school = user.get('school_id')

    if not user_school:
        raise RBACError("User is not associated with any school")

    if target_school_id and user_school != target_school_id:
        raise RBACError("Access denied. Different school")

    return user

def can_access_resource(user: dict, resource_owner_id: str) -> bool:
    """Check if user can access a resource owned by another user"""
    user_role = user.get('role')
    user_id = user.get('id')

    # Users can always access their own resources
    if user_id == resource_owner_id:
        return True

    # Admins can access resources in their school
    if user_role == 'admin':
        # Get resource owner's profile to check school
        try:
            owner_profile = get_user_profile(resource_owner_id)
            return user.get('school_id') == owner_profile.get('school_id')
        except:
            return False

    # Teachers can only access their own resources by default
    return False

def require_permission(user: dict, permission: str) -> dict:
    """Check if user has specific permission"""
    user_role = user.get('role')

    role_permissions = {
        'admin': RolePermissions.ADMIN,
        'teacher': RolePermissions.TEACHER,
        'student': RolePermissions.STUDENT
    }

    permissions = role_permissions.get(user_role, [])

    if permission not in permissions:
        raise RBACError(f"Permission '{permission}' denied for role '{user_role}'")

    return user

def validate_school_access(user: dict, school_id: str) -> dict:
    """Validate user has access to specific school"""
    user_school = user.get('school_id')
    user_role = user.get('role')

    if not user_school:
        raise RBACError("User not associated with any school")

    # Super admins (if implemented later) could access any school
    # For now, users can only access their own school
    if user_school != school_id:
        raise RBACError("Access denied to this school")

    return user

# Convenience decorators for FastAPI dependencies
def admin_required(current_user: dict) -> dict:
    """FastAPI dependency to require admin role"""
    profile = get_user_profile(current_user.id)
    return require_admin(profile)

def teacher_or_admin_required(current_user: dict) -> dict:
    """FastAPI dependency to require teacher or admin role"""
    profile = get_user_profile(current_user.id)
    return require_admin_or_teacher(profile)

def same_school_required(school_id: str):
    """FastAPI dependency factory to require same school"""
    def _check_school(current_user: dict) -> dict:
        profile = get_user_profile(current_user.id)
        return validate_school_access(profile, school_id)
    return _check_school

# Audit logging for security events
def log_rbac_violation(user_id: str, action: str, resource: str, reason: str):
    """Log RBAC violations for security monitoring"""
    try:
        supabase.table('security_log').insert({
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'violation_reason': reason,
            'timestamp': 'now()',
            'severity': 'high'
        }).execute()
    except Exception as e:
        # Don't fail the request if logging fails, but print for debugging
        print(f"Failed to log RBAC violation: {e}")

def check_resource_ownership(user: dict, resource_table: str, resource_id: str, id_field: str = 'id') -> dict:
    """Verify user owns or can access a specific resource"""
    try:
        # Get the resource
        resource = supabase.table(resource_table).select("*").eq(id_field, resource_id).single().execute().data

        if not resource:
            raise RBACError("Resource not found")

        # Check ownership or admin access
        resource_user_id = resource.get('user_id') or resource.get('created_by')

        if not can_access_resource(user, resource_user_id):
            log_rbac_violation(
                user.get('id'),
                f"access_{resource_table}",
                resource_id,
                "Insufficient permissions"
            )
            raise RBACError("Access denied to this resource")

        return user
    except RBACError:
        raise
    except Exception as e:
        raise RBACError(f"Failed to verify resource access: {str(e)}")
