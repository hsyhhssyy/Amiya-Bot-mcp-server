from __future__ import annotations
import logging

from ...helpers.bundle import get_table

from ...app.context import AppContext
from ...domain.models.operator import Operator
from ...domain.types import QueryResult
from ...helpers.glossary import mark_glossary_used_terms

logger = logging.getLogger(__name__)

class OperatorNotFoundError(ValueError):
    pass

