import logging
import sys
import structlog
from structlog import processors

def setup_logging(debug: bool = False):
    """Configura logging estructurado para producción"""
    log_level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        stream=sys.stdout,
        format="%(message)s"
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            processors.TimeStamper(fmt="iso"),
            processors.StackInfoRenderer(),
            processors.format_exc_info,
            processors.UnicodeDecoder(),
            processors.CallsiteParameterAdder(
                parameters=[processors.CallsiteParameter.FILENAME,
                           processors.CallsiteParameter.LINENO]
            ),
            processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Obtiene un logger configurado"""
    return structlog.get_logger(name)