from fastapi import FastAPI, Request
import uvicorn
import click
import asyncio
from starlette import status

from typing import List
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
        print(data)
        sm = request.app.session_maker
        async with sm.begin() as session:
            await UsersQueryset.create(session, **data.model_dump())

    @app.post('/add_repos/{user}/{repos}')
    async def add_repos(request: Request):
        pass

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
