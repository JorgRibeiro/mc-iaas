import logging
import sys
import time


LOGGER_NAME = "jorge_agent"


def configure_logging() -> None:
    logger = logging.getLogger(
        LOGGER_NAME
    )

    logger.setLevel(
        logging.INFO
    )

    # Impede duplicação através do root logger,
    # que também é configurado pelo Uvicorn.
    logger.propagate = False

    # Evita adicionar vários handlers caso
    # a configuração seja chamada novamente.
    if logger.handlers:
        return

    handler = logging.StreamHandler(
        sys.stdout
    )

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)sZ "
            "%(levelname)s "
            "%(name)s "
            "%(message)s"
        ),
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # Logs operacionais usam UTC.
    formatter.converter = time.gmtime

    handler.setFormatter(
        formatter
    )

    logger.addHandler(
        handler
    )
