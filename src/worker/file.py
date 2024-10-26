import os
import tempfile
from datetime import datetime

from loguru import logger


def file_exists(filepath):
    """
    Checks if a file exists.

    :param filepath: The path to the file to check.
    :return: True if the file exists, False otherwise.
    """
    return os.path.exists(filepath)


def delete_file(filepath):
    """
    Deletes a file from the filesystem.

    :param filepath: The path to the file to delete.
    """
    if not file_exists(filepath):
        logger.warning(f"File does not exist: {filepath}")
        return
    try:
        os.remove(filepath)
        logger.debug(f"File deleted: {filepath}")
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        raise


def move_file_to_folder(filepath, folder):
    """
    Moves a file to a folder.

    :param filepath: The path to the file to move.
    :param folder: The path to the folder to move the file to.
    """
    try:
        os.replace(filepath, os.path.join(folder, os.path.basename(filepath)))
        logger.info(f"File moved: {filepath} -> {folder}")
    except Exception as e:
        logger.error(f"Failed to move file: {e}")
        raise


def get_filename_from_path(filepath):
    """
    Extracts the filename from a file path.

    :param filepath: The path to the file.
    :return: The filename.
    """
    return os.path.basename(filepath)


def get_backup_file(
    backup_name: str, backup_filename: str = None, date_format: str = None
):
    """
    Generates a backup file name and path.

    :param backup_name: The name of the backup.
    :param backup_filename: The filename of the backup.
    :param date_format: The date format to use in the filename.
    :return: A tuple containing the prefix, filename, and path.
    """
    tmp_dir = tempfile.gettempdir()
    prefix = backup_filename if backup_filename else f"{backup_name}" + "_"
    filename = f"{prefix}{datetime.now().strftime(date_format)}.sql"
    path = os.path.join(tmp_dir, filename)
    return prefix, filename, path
