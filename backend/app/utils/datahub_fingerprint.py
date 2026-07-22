"""Deterministic fingerprint for the normalized DataHub context pack."""

from app.schemas.datahub_context import DataHubContextPack
from app.utils.fingerprint import fingerprint_payload


def fingerprint_datahub_context(context: DataHubContextPack) -> str:
    """Hash the complete normalized pack using the locked canonical JSON form."""
    if not isinstance(context, DataHubContextPack):
        raise TypeError("context must be a DataHubContextPack")
    return fingerprint_payload(context.model_dump(mode="json"))
