"""检索范围预设方案。"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessError
from ..models import SearchPreset
from ..schemas.preset import PresetCreate


async def list_presets(db: AsyncSession, user_id: int) -> list[SearchPreset]:
    result = await db.execute(
        select(SearchPreset)
        .where(SearchPreset.user_id == user_id)
        .order_by(SearchPreset.created_at.desc())
    )
    return list(result.scalars().all())


async def create_preset(db: AsyncSession, user_id: int, req: PresetCreate) -> SearchPreset:
    preset = SearchPreset(user_id=user_id, name=req.name, document_ids=req.document_ids)
    db.add(preset)
    await db.commit()
    await db.refresh(preset)
    return preset


async def delete_preset(db: AsyncSession, user_id: int, preset_id: int) -> None:
    preset = await db.get(SearchPreset, preset_id)
    if preset is None or preset.user_id != user_id:
        raise BusinessError("预设不存在", 404)
    await db.delete(preset)
    await db.commit()
