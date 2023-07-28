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
    """
        Отримати інформацію про поточного користувача.

        Ця функція виконує HTTP GET запит до шляху "/me" для отримання інформації про
        поточного користувача, який автентифікований в системі.

        Args:
            current_user (User, залежність): Об'єкт користувача, отриманий залежністю
                                             від функції auth_service.get_current_user.

        Returns:
            UserDBScheme: Об'єкт користувача, що містить інформацію про поточного користувача
                          у форматі UserDBScheme.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до інформації.

        Example:
            Приклад успішного запиту та відповіді:
            GET https://yourapi.com/me
            Response:
            {
                 "username": "example_user",
                 "email": "user@example.com",
                 "avatar": "https://yourapi.com/static/avatars/avatar_example.jpg",
            }
        """
    return current_user


@user_router.patch('/avatar', response_model=UserDBScheme)
async def update_user_avatar(file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user),
                             db: AsyncSession = Depends(get_db)):
    """
        Оновити аватар користувача.

        Ця функція виконує HTTP PATCH запит до шляху "/avatar" для оновлення аватару
        поточного користувача.

        Args:
            file (UploadFile, необов'язковий): Файл зображення для оновлення аватару.
            current_user (User, залежність): Об'єкт користувача, отриманий залежністю
                                             від функції auth_service.get_current_user.
            db (AsyncSession, залежність): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            UserDBScheme: Об'єкт користувача, який містить оновлену інформацію про користувача
                          у форматі UserDBScheme.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до оновлення аватару.
            HTTPException(400): Виникає, якщо файл зображення не надіслано або формат
                                файлу не підтримується.

        Example:
             Приклад успішного запиту та відповіді:
             PATCH https://yourapi.com/avatar
             Request Body:
             (file with image data)

        Response:

            {
                 "username": "example_user",

                 "email": "user@example.com",

                 "avatar": "https://yourapi.com/static/avatars/avatar_example.jpg",
            }
        """
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

