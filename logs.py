import logging
import os
import sys
from typing import Optional

import coloredlogs


class Logger:
    """Cria e configura loggers do módulo :mod:`logging`."""

    @classmethod
    def get_logger(
        cls,
        name: str = "main",
        level: int = logging.DEBUG,
        *,
        use_colors: Optional[bool] = None,
    ) -> logging.Logger:
        """Retorna um logger configurado e pronto para ser customizado.

        A detecção do suporte a cores e a configuração inicial ficam
        encapsuladas nesta classe. O retorno continua sendo um
        ``logging.Logger`` padrão, portanto seus handlers, formatters, nível e
        propagação podem ser alterados normalmente pelo código consumidor.
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.handlers:
            if use_colors is None:
                use_colors = cls._terminal_supports_colors()

            if use_colors:
                coloredlogs.install(level=level, logger=logger)
            else:
                handler = logging.StreamHandler()
                handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    )
                )
                logger.addHandler(handler)

        return logger

    @staticmethod
    def _terminal_supports_colors() -> bool:
        """Verifica se o terminal atual suporta saída colorida."""
        return (
            sys.stdout.isatty()
            and os.getenv("NO_COLOR") is None
            and os.getenv("TERM") != "dumb"
        )


logger = Logger.get_logger()
