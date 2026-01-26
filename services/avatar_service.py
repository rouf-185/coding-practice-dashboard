"""
Avatar service - Business logic for profile picture operations.
"""
import os
import secrets
from typing import Optional, Tuple
from PIL import Image, ImageOps
from flask import current_app
from repositories import UserRepository
from models import User


class AvatarService:
    """Service for avatar/profile picture operations."""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    @staticmethod
    def _get_upload_dir() -> str:
        """Get the avatar upload directory, creating if needed."""
        upload_dir = current_app.config.get('AVATAR_UPLOAD_DIR')
        if not upload_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            upload_dir = os.path.join(base_dir, 'static', 'uploads', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir
    
    @staticmethod
    def _is_allowed_file(filename: str) -> bool:
        """Check if file extension is allowed."""
        if not filename or '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in AvatarService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def _save_resized_avatar(image_file, user_id: int) -> str:
        """
        Save a square resized avatar.
        
        Returns:
            Static-relative path, e.g. 'uploads/avatars/user_1_xxx.png'
        """
        upload_dir = AvatarService._get_upload_dir()
        
        img = Image.open(image_file)
        img = ImageOps.exif_transpose(img)
        img = img.convert('RGB')
        img = ImageOps.fit(img, (256, 256), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        
        token = secrets.token_urlsafe(8)
        filename = f"user_{user_id}_{token}.png"
        abs_path = os.path.join(upload_dir, filename)
        img.save(abs_path, format='PNG', optimize=True)
        
        return f"uploads/avatars/{filename}"
    
    @staticmethod
    def _delete_file(rel_path: str) -> None:
        """Delete an avatar file by relative path."""
        if not rel_path:
            return
        
        upload_dir = AvatarService._get_upload_dir()
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(base_dir, 'static', rel_path)
        
        # Security: only delete if it's in the upload directory
        if abs_path.startswith(upload_dir) and os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception:
                pass
    
    @staticmethod
    def upload_avatar(user: User, file) -> Tuple[bool, str]:
        """
        Upload and save a new avatar for the user.
        
        Returns:
            Tuple of (success, message)
        """
        if not file or not file.filename:
            return False, 'Please choose an image to upload.'
        
        if not AvatarService._is_allowed_file(file.filename):
            return False, 'Please upload a PNG, JPG, or WEBP image.'
        
        try:
            new_rel_path = AvatarService._save_resized_avatar(file, user.id)
        except Exception as e:
            print(f"Avatar upload error: {e}")
            return False, 'Could not process that image. Please try a different file.'
        
        # Delete old avatar
        if user.profile_image:
            AvatarService._delete_file(user.profile_image)
        
        user.profile_image = new_rel_path
        UserRepository.update(user)
        
        return True, 'Profile picture updated.'
    
    @staticmethod
    def delete_avatar(user: User) -> Tuple[bool, str]:
        """
        Delete user's avatar.
        
        Returns:
            Tuple of (success, message)
        """
        if user.profile_image:
            AvatarService._delete_file(user.profile_image)
        
        user.profile_image = None
        UserRepository.update(user)
        
        return True, 'Profile picture deleted.'
