"""
Declare tables to database from class of model.
"""
from datetime import datetime as dt
from sqlalchemy import Column, BigInteger, Text, DateTime, Integer
from sqlalchemy.orm.collections import InstrumentedList
from database import Base


class BaseModel(Base):
    """
    Base model as parent for another models.
    """
    __abstract__ = True

    def to_dict(self):
        """
        Convert data model to Python dict and return.
        """
        data = {}
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            if isinstance(v, Base):
                v = v.to_dict()
            elif isinstance(v, InstrumentedList):
                v = [item.to_dict() for item in v]
            elif isinstance(v, dt):
                v = v.strftime('%d.%m.%Y %H:%M:%S.%f')[:-3]
            data[k] = v
        return data


class Users(BaseModel):
    """
    Declare Users table
    """
    __tablename__ = "users"
    __table_args__ = {'comment': 'Таблица пользователей.'}

    user_id = Column(BigInteger(), primary_key=True, nullable=False,
                     comment='ID пользователя Telegram')
    username = Column(Text(), nullable=False, comment='Никнейм пользователя')
    first_name = Column(Text(), nullable=False, comment='Имя пользователя')


class Repos(BaseModel):
    """
    Declare Repos table
    """
    __tablename__ = "repos"
    __table_args__ = {'comment': 'Таблица отслеживаемых библиотек.'}

    id = Column(Integer(), nullable=False, autoincrement=True, primary_key=True,
                comment='ID в базе данных')
    uri = Column(Text(), nullable=False, primary_key=True, comment='Ссылка на репозиторий')
    api_uri = Column(Text(), nullable=False, comment='Ссылка на репозиторий')
    owner = Column(Text(), nullable=False, comment='Владелец репозитория')
    repo_name = Column(Text(), nullable=False, comment='Название репозитория')
    release = Column(Text(), nullable=False, comment='Номер последнего релиза')
    release_date = Column(DateTime(), nullable=False, comment='Дата последнего релиза')


class Subscriptions(BaseModel):
    """
    Declare Subscriptions table
    """
    __tablename__ = "subscriptions"
    __table_args__ = {'comment': 'Таблица подписок.'}

    user_id = Column(Integer(), nullable=False, primary_key=True, comment='ID пользователя')
    repo_id = Column(Integer(), nullable=False, primary_key=True, comment='ID репозитория')


class Notifications(BaseModel):
    """
    Declare Notifications table.
    """
    __tablename__ = "notifications"
    __table_args__ = {'comment': 'Таблица актуальных обновлений библиотек.'}

    user_id = Column(Integer(), nullable=False, primary_key=True, comment='ID пользователя')
    repo_id = Column(Integer(), nullable=False, primary_key=True, comment='ID репозитория')


class NotificationJobs(BaseModel):
    """
    Declare NotificationJobs table.
    """
    __tablename__ = "notificationjobs"
    __table_args__ = {'comment': 'Таблица для рассылок подписанным юзерам.'}

    user_id = Column(Integer(), nullable=False, primary_key=True, comment='ID пользователя')
    chat_id = Column(Integer(), nullable=False, primary_key=True, comment='ID чата')
    hour = Column(Integer(), nullable=False, comment='Час уведомления')
    minute = Column(Integer(), nullable=False, comment='Минута уведомления')
