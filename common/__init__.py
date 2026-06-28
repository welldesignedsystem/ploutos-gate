import logging as _logging
_logging.getLogger("startup").info("common package loaded, importing startup")
from common import startup  # noqa: F401 — patches scheduler endpoint before uvicorn
