from datetime import datetime
from pydantic import BaseModel, Field, field_validator, validator


class UsersSchema(BaseModel):
    user_id: int = Field(..., description='ID Telegram')
    username: str = Field(..., description='nickname')
    first_name: str = Field(..., description='First name')


class UsersViewSchema(UsersSchema):
    id: int = Field(..., description='ID')


class ReposSchema(BaseModel):
    uri: str = Field(..., description='URI Repo')
    api_uri: str = Field(..., description='API URI Repo')
    owner: str = Field(..., description='Owner')
    repo_name: str = Field(..., description='Repo name')
    release: str = Field(..., description='Release tag')
    release_date: str = Field(..., description='Release date')

    @field_validator('release_date', mode='after')
    @classmethod
    def validate_release_date(cls, value):
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ', )


class ReposViewSchema(ReposSchema):
    id: int = Field(..., description='ID')


class SubscriptionsSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    repo_id: int = Field(..., description='repo id')


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
    release_date: datetime = Field(..., description='release datetime')


class NewReleasesViewSchema(NewReleasesSchema):
    id: int = Field(..., description='ID')


class SubscriptionsByUserSchema(BaseModel):
    user_id: int = Field(..., description='user id')
    owner: str = Field(..., description='repo owner')
    repo_name: str = Field(..., description='repo name')
    repo_uri: str = Field(..., description='repo URI')
    release: str = Field(..., description='release number')
    release_date: datetime = Field(..., description='release datetime')

    @field_validator('release_date', mode='after')
    @classmethod
    def validate_release_date(cls, value):
        return datetime.strftime(value, '%Y.%m.%d %H:%M:%S', )

class SubscriptionsByUserViewSchema(SubscriptionsByUserSchema):
    id: int = Field(..., description='ID')
