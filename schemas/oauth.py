from uuid import UUID

from pydantic import BaseModel


class AccessToken(BaseModel):
    active: bool
    scope: str | None
    exp: int | None
    client_id: str | None
    user_id: str | None
    user_email: str | None
    user_phone_no: str | None
    authorities: list[str] | None


class OauthUser(BaseModel):

    id: UUID
    email: str
    first_name: str | None
    last_name: str | None
    full_name: str | None
    mobile_no: str | None
    email_verified: bool
    mobile_verified: bool
    avatar: str | None
    roles: list[str] | None
