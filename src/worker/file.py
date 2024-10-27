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
    backup_id: str, backup_filename: str = None, date_format: str = None
):
    """
    Generates a backup file name and path.

    :param backup_id: The name of the backup.
    :param backup_filename: The filename of the backup.
    :param date_format: The date format to use in the filename.
    :return: A tuple containing the prefix, filename, and path.
    """
    tmp_dir = tempfile.gettempdir()
    prefix = backup_filename if backup_filename else f"{backup_id}" + "_"
    filename = f"{prefix}{datetime.now().strftime(date_format)}.sql"
    path = os.path.join(tmp_dir, filename)
    return prefix, filename, path


def get_backup_date_from_filename(
    filename: str, filename_prefix: str, date_format: str
):
    """
    Extracts the date from a backup file name.

    :param filename: The backup file name.
    :param filename_prefix: The prefix of the backup file name.
    :param date_format: The date format used in the backup file name.
    :return: The date extracted from the file name.
    """
    try:
        date_str = filename[len(filename_prefix) :]
        date_str = date_str.split(".sql")[0]
        return datetime.strptime(date_str, date_format)
    except Exception as e:
        logger.error(f"Failed to extract date from filename '{filename}': {e}")
        return None


def get_backups_to_delete(files, filename_prefix, date_format, max_backup_files):
    """
    Returns a list of files to delete based on the max_backup_files limit.

    :param files: List of backup files.
    :param filename_prefix: Prefix of the backup filenames.
    :param date_format: Date format used in the backup filenames.
    :param max_backup_files: Maximum number of backup files to keep.
    :return: List of files to delete.
    """
    if not files:
        return []

    files = [file for file in files if file.startswith(filename_prefix)]
    files_to_delete = []

    for file in files:
        date = get_backup_date_from_filename(file, filename_prefix, date_format)
        if not date:
            continue
        files_to_delete.append((date, file))

    files_to_delete.sort()
    if len(files_to_delete) > max_backup_files:
        return [file for _, file in files_to_delete[:-max_backup_files]]
    return []
