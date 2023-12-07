"""
Module for start FastAPI application.
Manage databases for work bot and communication with users.
"""
import logging
from typing import List, Dict, Tuple, Literal
import os
import asyncio
import json
import uvicorn
import click
from starlette import status
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, Request

from getlogger import get_logger
from database import Base, engine
from database import sm as session_maker
from querysets import UsersQueryset, ReposQueryset, SubscriptionsQueryset, NotificationsQueryset
from schemas import UsersSchema, ReposSchema, SubscriptionsSchema, SubscriptionsByUserSchema


def request_to_api_github(api_uri: str, logger: logging.Logger) -> Tuple[str, str]:
    """
    Send GET request to API GitHub for getting latest repository release.
    Do 10 * 10 attempt get release info till don't get this
    :param api_uri: URL of API GitHub.
    :param logger: logger
    :return: tuple(release_number, release_data)
    """
    token = os.environ.get("GITHUB_API_TOKEN")

    session = requests.Session()
    retry = Retry(connect=10, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    new_release, new_release_date = None, None
    try:
        response = session.get(api_uri,
                               timeout=10,
                               headers={'Accept': 'application/vnd.github+json',
                                        'Authorization': f'Bearer {token}',
                                        'X-GitHub-Api-Version': '2022-11-28'})
        if response.status_code == 200:
            response = json.loads(response.text)
            new_release = response['tag_name']
            new_release_date = response['created_at']
            logger.info(f'Success parse release info by api_uri: {api_uri}')
    except Exception as e:
        logger.error(f"Wrong request API GitHub for api_uri: {api_uri}. Return error: {e}")

    return new_release, new_release_date


async def check_releases(app: FastAPI, logger: logging.Logger) -> None:
    """
    Select all data from table Repos and run getting info of release.
    If repository has new release - do update in table Repos
    and create new notification for users who have subscriptions.
    :param app: application FastAPI
    :param logger: logger
    :return: None
    """
    async with app.session_maker.begin() as session:
        select_all = await ReposQueryset.select_all(session)
        for id_repo, uri, api_uri, owner, repo_name, _, release_date in select_all:
            new_release, new_release_date = request_to_api_github(api_uri,
                                                                  logger=logger)
            if new_release and new_release_date:
                keys_repo = ['uri', 'api_uri', 'owner',
                             'repo_name', 'release', 'release_date']
                values_repo = [uri, api_uri, owner, repo_name, new_release, new_release_date]
                repo_as_dict = ReposSchema.model_validate(dict(zip(keys_repo,
                                                                   values_repo))).model_dump()

                if release_date < repo_as_dict['release_date']:
                    await ReposQueryset.update(session, repo_as_dict)
                    await NotificationsQueryset.create(session, id_repo)
                    logger.info(f'Repo {repo_name}(by {owner}) was update success.')


def create_app() -> FastAPI:
    """
    Create new application FastAPI with methods by REST
    :return: application FastAPI
    """
    async def lifespan(_: FastAPI):
        async with app.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info('Success connect to database and create tables.')
        app.scheduler.start()
        app.scheduler.add_job(check_releases, 'cron',
                              day_of_week='mon-sun',
                              hour=0, minute=0,
                              args=[app, logger])
        logger.info('Success create Job of parsing releases.')
        logger.info('Startup FastAPI.')

        yield

        await app.engine.dispose()
        logger.info('Shutdown FastAPI.')

    logger = get_logger()
    debug = True
    if os.environ.get('FASTAPI_DEBUG') == 'on':
        debug = False
    app = FastAPI(docs_url='/docs',
                  debug=debug,
                  lifespan=lifespan)
    app.engine = engine
    app.session_maker = session_maker
    app.scheduler = AsyncIOScheduler()

    logger.info('Application FastAPI was created.')

    @app.get('/get_releases/{user}', response_model=List[SubscriptionsByUserSchema])
    async def get_releases(request: Request, user: int):
        """
        Select all notifications on repos,
        if user have subscriptions on it's and them have new release.
        """
        try:
            async with request.app.session_maker.begin() as session:
                res = await NotificationsQueryset.get_repos_by_user(session, user)
                keys_subscriptions = ['user_id', 'owner', 'repo_name',
                                      'repo_uri', 'release', 'release_date']
                to_repo = SubscriptionsByUserSchema.model_validate
                response = [to_repo(dict(zip(keys_subscriptions, repo))) for repo in res]
                logger.info('Correct response new releases for user_id: %s', user)
                return response
        except Exception as e:
            logger.info('Wrong send new releases for user_id %s with error: %s', user, e)

    @app.get('/get_subscriptions/{user}', response_model=List[SubscriptionsByUserSchema])
    async def get_subscriptions(request: Request, user: int):
        """
        Select all subscriptions on repos by user.
        """
        try:
            async with request.app.session_maker.begin() as session:
                res = await SubscriptionsQueryset.get_repos_by_user(session, user)
                keys_subscriptions = ['user_id', 'owner', 'repo_name',
                                      'repo_uri', 'release', 'release_date']
                to_repo = SubscriptionsByUserSchema.model_validate
                response = [to_repo(dict(zip(keys_subscriptions, repo))) for repo in res]
                logger.info('Correct response subscriptions for user_id: %s', user)
                return response
        except Exception as e:
            logger.info('Wrong send subscriptions for user_id %s with error: %s', user, e)

    @app.post('/add_user',
              status_code=status.HTTP_201_CREATED)
    async def add_user(request: Request, data: UsersSchema):
        """
        Add new user in table Users when user have first conversation with bot.
        """
        try:
            async with request.app.session_maker.begin() as session:
                await UsersQueryset.create(session, **data.model_dump())
                logger.info('User create to database success: %s', data.model_dump()['user_id'])
        except Exception as e:
            logger.info('Something was wrong when try add user %s with error: %s',
                        data.model_dump()['user_id'], e)

    @app.post('/add_repos',
              status_code=status.HTTP_201_CREATED)
    async def add_repos(request: Request, data: Dict[str, int | List[List[str]]]):
        """
        Add subscriptions of user by list of repos.
        By every repository get release and release data and put on table Repos and Subscriptions.
        If repos have in table Repos and have new release:
        update for all user who can notifications on this repo.
        """
        subscriptions = {'user_id': data['user_id']}
        try:
            for repo in data['repos']:
                uri = f'https://github.com/{repo[0]}/{repo[1]}'
                api_uri = f'https://api.github.com/repos/{repo[0]}/{repo[1]}/releases/latest'
                release, release_date = request_to_api_github(api_uri, logger)
                if release and release_date:
                    keys_repo = ['uri', 'api_uri', 'owner',
                                 'repo_name', 'release', 'release_date']
                    values_repo = [uri, api_uri, repo[0], repo[1], release, release_date]

                    async with request.app.session_maker.begin() as session:
                        repo_as_dict = ReposSchema.model_validate(dict(zip(keys_repo,
                                                                           values_repo))
                                                                  ).model_dump()
                        id_repo, _, is_update = await ReposQueryset.create(session,
                                                                           repo_as_dict)
                    logger.info('Success create %s(by %s) in table Repos.', repo[1], repo[0])

                    if is_update:
                        async with request.app.session_maker.begin() as session:
                            await ReposQueryset.update(session, repo_as_dict)
                            await NotificationsQueryset.create(session, id_repo)

                    subscriptions['repo_id'] = id_repo
                    async with request.app.session_maker.begin() as session:
                        await SubscriptionsQueryset.create(session,
                                                           SubscriptionsSchema
                                                           .model_validate(subscriptions)
                                                           .model_dump())
        except Exception as e:
            logger.error('Wrong create repo with error: %s', e)

    @app.post('/delete_subscriptions',
              status_code=status.HTTP_200_OK)
    async def delete_subscriptions(request: Request, data: Dict[str, int | List[str]]):
        """
        Delete subscriptions of user by list of repos.
        """
        try:
            async with request.app.session_maker.begin() as session:
                await SubscriptionsQueryset.delete_by_user_and_repos(session,
                                                                     data['user_id'],
                                                                     data['repos'])
                await NotificationsQueryset.delete_by_user_and_repos(session,
                                                                     data['user_id'],
                                                                     data['repos'])
            logger.info('Success delete subscriptions(amount %s) for user_id %s.',
                        len(data['repos']), data['user_id'])
        except Exception as e:
            logger.error('Wrong delete subscriptions for user_id %s with error %s',
                         data['user_id'], e)

    @app.post('/delete_all_subscriptions',
              status_code=status.HTTP_200_OK)
    async def delete_all_repos(request: Request, user: Dict[str, int]):
        """
        Delete all subscriptions of user.
        """
        try:
            async with request.app.session_maker.begin() as session:
                await SubscriptionsQueryset.delete_by_user(session, user['user_id'])
                await NotificationsQueryset.delete_by_user(session, user['user_id'])
            logger.info('Success delete all subscriptions for user_id %s.', user['user_id'])
        except Exception as e:
            logger.error('Wrong delete all subscriptions for user_id %s with error %s',
                         user['user_id'], e)

    return app


@click.command()
@click.option('--host', '-h', default='0.0.0.0')
@click.option('--port', '-p', default=8880)
@click.option('--workers', '-w', default=1)
@click.option('--lifespan', '-ls', default='on')
def main(host: str, port: int, workers: int, lifespan: Literal[str]) -> None:
    """
    Run FastAPI application in uvicorn async loop
    :param host: host ip address
    :param port: host port
    :param workers: amount of workers applications
    :param lifespan: lifespan flag
    :return: None
    """
    uvicorn.run(f'{__name__}:create_app',
                host=host,
                port=port,
                workers=workers,
                lifespan=lifespan)


if __name__ == '__main__':
    asyncio.run(main())
