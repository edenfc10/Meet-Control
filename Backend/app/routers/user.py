# ============================================================================
# User Router - API routes for user management
# ============================================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schema.user import BoolOutput, UserInCreateNoRole, UserOutput
from app.security.TokenValidator import TokenValidator
from app.service.userService import UserService
from logger import LoggerManager


userRouter = APIRouter()

allow_super_admin_only = TokenValidator(allowed_roles=["super_admin"])
allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])
validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent"])
all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])


@userRouter.get("/all", status_code=200, response_model=list[UserOutput])
def get_all_users(session: Session = Depends(get_db), user=Depends(validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested all users",
            user.s_id,
            user.UUID,
            user.role.value,
        )
        return UserService(session=session).get_all_users(
            current_user_role=user.role.value,
            current_user_uuid=str(user.UUID),
        )
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch all users for requester %s:%s role=%s",
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.get("/{s_id}", status_code=200, response_model=UserOutput)
def get_user_by_s_id(s_id: str, session: Session = Depends(get_db), user=Depends(validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested user by s_id=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            s_id,
        )
        requested_user = UserService(session=session).get_user_by_s_id_for_requester(
            s_id=s_id,
            requester_role=user.role.value,
            requester_uuid=str(user.UUID),
        )
        return UserOutput.model_validate(requested_user, from_attributes=True)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch user s_id=%s for requester %s:%s role=%s",
            s_id,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))
    

@userRouter.get("/uuid/{uuid}", status_code=200, response_model=UserOutput)
def get_user_by_uuid(uuid: str, session: Session = Depends(get_db), user=Depends(validator)):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested user by uuid=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            uuid,
        )
        requested_user = UserService(session=session).get_user_by_uuid(
            uuid=uuid,
        )
        return UserOutput.model_validate(requested_user, from_attributes=True)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch user uuid=%s for requester %s:%s role=%s",
            uuid,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.post("/create-agent", status_code=200, response_model=UserOutput)
def create_agent_user(
    user_data: UserInCreateNoRole,
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    try:
        LoggerManager.get_logger().info(
            "Creating agent user with s_id=%s by requester s_id=%s role=%s",
            user_data.s_id,
            user.s_id,
            user.role.value,
        )
        return UserService(session=session).create_agent_user(user_data=user_data)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create agent user s_id=%s by requester %s:%s role=%s",
            user_data.s_id,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.post("/create-admin", status_code=200, response_model=UserOutput)
def create_admin_user(
    user_data: UserInCreateNoRole,
    session: Session = Depends(get_db),
    user=Depends(allow_super_admin_only),
):
    try:
        LoggerManager.get_logger().info(
            "Creating admin user with s_id=%s by requester s_id=%s role=%s",
            user_data.s_id,
            user.s_id,
            user.role.value,
        )
        return UserService(session=session).create_admin_user(user_data=user_data)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create admin user s_id=%s by requester %s:%s role=%s",
            user_data.s_id,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.post("/create-viewer", status_code=200, response_model=UserOutput)
def create_viewer_user(
    user_data: UserInCreateNoRole,
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),  # admin, super_admin בלבד
):
    try:
        LoggerManager.get_logger().info(
            "Creating viewer user with s_id=%s by requester s_id=%s role=%s",
            user_data.s_id,
            user.s_id,
            user.role.value,
        )
        return UserService(session=session).create_viewer_user(user_data=user_data)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to create viewer user s_id=%s by requester %s:%s role=%s",
            user_data.s_id,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))
    
@userRouter.put("/update/{user_uuid}", status_code=200, response_model=UserOutput)
def update_user_details(
    user_uuid: str,
    update_data: UserInCreateNoRole,
    session: Session = Depends(get_db),
    user=Depends(allow_admins_only),
):
    try:
        requester_role = getattr(user.role, "value", user.role)
        # בדיקת הרשאות לשינוי role
        if update_data.role is not None:
            new_role = getattr(update_data.role, "value", update_data.role)
            ROLE_HIERARCHY = {"super_admin": 4, "admin": 3, "agent": 2, "viewer": 1}
            if ROLE_HIERARCHY.get(new_role, 0) >= ROLE_HIERARCHY.get(requester_role, 0):
                raise HTTPException(status_code=403, detail="You cannot assign a role equal to or higher than your own.")
        LoggerManager.get_logger().info(
            "Updating user details for user_uuid=%s by requester s_id=%s role=%s",
            user_uuid,
            user.s_id,
            user.role.value,
        )
        return UserService(session=session).update_details_on_user(
            user_uuid=user_uuid,
            update_data=update_data,
        )
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to update user details for user_uuid=%s by requester %s:%s role=%s",
            user_uuid,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.delete("/{user_id}", status_code=200, response_model=BoolOutput)
def delete_user(user_id: str, session: Session = Depends(get_db), user=Depends(allow_admins_only)):
    try:
        LoggerManager.get_logger().info(
            "Deleting user s_id=%s by requester s_id=%s role=%s",
            user_id,
            user.s_id,
            user.role.value,
        )
        success = UserService(session=session).delete_user(
            user_id=user_id,
            current_user_role=user.role.value,
            current_user_s_id=user.s_id,
        )
        return BoolOutput(success=success)
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to delete user s_id=%s by requester %s:%s role=%s",
            user_id,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))


@userRouter.get("/group/{group_uuid}/meetings", status_code=200, response_model=list[str])
def get_group_meetings_by_user_uuid(
    group_uuid: str,
    session: Session = Depends(get_db),
    user=Depends(validator),
):
    try:
        LoggerManager.get_logger().info(
            "User %s:%s with role %s requested group meetings for group_uuid=%s",
            user.s_id,
            user.UUID,
            user.role.value,
            group_uuid,
        )
        return UserService(session=session).get_group_meetings_by_user_uuid(
            user_uuid=str(user.UUID),
            group_uuid=group_uuid,
        )
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch group meetings for group_uuid=%s by requester %s:%s role=%s",
            group_uuid,
            user.s_id,
            user.UUID,
            user.role.value,
        )
        raise HTTPException(status_code=500, detail=str(error))
