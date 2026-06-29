from fastapi import APIRouter, Depends, Query
from app.security.TokenValidator import TokenValidator

reportsRouter = APIRouter()

allow_admins_only = TokenValidator(allowed_roles=["admin", "super_admin"])


@reportsRouter.get("/cdr", status_code=200)
def get_cdr_by_phone(
    phone: str = Query(..., min_length=1),
    user=Depends(allow_admins_only),
):
    return []
