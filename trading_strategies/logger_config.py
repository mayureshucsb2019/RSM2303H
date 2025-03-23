import logging

# def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
#     """Sets up a logger with the specified name and level."""
#     logger = logging.getLogger(name)
#     if not logger.hasHandlers():
#         handler = logging.StreamHandler()
#         formatter = logging.Formatter(
#             "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#         )
#         handler.setFormatter(formatter)
#         logger.addHandler(handler)
#         logger.setLevel(level)
#     return logger


def setup_logger(
    name: str, level: int = logging.INFO, log_file: str = "output.txt"
) -> logging.Logger:
    """Sets up a logger with the specified name, level, and optional file logging."""
    logger = logging.getLogger(name)

    if not logger.hasHandlers():  # Prevent duplicate handlers
        logger.setLevel(level)

        # Console handler (prints to terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # File handler (logs to file)
        file_handler = logging.FileHandler(log_file, mode="w")  # Use "a" for appending
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
