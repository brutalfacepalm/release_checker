import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# host = os.environ.get("DATABASE_HOST")
# port = int(os.environ.get("DATABASE_PORT"))
# login = os.environ.get("DATABASE_USER")
# password = os.environ.get("DATABASE_PASSWORD")
# name = os.environ.get("DATABASE_NAME")

host = '0.0.0.0'
port = 5432
login = 'fastapi'
password = 'fastapi'
name = 'fastapi'

engine = create_async_engine(f'postgresql+asyncpg://{login}:{password}@{host}:{port}/{name}')
sm = sessionmaker(engine, autocommit=False, autoflush=False, class_=AsyncSession)

Base = declarative_base()
