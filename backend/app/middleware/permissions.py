from fastapi import Depends, HTTPException

from app.middleware.auth import get_current_user
from app.models.user import User, RoleEnum


def require_roles(*roles: RoleEnum):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "success": False,
                    "message": "You do not have permission to perform this action",
                    "error_code": "FORBIDDEN",
                },
            )
        return current_user

    return checker


require_admin = require_roles(RoleEnum.ADMIN)
require_admin_or_reviewer = require_roles(RoleEnum.ADMIN, RoleEnum.REVIEWER)
require_any = require_roles(RoleEnum.ADMIN, RoleEnum.ASSESSOR, RoleEnum.REVIEWER)
