"""ideanest_assesment models."""

from typing import Sequence, Type

from beanie import Document

from ideanest_assesment.db.models.dummy_model import DummyModel


def load_all_models() -> Sequence[Type[Document]]:
    """Load all models from this folder."""
    return [
        DummyModel,
    ]
