import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.db import get_db
from src.DB.models import User
from src.conf.config import settings
from src.schemas.User_Schemas import UserDBScheme
from src.services.authservice import authservice as auth_service
from src.repository import users_repo as user_repository
from src.services.avatar import UploadImage

user_router = APIRouter()


@user_router.get("/me", response_model=UserDBScheme)
async def get_my_info(current_user: User = Depends(auth_service.get_current_user)):
    return current_user


@user_router.patch('/avatar', response_model=UserDBScheme)
async def update_user_avatar(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: AsyncSession = Depends(get_db)):
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )

    public_id = UploadImage.generate_name_avatar(current_user.email)
    r = UploadImage.upload(file.file, public_id)
    src_url = UploadImage.get_url_for_avatar(public_id, r)
    user = await user_repository.update_avatar(email=current_user.email, src_url=src_url, db=db)
    return user

