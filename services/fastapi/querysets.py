from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from models import Users, Repos, Subscriptions, Notifications


class UsersQueryset:
    model = Users

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        created = cls.model(**kwargs)
        await session.merge(created)
        await session.flush([created])


class ReposQueryset:
    model = Repos

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        created = cls.model(**kwargs)
        await session.merge(created)
        await session.flush([created])


class SubscriptionsQueryset:
    model = Subscriptions


class NotificationsQueryset:
    model = Notifications
