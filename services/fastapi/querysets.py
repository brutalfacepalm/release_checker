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
    async def create(cls, session: AsyncSession, data_dict):
        to_update = await session.scalar(select(cls.model).where((cls.model.uri==data_dict['uri'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            return created.id, True
        else:
            return to_update.id, False


class SubscriptionsQueryset:
    model = Subscriptions

    @classmethod
    async def create(cls, session: AsyncSession, data_dict):
        to_update = await session.scalar(select(cls.model).where((cls.model.user_id==data_dict['user_id']) &
                                                                 (cls.model.repo_id==data_dict['repo_id'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            return created.id

class NotificationsQueryset:
    model = Notifications
