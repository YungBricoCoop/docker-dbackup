import lzma
from loguru import logger


def compress_file(filepath):
    """
    Compresses a file using XZ compression.

    :param filepath: The path to the file to compress.
    :return: The path to the compressed file.
    """
    compressed_filepath = filepath + ".xz"

    try:
        with open(filepath, "rb") as input_file:
            with lzma.open(compressed_filepath, "wb") as output_file:
                output_file.write(input_file.read())
        logger.debug(f"File compressed successfully: {compressed_filepath}")
        return compressed_filepath
    except Exception as e:
        logger.error(f"Compression failed: {e}")
        raise e


def decompress_file(filepath):
    """
    Decompresses a file using XZ compression.

    :param filepath: The path to the file to decompress.
    :return: The path to the decompressed file.
    """
    decompressed_filepath = filepath[:-3]
    logger.info(f"Decompressing file: {filepath} -> {decompressed_filepath}")

    try:
        with lzma.open(filepath, "rb") as input_file:
            with open(decompressed_filepath, "wb") as output_file:
                output_file.write(input_file.read())
        logger.info(f"File decompressed successfully: {decompressed_filepath}")
        return decompressed_filepath
    except Exception as e:
        logger.error(f"Decompression failed: {e}")
        raise e
