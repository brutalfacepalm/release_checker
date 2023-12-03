from sqlalchemy import select, update, text
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
            ## TO DO CHECK NEW RELEASES AND UPDATE NOTIFICATIONS TABLE
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

    @classmethod
    async def get_repos_by_user(cls, session, user):
        query = text(f"""SELECT s.user_id, r.owner, r.repo_name, 
        r.uri, r.release, r.release_date FROM subscriptions AS s
        JOIN repos AS r ON s.repo_id=r.id WHERE s.user_id={user} 
        ORDER BY (r.repo_name, r.owner) ASC;""")
        repos = await session.execute(query)
        return repos



class NotificationsQueryset:
    model = Notifications
