"""
Module with all schemas data in application FastAPI
"""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class UsersSchema(BaseModel):
    """
    Schema of User data
    """
    user_id: int = Field(..., description='ID Telegram')
    username: str = Field(..., description='nickname')
    first_name: str = Field(..., description='First name')


class ReposSchema(BaseModel):
    """
    Schema of Repos data
    Have validation and transform release date to datetime
    """
    uri: str = Field(..., description='URI Repo')
    api_uri: str = Field(..., description='API URI Repo')
    owner: str = Field(..., description='Owner')
    repo_name: str = Field(..., description='Repo name')
    release: str = Field(..., description='Release tag')
    release_date: str | datetime = Field(..., description='Release date')

    @field_validator('release_date', mode='after')
    @classmethod
    def validate_release_date(cls, value):
        """
        Validation and transform Field release_date to datetime format
        :param value: release_date
        :return:
        """
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ', )


class SubscriptionsSchema(BaseModel):
    """
    Schema of Subscriptions data
    """
    user_id: int = Field(..., description='user id')
    repo_id: int = Field(..., description='repo id')


class SubscriptionsByUserSchema(BaseModel):
    """
    Schema of Subscriptions By User data
    Need for send to user.
    """
    user_id: int = Field(..., description='user id')
    owner: str = Field(..., description='repo owner')
    repo_name: str = Field(..., description='repo name')
    repo_uri: str = Field(..., description='repo URI')
    release: str = Field(..., description='release number')
    release_date: str | datetime = Field(..., description='release datetime')

    @field_validator('release_date', mode='after')
    @classmethod
    def validate_release_date(cls, value):
        """
        Validation and transform Field release_date from datetime format to string
        :param value: release_date
        :return:
        """
        return datetime.strftime(value, '%Y.%m.%d %H:%M:%S', )
