# src/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from src.database import async_session
from src.models.user import User
from src.config import settings
from fastapi_users import exceptions as users_exceptions
from fastapi_users.jwt import decode_jwt

# ───────────────────────────────────────────────
# 1. Получение асинхронной сессии БД
# ───────────────────────────────────────────────
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


# ───────────────────────────────────────────────
# 2. OAuth2 схема для Bearer-токена (JWT)
# ───────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/jwt/login",          # куда фронт отправляет логин для получения токена
    scheme_name="JWT"
)


# ───────────────────────────────────────────────
# 3. Получение текущего пользователя по JWT-токену
# ───────────────────────────────────────────────
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Зависимость, которая:
    - берёт токен из заголовка Authorization: Bearer ...
    - декодирует JWT
    - находит пользователя в базе по id из токена
    """
    try:
        payload = decode_jwt(
            token=token,
            secret=settings.JWT_SECRET,
            audience=None,  # если используете audience — укажите
            algorithms=[settings.ALGORITHM]
        )
    except users_exceptions.InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int | None = payload.get("sub")  # "sub" — стандартное поле для id пользователя

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит идентификатор пользователя"
        )

    # Запрос пользователя из базы
    from src.crud.user import get_user_by_id  # предполагаем, что у тебя есть такая функция
    # Если crud ещё нет — можно сделать запрос напрямую

    stmt = select(User).where(User.id == int(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь неактивен"
        )

    return user


# ───────────────────────────────────────────────
# 4. Готовые аннотации для частого использования
# ───────────────────────────────────────────────

# Текущий аутентифицированный пользователь (обязательный)
CurrentUser = Annotated[User, Depends(get_current_user)]

# Сессия базы данных (часто используется)
DBSession = Annotated[AsyncSession, Depends(get_db)]