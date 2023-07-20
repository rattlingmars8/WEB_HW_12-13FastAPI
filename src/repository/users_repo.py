from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.DB.models import User
from src.schemas.User_Schemas import UserCreate
from src.services import authservice as auth_service


async def repo_create_user(body: UserCreate, db: AsyncSession):
    g = Gravatar(email=body.email)
    avatar_img_url = g.get_image()
    refresh_token = await auth_service.authservice.create_refresh_token({"sub": body.email})
    user = User(**body.dict(),
                created_at=datetime.utcnow(),
                avatar=avatar_img_url,
                refresh_token=refresh_token)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def repo_user_authentication_by_email(email: str, db: AsyncSession) -> User:
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalar()
    return existing_user


async def repo_update_refresh_token(user: User, new_refresh_token: str, db: AsyncSession):
    user.refresh_token = new_refresh_token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    user = await repo_user_authentication_by_email(email=email, db=db)
    user.is_activated = True
    await db.commit()


async def update_avatar(email, src_url, db: AsyncSession):
    user = await repo_user_authentication_by_email(email=email, db=db)
    user.avatar = src_url
    await db.commit()
    return user


async def add_reset_token_to_db(user, reset_token, db: AsyncSession):
    user.reset_token = reset_token
    await db.commit()
