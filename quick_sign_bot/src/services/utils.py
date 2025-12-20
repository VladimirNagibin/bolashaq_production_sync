import hashlib

# import mimetypes
import os
import uuid
from datetime import datetime
from typing import Any

import magic


def generate_unique_filename(original_filename: str) -> str:
    """Генерация уникального имени файла"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_str = uuid.uuid4().hex[:8]
    name, ext = os.path.splitext(original_filename)
    return f"{timestamp}_{random_str}{ext}"


def get_file_hash(file_path: str) -> str:
    """Вычисление хэша файла"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def validate_file_extension(
    filename: str, allowed_extensions: list[Any]
) -> tuple[bool, str]:
    """Проверка расширения файла"""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Неподдерживаемый формат файла: {ext}"
    return True, ""


def validate_file_size(file_size: int, max_size: int) -> tuple[bool, str]:
    """Проверка размера файла"""
    if file_size > max_size:
        mb_size = max_size // 1024 // 1024
        return False, f"Файл слишком большой. Максимальный размер: {mb_size}MB"
    return True, ""


def detect_file_type(file_path: str) -> str:
    """Определение типа файла"""
    try:
        mime = magic.from_file(file_path, mime=True)
        return mime  # type: ignore[no-any-return]
    except Exception:
        return "application/octet-stream"


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от опасных символов"""
    # Удаляем опасные символы
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in dangerous_chars:
        filename = filename.replace(char, "_")

    # Ограничиваем длину
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename


def create_upload_folder(upload_folder: str) -> None:
    """Создание папки для загрузок если не существует"""
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)
        os.chmod(upload_folder, 0o755)  # Права на чтение/запись
