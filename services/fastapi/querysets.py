"""
blabla
"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from models import Users, Repos, Subscriptions, Notifications, NotificationJobs


class UsersQueryset:
    """
    blabla
    """
    model = Users

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        """
        blabla
        """
        created = cls.model(**kwargs)
        await session.merge(created)
        await session.flush([created])


class ReposQueryset:
    """
    blabla
    """
    model = Repos

    @classmethod
    async def select_all(cls, session: AsyncSession):
        """
        blabla
        """
        query = text("SELECT * FROM repos;")
        select_all = await session.execute(query)
        return select_all

    @classmethod
    async def create(cls, session: AsyncSession, data_dict):
        """
        blabla
        """
        to_update = await session.scalar(select(cls.model)
                                         .where((cls.model.uri==data_dict['uri'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            return created.id, True, False
        else:
            if to_update.release_date < data_dict['release_date']:
                return to_update.id, False, True
            else:
                return to_update.id, False, False

    @classmethod
    async def update(cls, session: AsyncSession, data_dict):
        """
        blabla
        """
        release = data_dict['release']
        release_date = data_dict['release_date']
        uri = data_dict['uri']

        query = text(f"""UPDATE repos SET release='{release}', 
        release_date='{release_date}' WHERE uri='{uri}';""")
        await session.execute(query)


class SubscriptionsQueryset:
    """
    blabla
    """
    model = Subscriptions

    @classmethod
    async def create(cls, session: AsyncSession, data_dict):
        """
        blabla
        """
        to_update = await session.scalar(select(cls.model)
                                         .where((cls.model.user_id==data_dict['user_id']) &
                                                (cls.model.repo_id==data_dict['repo_id'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            # return created.id

    @classmethod
    async def get_repos_by_user(cls, session, user):
        """
        blabla
        """
        query = text(f"""SELECT s.user_id, r.owner, r.repo_name, 
        r.uri, r.release, r.release_date FROM subscriptions AS s
        JOIN repos AS r ON s.repo_id=r.id WHERE s.user_id={user} 
        ORDER BY (r.repo_name, r.owner) ASC;""")
        repos = await session.execute(query)
        return repos

    @classmethod
    async def delete_by_user(cls, session, user):
        """
        blabla
        """
        query = text(f"""DELETE FROM subscriptions AS s WHERE s.user_id={user};""")
        await session.execute(query)

    @classmethod
    async def delete_by_user_and_repos(cls, session, user, repos):
        """
        blabla
        """
        query = text(f"""DELETE FROM subscriptions AS s WHERE s.user_id={user} 
        AND s.repo_id IN (SELECT r.id FROM repos AS r 
        WHERE r.uri IN ({', '.join(repos)}));""")
        await session.execute(query)


class NotificationsQueryset:
    """
    blabla
    """
    model = Notifications

    @classmethod
    async def create(cls, session: AsyncSession, id_repo):
        """
        blabla
        """
        query = text(f"""INSERT INTO notifications (user_id, repo_id) 
        (SELECT s.user_id, s.repo_id FROM subscriptions AS s 
        WHERE s.repo_id={id_repo}) ON CONFLICT DO NOTHING;""")
        await session.execute(query)

    @classmethod
    async def get_repos_by_user(cls, session, user):
        """
        blabla
        """
        query = text(f"""SELECT n.user_id, r.owner, r.repo_name, 
        r.uri, r.release, r.release_date FROM notifications AS n
        JOIN repos AS r ON n.repo_id=r.id WHERE n.user_id={user} 
        ORDER BY (r.repo_name, r.owner) ASC;""")
        repos = await session.execute(query)
        await cls.delete_by_user(session, user)
        return repos

    @classmethod
    async def delete_by_user(cls, session, user):
        """
        blabla
        """
        query = text(f"""DELETE FROM notifications AS n WHERE n.user_id={user};""")
        await session.execute(query)

    @classmethod
    async def delete_by_user_and_repos(cls, session, user, repos):
        """
        blabla
        """
        query = text(f"""DELETE FROM notifications AS n WHERE n.user_id={user} 
        AND n.repo_id IN (SELECT r.id FROM repos AS r 
        WHERE r.uri IN ({', '.join(repos)}));""")
        await session.execute(query)


class NotificationJobsQueryset:
    """
    blabla
    """
    model = NotificationJobs

    @classmethod
    async def create(cls, session: AsyncSession, user, chat_id, hour, minute):
        """
        blabla
        """
        query = text(f"""INSERT INTO notificationjobs 
        (user_id, chat_id, hour, minute) 
        VALUES ({user}, {chat_id}, {hour}, {minute});""")
        await session.execute(query)

    @classmethod
    async def select(cls, session: AsyncSession):
        """
        blabla
        """
        query = text(f"""SELECT * FROM notificationjobs;""")
        jobs = await session.execute(query)
        return jobs

    @classmethod
    async def delete(cls, session: AsyncSession, user):
        """
        blabla
        """
        query = text(f"""DELETE FROM notificationjobs WHERE user_id={user};""")
        await session.execute(query)
