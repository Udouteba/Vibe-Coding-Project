from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config import CATEGORIES

from ..common.response import ok
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..services import document_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
async def list_categories(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    counts = await document_service.category_counts(db)
    return ok([{"name": c, "count": counts.get(c, 0)} for c in CATEGORIES])
