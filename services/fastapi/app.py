from fastapi import FastAPI, Request
import uvicorn
import click
import asyncio
from starlette import status
from datetime import datetime
import requests
import json

from typing import List, Dict
from getlogger import get_logger
from database import Base, engine
from database import sm as session_maker
from querysets import UsersQueryset, ReposQueryset, SubscriptionsQueryset, NotificationsQueryset
from schemas import (UsersSchema, UsersViewSchema,
                     ReposSchema, ReposViewSchema,
                     SubscriptionsSchema, SubscriptionsViewSchema,
                     NotificationsSchema, NotificationsViewSchema,
                     NewReleasesSchema, NewReleasesViewSchema,
                     SubscriptionsByUserSchema, SubscriptionsByUserViewSchema)


def create_app():

    async def lifespan(app: FastAPI):
        async with app.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info('Startup FastAPI')

        yield

        await app.engine.dispose()
        logger.info('Shutdown FastAPI')

    logger = get_logger()
    app = FastAPI(docs_url='/docs',
                  debug=True,
                  lifespan=lifespan)
    app.engine = engine
    app.session_maker = session_maker
    logger.info('Application FastAPI was created')

    async def check_releases(session):
        token = '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'
        select_all = await ReposQueryset.select_all(session)
        for id_repo, uri, api_uri, owner, repo_name, release, release_date in select_all:
            response = requests.get(api_uri,
                                    headers={'Authorization': f'token:{token}',
                                             'X-GitHub-Api-Version': '2022-11-28'})
            response = json.loads(response.text)
            new_release = response['tag_name']
            new_release_date = response['created_at']

            repo_to_load = {'uri': uri,
                            'api_uri': api_uri,
                            'owner': owner,
                            'repo_name': repo_name,
                            'release': new_release,
                            'release_date': new_release_date}

            repo_to_load_as_schema = ReposSchema.model_validate(repo_to_load)
            repo_as_dict = repo_to_load_as_schema.model_dump()

            if release_date < repo_as_dict['release_date']:
                await ReposQueryset.update(session, repo_as_dict)
                await NotificationsQueryset.create(session, id_repo)

    @app.get('/get_releases/{user}', response_model=List[SubscriptionsByUserSchema])
    async def get_releases(request: Request, user: int):
        sm = request.app.session_maker
        response = []
        async with sm.begin() as session:
            await check_releases(session)

            res = await NotificationsQueryset.get_repos_by_user(session, user)
            for by_repo in res:
                one_repo = {'user_id': by_repo[0],
                            'owner': by_repo[1],
                            'repo_name': by_repo[2],
                            'repo_uri': by_repo[3],
                            'release': by_repo[4],
                            'release_date': by_repo[5]}
                repo = SubscriptionsByUserSchema.model_validate(one_repo)
                response.append(repo)
        return response

    @app.get('/get_subscriptions/{user}', response_model=List[SubscriptionsByUserSchema])
    async def get_subscriptions(request: Request, user: int):
        sm = request.app.session_maker
        response = []
        async with sm.begin() as session:
            res = await SubscriptionsQueryset.get_repos_by_user(session, user)
            for by_repo in res:
                one_repo = {'user_id': by_repo[0],
                            'owner': by_repo[1],
                            'repo_name': by_repo[2],
                            'repo_uri': by_repo[3],
                            'release': by_repo[4],
                            'release_date': by_repo[5]}
                repo = SubscriptionsByUserSchema.model_validate(one_repo)
                response.append(repo)
        return response

    @app.post('/add_user',
              status_code=status.HTTP_201_CREATED)
    async def add_user(request: Request, data: UsersSchema):
        sm = request.app.session_maker
        async with sm.begin() as session:
            await UsersQueryset.create(session, **data.model_dump())

    @app.post('/add_repos',
              status_code=status.HTTP_201_CREATED)
    async def add_repos(request: Request, data: Dict[str, int | List[List[str]]]):
        token = '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'
        sm = request.app.session_maker
        user_id = data['user_id']
        subscriptions = {'user_id': user_id}
        for repo in data['repos']:
            owner = repo[0]
            repo_name = repo[1]
            uri = f'https://github.com/{owner}/{repo_name}'
            api_uri = f'https://api.github.com/repos/{owner}/{repo_name}/releases/latest'

            response = requests.get(api_uri,
                                    headers={'Authorization': f'token:{token}',
                                             'X-GitHub-Api-Version': '2022-11-28'})
            response = json.loads(response.text)
            release = response['tag_name']
            release_date = response['created_at']

            repo_to_load = {'uri': uri,
                            'api_uri': api_uri,
                            'owner': owner,
                            'repo_name': repo_name,
                            'release': release,
                            'release_date': release_date}

            async with sm.begin() as session:
                repo_to_load_as_schema = ReposSchema.model_validate(repo_to_load)
                repo_as_dict = repo_to_load_as_schema.model_dump()
                id_repo, is_created, is_update = await ReposQueryset.create(session, repo_as_dict)

            if is_update:
                async with sm.begin() as session:
                    await ReposQueryset.update(session, repo_as_dict)
                    await NotificationsQueryset.create(session, id_repo)

            subscriptions['repo_id'] = id_repo
            async with sm.begin() as session:
                subscriptions_to_load_as_schema = SubscriptionsSchema.model_validate(subscriptions)
                subscriptions_as_dict = subscriptions_to_load_as_schema.model_dump()
                await SubscriptionsQueryset.create(session, subscriptions_as_dict)

    @app.post('/delete_subscriptions',
              status_code=status.HTTP_200_OK)
    async def delete_repos(request: Request, data: Dict[str, int | List[str]]):
        sm = request.app.session_maker
        async with sm.begin() as session:
            await SubscriptionsQueryset.delete_by_user_and_repos(session, data['user_id'], data['repos'])
            await NotificationsQueryset.delete_by_user_and_repos(session, data['user_id'], data['repos'])

    @app.post('/delete_all_subscriptions',
              status_code=status.HTTP_200_OK)
    async def delete_all_repos(request: Request, user: Dict[str, int]):
        sm = request.app.session_maker
        async with sm.begin() as session:
            await SubscriptionsQueryset.delete_by_user(session, user['user_id'])
            await NotificationsQueryset.delete_by_user(session, user['user_id'])

    return app


@click.command()
@click.option('--host', '-h', default='0.0.0.0')
@click.option('--port', '-p', default=8880)
@click.option('--workers', '-w', default=1)
@click.option('--lifespan', '-ls', default='on')
def main(host, port, workers, lifespan):
    uvicorn.run(f'{__name__}:create_app',
                host=host,
                port=port,
                workers=workers,
                lifespan=lifespan)


if __name__ == '__main__':
    asyncio.run(main())
