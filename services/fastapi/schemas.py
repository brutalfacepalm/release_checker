from datetime import datetime as dt
from pydantic import BaseModel, Field, validator


class UsersSchema(BaseModel):
    user_id: int = Field(..., description='ID Telegram')
    username: str = Field(..., description='nickname')
    first_name: str = Field(..., description='First name')


class UsersViewSchema(UsersSchema):
    id: int = Field(..., description='ID')


class ReposSchema(BaseModel):
    uri: str = Field(..., description='URI Repo')
    owner: str = Field(..., description='Owner')
    repo_name: str = Field(..., description='Repo name')
    release: str = Field(..., description='Release tag')
    release_date: dt = Field(..., description='Release date')


class ReposViewSchema(ReposSchema):
    id: int = Field(..., description='ID')


class SubscriptionsSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    repo_id: str = Field(..., description='repo id')


class SubscriptionsViewSchema(SubscriptionsSchema):
    id: int = Field(..., description='ID')


class NotificationsSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    repo_id: str = Field(..., description='repo id')


class NotificationsViewSchema(NotificationsSchema):
    id: int = Field(..., description='ID')


class NewReleasesSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    owner: str = Field(..., description='repo owner')
    repo_name: str = Field(..., description='repo name')
    repo_uri: str = Field(..., description='repo URI')
    release: str = Field(..., description='release number')
    release_date: dt = Field(..., description='release datetime')


class NewReleasesViewSchema(NewReleasesSchema):
    id: int = Field(..., description='ID')


class SubscriptionsByUserSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    owner: str = Field(..., description='repo owner')
    repo_name: str = Field(..., description='repo name')
    repo_uri: str = Field(..., description='repo URI')
    release: str = Field(..., description='release number')
    release_date: dt = Field(..., description='release datetime')


class SubscriptionsByUserViewSchema(SubscriptionsByUserSchema):
    id: int = Field(..., description='ID')
