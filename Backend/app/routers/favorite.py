from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schema.favorite import FavoriteMeetingOutput, FavoriteToggleResponse
from app.security.TokenValidator import TokenValidator
from app.service.favoriteMeetingService import FavoriteMeetingService
from logger import LoggerManager


favoriteRouter = APIRouter()

all_members_validator = TokenValidator(allowed_roles=["admin", "super_admin", "agent", "viewer"])


@favoriteRouter.post("/meetings/{meeting_uuid}", status_code=200, response_model=FavoriteToggleResponse)
def add_meeting_to_favorites(
    meeting_uuid: str = Path(..., pattern=r"^[0-9a-fA-F-]{36}$"),
    session: Session = Depends(get_db),
    user=Depends(all_members_validator),
):
    user_role = getattr(user.role, "value", user.role)
    try:
        FavoriteMeetingService(session=session).add_favorite(
            user_uuid=str(user.UUID),
            user_role=str(user_role),
            meeting_uuid=meeting_uuid,
        )
        return {"detail": "Meeting added to favorites"}
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to add meeting UUID=%s to favorites for user %s:%s role=%s. Error: %s",
            meeting_uuid,
            user.s_id,
            user.UUID,
            user_role,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@favoriteRouter.delete("/meetings/{meeting_uuid}", status_code=200, response_model=FavoriteToggleResponse)
def remove_meeting_from_favorites(
    meeting_uuid: str = Path(..., pattern=r"^[0-9a-fA-F-]{36}$"),
    session: Session = Depends(get_db),
    user=Depends(all_members_validator),
):
    try:
        FavoriteMeetingService(session=session).remove_favorite(
            user_uuid=str(user.UUID),
            meeting_uuid=meeting_uuid,
        )
        return {"detail": "Meeting removed from favorites"}
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to remove meeting UUID=%s from favorites for user %s:%s. Error: %s",
            meeting_uuid,
            user.s_id,
            user.UUID,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")


@favoriteRouter.get("/meetings", status_code=200, response_model=list[FavoriteMeetingOutput])
def get_my_favorite_meetings(
    session: Session = Depends(get_db),
    user=Depends(all_members_validator),
):
    user_role = getattr(user.role, "value", user.role)
    try:
        return FavoriteMeetingService(session=session).get_user_favorites(
            user_uuid=str(user.UUID),
            user_role=str(user_role),
        )
    except HTTPException as http_error:
        raise http_error
    except Exception as error:
        LoggerManager.get_logger().exception(
            "Failed to fetch favorites for user %s:%s role=%s. Error: %s",
            user.s_id,
            user.UUID,
            user_role,
            str(error),
        )
        raise HTTPException(status_code=500, detail="Internal Server Error")
