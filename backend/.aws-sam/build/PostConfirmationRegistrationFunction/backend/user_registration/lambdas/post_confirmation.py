from __future__ import annotations

import json
import logging
from typing import Any, Dict

from ..config import MissingConfiguration, load_settings
from ..services.registration import RegistrationService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    """Handle a Cognito PostConfirmation trigger."""
    logger.info("Incoming Cognito event: %s", json.dumps(event))

    user_id = event.get("userName")
    attributes = event.get("request", {}).get("userAttributes", {})
    email = attributes.get("email")
    name = attributes.get("name")
    user_pool_id = event.get("userPoolId")

    if not user_id or not email:
        logger.error("userName or email missing from Cognito event; skipping registration")
        return event

    if not user_pool_id:
        logger.error("userPoolId missing from Cognito event; skipping registration")
        return event

    try:
        settings = load_settings()
    except MissingConfiguration:
        logger.exception("Registration Lambda is missing required configuration")
        raise

    service = RegistrationService(settings)

    try:
        service.register(user_id=user_id, email=email, name=name, user_pool_id=user_pool_id)
    except Exception:
        logger.exception("Failed to register Cognito user %s", user_id)
        raise

    return event