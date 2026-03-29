from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserRepository:
    """
    Доступ к таблице users.
    Коммит/rollback выполняет вызывающий сервис; вставки идемпотентны по смыслу (PK user_id).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def ensure_user(self, user_id: int) -> bool:
        result = await self._session.execute(select(User).where(User.user_id == user_id))
        if result.scalar_one_or_none() is not None:
            return False
        self._session.add(User(user_id=user_id))
        return True

    async def record_get_access_unique(self, user_id: int) -> bool:
        result = await self._session.execute(select(User).where(User.user_id == user_id))
        row = result.scalar_one_or_none()
        if row is not None and row.get_access_clicked:
            return False
        if row is not None:
            row.get_access_clicked = True
        else:
            self._session.add(User(user_id=user_id, get_access_clicked=True))
        return True

    async def record_subscription_passed_unique(self, user_id: int) -> bool:
        result = await self._session.execute(select(User).where(User.user_id == user_id))
        row = result.scalar_one_or_none()
        if row is not None and row.subscription_passed:
            return False
        if row is not None:
            row.subscription_passed = True
        else:
            self._session.add(User(user_id=user_id, subscription_passed=True))
        return True

    async def get_admin_statistics(self) -> tuple[int, int, int]:
        total = await self._session.scalar(select(func.count()).select_from(User))
        access = await self._session.scalar(
            select(func.count()).select_from(User).where(User.get_access_clicked.is_(True))
        )
        passed = await self._session.scalar(
            select(func.count()).select_from(User).where(User.subscription_passed.is_(True))
        )
        return int(total or 0), int(access or 0), int(passed or 0)
