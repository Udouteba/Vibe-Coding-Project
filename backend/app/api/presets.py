from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.response import ok
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import User
from ..schemas.preset import PresetCreate, PresetOut
from ..services import preset_service

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("")
async def list_presets(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    presets = await preset_service.list_presets(db, user.id)
    return ok([PresetOut.model_validate(p).model_dump() for p in presets])


@router.post("")
async def create_preset(
    req: PresetCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    preset = await preset_service.create_preset(db, user.id, req)
    return ok(PresetOut.model_validate(preset).model_dump(), "保存成功")


@router.delete("/{preset_id}")
async def delete_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    await preset_service.delete_preset(db, user.id, preset_id)
    return ok(message="删除成功")
