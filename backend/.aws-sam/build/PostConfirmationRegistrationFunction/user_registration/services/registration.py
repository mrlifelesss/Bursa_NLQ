from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from botocore.exceptions import ClientError

from .. import aws_clients
from ..config import RegistrationSettings

logger = logging.getLogger(__name__)


class RegistrationService:
    """Persist the application records that back a Cognito user."""

    def __init__(self, settings: RegistrationSettings) -> None:
        self._settings = settings
        self._users_table = aws_clients.dynamodb_table(settings.users_table)
        self._orgs_table = aws_clients.dynamodb_table(settings.organizations_table)
        self._cognito = aws_clients.cognito_idp_client()

    def register(self, *, user_id: str, email: str, name: Optional[str], user_pool_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        organization_id = str(uuid.uuid4())
        welcome_ends = now + timedelta(days=self._settings.welcome_period_days)

        user_item = {
            "userId": user_id,
            "organizationId": organization_id,
            "email": email,
            "displayName": name or "New User",
            "role": "owner",
            "language": self._settings.default_language,
            "createdAt": now.isoformat(),
        }

        org_item = {
            "organizationId": organization_id,
            "ownerUserId": user_id,
            "subscriptionTier": "free",
            "subscriptionStatus": "active",
            "tier1Limit": self._settings.tier1_limit,
            "tier1CreditsUsed": 0,
            "tier2Limit": self._settings.tier2_limit,
            "tier2CreditsUsed": 0,
            "welcomeCreditsExpiresAt": welcome_ends.isoformat(),
            "creditCycleResetAt": welcome_ends.isoformat(),
            "createdAt": now.isoformat(),
        }

        logger.info("Creating application records for user %s in organization %s", user_id, organization_id)

        try:
            self._users_table.put_item(Item=user_item, ConditionExpression="attribute_not_exists(userId)")
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
                raise
            logger.warning("User %s already exists in table %s", user_id, self._settings.users_table)

        self._orgs_table.put_item(Item=org_item)

        self._ensure_group_membership(user_id, user_pool_id)

        return {"user": user_item, "organization": org_item}

    def _ensure_group_membership(self, user_id: str, user_pool_id: str) -> None:
        group = self._settings.free_group_name
        if not group:
            return

        logger.info("Adding user %s to Cognito group %s", user_id, group)
        try:
            self._cognito.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=user_id,
                GroupName=group,
            )
        except ClientError:
            logger.exception("Failed to add user %s to Cognito group %s", user_id, group)
            raise