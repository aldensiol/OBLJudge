import logging


def setup_logger(reference: str) -> logging.Logger:
    """Setup a logger with the given reference name."""
    logger = logging.getLogger(reference)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
