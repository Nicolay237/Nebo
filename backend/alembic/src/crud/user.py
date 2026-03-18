# src/crud/user.py
from typing import Optional, List
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.user import User


async def get_user_by_id(
    db: AsyncSession,
    user_id: int,
    load_relations: bool = False
) -> Optional[User]:
    """
    Получить пользователя по ID
    """
    stmt = select(User).where(User.id == user_id)
    
    if load_relations:
        stmt = stmt.options(
            # можно добавить подгрузку связанных сущностей, если нужно
            # например: selectinload(User.chats) — но это редко нужно здесь
        )
    
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str
) -> Optional[User]:
    """
    Получить пользователя по email (обычно используется при логине)
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_username(
    db: AsyncSession,
    username: str
) -> Optional[User]:
    """
    Получить пользователя по username (для поиска, упоминаний, etc.)
    """
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
    is_active: bool = True,
    is_superuser: bool = False,
    is_verified: bool = False
) -> User:
    """
    Создать нового пользователя (используется fastapi-users или вручную)
    """
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        is_active=is_active,
        is_superuser=is_superuser,
        is_verified=is_verified
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user_id: int,
    **kwargs
) -> Optional[User]:
    """
    Обновить поля пользователя
    Пример: await update_user(db, user_id=5, username="new_nick", is_active=False)
    """
    if not kwargs:
        return None

    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(**kwargs)
        .returning(User)
    )
    
    result = await db.execute(stmt)
    await db.commit()
    
    updated_user = result.scalar_one_or_none()
    if updated_user:
        await db.refresh(updated_user)
    
    return updated_user


async def search_users_by_username(
    db: AsyncSession,
    query: str,
    limit: int = 20,
    exclude_user_id: Optional[int] = None
) -> List[User]:
    """
    Поиск пользователей по части username (для функции "найти собеседника")
    """
    search_pattern = f"%{query}%"
    
    stmt = select(User).where(User.username.ilike(search_pattern))
    
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    
    stmt = stmt.order_by(User.username).limit(limit)
    
    result = await db.execute(stmt)
    return result.scalars().all()


async def set_user_online_status(
    db: AsyncSession,
    user_id: int,
    is_online: bool = True
) -> Optional[User]:
    """
    Простой способ отмечать онлайн-статус (можно расширить last_seen)
    """
    return await update_user(
        db,
        user_id=user_id,
        is_online=is_online,          # поле нужно добавить в модель, если хочешь
        # last_seen=datetime.utcnow() если добавишь поле
    )