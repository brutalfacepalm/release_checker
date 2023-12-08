"""
Module with querysets of models.
Declare logic CRUD.
"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from models import Users, Repos, Subscriptions, Notifications, NotificationJobs


class UsersQueryset:
    """
    Manage table Users.
    """
    model = Users

    @classmethod
    async def create(cls, session: AsyncSession, **kwargs):
        """
        Create user in table Users.
        """
        created = cls.model(**kwargs)
        await session.merge(created)
        await session.flush([created])


class ReposQueryset:
    """
    Manage table Repos.
    """
    model = Repos

    @classmethod
    async def select_all(cls, session: AsyncSession):
        """
        Select all from data table Repos.
        """
        query = text("SELECT * FROM repos;")
        select_all = await session.execute(query)
        return select_all

    @classmethod
    async def create(cls, session: AsyncSession, data_dict):
        """
        Create new repo if not exist.
        If it's exist: check release data and new data of release.
        If it's need to update - declare current repo as update.
        """
        to_update = await session.scalar(select(cls.model)
                                         .where((cls.model.uri == data_dict['uri'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            id_, is_create, is_update = created.id, True, False
        else:
            if to_update.release_date < data_dict['release_date']:
                id_, is_create, is_update = to_update.id, False, True
            else:
                id_, is_create, is_update = to_update.id, False, False
        return id_, is_create, is_update

    @classmethod
    async def update(cls, session: AsyncSession, data_dict):
        """
        If it's need update repo in table - set new value of release and release_date
        """
        release = data_dict['release']
        release_date = data_dict['release_date']
        uri = data_dict['uri']

        query = text(f"""UPDATE repos SET release='{release}', 
        release_date='{release_date}' WHERE uri='{uri}';""")
        await session.execute(query)


class SubscriptionsQueryset:
    """
    Manage table Subscriptions.
    """
    model = Subscriptions

    @classmethod
    async def create(cls, session: AsyncSession, data_dict):
        """
        Create new subscriptions. If user already have subscription on repos - do nothing.
        """
        to_update = await session.scalar(select(cls.model)
                                         .where((cls.model.user_id == data_dict['user_id']) &
                                                (cls.model.repo_id == data_dict['repo_id'])))
        if not to_update:
            created = cls.model(**data_dict)
            await session.merge(created)
            await session.flush([created])
            # return created.id

    @classmethod
    async def get_repos_by_user(cls, session, user):
        """
        Select all repos and info of them by user.
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
        Delete all subscriptions from table by user.
        """
        query = text(f"""DELETE FROM subscriptions AS s WHERE s.user_id={user};""")
        await session.execute(query)

    @classmethod
    async def delete_by_user_and_repos(cls, session, user, repos):
        """
        Delete concrete repos from subscriptions of user.
        """
        query = text(f"""DELETE FROM subscriptions AS s WHERE s.user_id={user} 
        AND s.repo_id IN (SELECT r.id FROM repos AS r 
        WHERE r.uri IN ({', '.join(repos)}));""")
        await session.execute(query)


class NotificationsQueryset:
    """
    Manage table Notifications.
    """
    model = Notifications

    @classmethod
    async def create(cls, session: AsyncSession, id_repo):
        """
        Create notifications if user have subscriptions by repo_id.
        """
        query = text(f"""INSERT INTO notifications (user_id, repo_id) 
        (SELECT s.user_id, s.repo_id FROM subscriptions AS s 
        WHERE s.repo_id={id_repo}) ON CONFLICT DO NOTHING;""")
        await session.execute(query)

    @classmethod
    async def get_repos_by_user(cls, session, user):
        """
        Select all notifications by user and delete them after send message.
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
        Delete all notifications by user.
        """
        query = text(f"""DELETE FROM notifications AS n WHERE n.user_id={user};""")
        await session.execute(query)

    @classmethod
    async def delete_by_user_and_repos(cls, session, user, repos):
        """
        Delete concrete notifications by user and repos_id.
        """
        query = text(f"""DELETE FROM notifications AS n WHERE n.user_id={user} 
        AND n.repo_id IN (SELECT r.id FROM repos AS r 
        WHERE r.uri IN ({', '.join(repos)}));""")
        await session.execute(query)


class NotificationJobsQueryset:
    """
    Manage table NotificationJobs.
    In this table have time of notifications whom user set in bot.
    """
    model = NotificationJobs

    @classmethod
    async def create(cls, session: AsyncSession, job):
        """
        Create new time of job notifications.
        """
        query = text(f"""INSERT INTO notificationjobs 
        (user_id, chat_id, hour, minute) 
        VALUES ({', '.join(map(str, job))});""")
        await session.execute(query)

    @classmethod
    async def select(cls, session: AsyncSession):
        """
        Select all settings of notifications.
        Need for start bot and run job early if was set by user.
        """
        query = text("SELECT * FROM notificationjobs;")
        jobs = await session.execute(query)
        return jobs

    @classmethod
    async def delete(cls, session: AsyncSession, user):
        """
        Delete notification job by user.
        """
        query = text(f"""DELETE FROM notificationjobs WHERE user_id={user};""")
        await session.execute(query)
