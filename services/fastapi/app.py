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

    @app.get('/get_releases/{user}', response_model=List[NewReleasesSchema])
    async def get_releases(request: Request):
        pass

    @app.get('/get_subscriptions/{user}', response_model=List[SubscriptionsByUserSchema])
    async def get_subscriptions(request: Request):
        pass

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
        for repository in data['repos']:
            owner = repository[0]
            repo_name = repository[1]
            uri = f'https://github.com/{owner}/{repo_name}'
            api_uri = f'https://api.github.com/repos/{owner}/{repo_name}/releases/latest'

            response = requests.get(api_uri,
                                    headers={'Authorization': f'token:{token}',
                                             'X-GitHub-Api-Version': '2022-11-28'})
            response = json.loads(response.text)
            release = response['tag_name']
            release_date = datetime.strptime(response['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            print(type(release_date))

            repo_to_load = {'uri': uri,
                            'api_uri': api_uri,
                            'owner': owner,
                            'repo_name': repo_name,
                            'release': release,
                            'release_date': release_date}

            async with sm.begin() as session:
                repo_to_load_as_schema = ReposSchema.model_validate(repo_to_load)
                await ReposQueryset.create(session, **repo_to_load_as_schema.model_dump())

    @app.post('/delete_subscriptions/{user}/{repos}')
    async def delete_repos(request: Request):
        pass

    @app.post('/delete_all_subscriptions/{user}')
    async def delete_all_repos(request: Request):
        pass

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
