"""
AfroMations - Lemon Squeezy Billing Integration
Works in demo mode when keys aren't configured.
"""
import os
import hmac
import json
import hashlib
import httpx
from typing import Optional, Dict, Any

LS_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LS_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
LS_WEBHOOK_SECRET = os.environ.get("LEMON_SQUEEZY_WEBHOOK_SECRET", "")
LS_BASE = "https://api.lemonsqueezy.com/v1"

# Map plan IDs to Lemon Squeezy variant IDs
# Set LEMON_SQUEEZY_VARIANT_{PLAN_ID} env vars with your real variant IDs
PLAN_VARIANTS: Dict[str, Dict[str, str]] = {
    "creator_pro": {
        "annual": os.environ.get("LS_VARIANT_CREATOR_PRO_ANNUAL", ""),
        "two_year": os.environ.get("LS_VARIANT_CREATOR_PRO_2YEAR", ""),
    },
    "studio": {
        "annual": os.environ.get("LS_VARIANT_STUDIO_ANNUAL", ""),
        "two_year": os.environ.get("LS_VARIANT_STUDIO_2YEAR", ""),
    },
    "black_label": {
        "annual": os.environ.get("LS_VARIANT_BLACK_LABEL_ANNUAL", ""),
        "two_year": os.environ.get("LS_VARIANT_BLACK_LABEL_2YEAR", ""),
    },
}

PLAN_PRICES = {
    "creator_pro": {"annual": 2400, "two_year": 4200},
    "studio": {"annual": 9600, "two_year": 16800},
    "black_label": {"annual": 36000, "two_year": 60000},
}


def billing_available() -> bool:
    return bool(LS_API_KEY and LS_STORE_ID)


async def create_checkout(
    plan_id: str,
    term: str,
    user_email: str,
    user_name: str,
    custom_data: Dict = None,
) -> Dict[str, Any]:
    """
    Create a Lemon Squeezy checkout session.
    Returns checkout URL or demo data if not configured.
    """
    if not billing_available():
        return {
            "demo": True,
            "url": f"https://afromations.lemonsqueezy.com/checkout/demo?plan={plan_id}&term={term}",
            "plan": plan_id,
            "term": term,
            "price": PLAN_PRICES.get(plan_id, {}).get(term, 0),
            "message": "Billing not configured. Set LEMON_SQUEEZY_API_KEY to enable real payments.",
        }

    variant_id = PLAN_VARIANTS.get(plan_id, {}).get(term, "")
    if not variant_id:
        return {
            "demo": True,
            "url": f"https://afromations.lemonsqueezy.com/checkout/demo?plan={plan_id}&term={term}",
            "message": f"Variant ID not configured for {plan_id}/{term}. Set LS_VARIANT_{plan_id.upper()}_{term.upper()} env var.",
        }

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "name": user_name,
                    "custom": custom_data or {},
                },
                "product_options": {
                    "redirect_url": os.environ.get("APP_URL", "https://afromations.app") + "/billing/success",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": LS_STORE_ID}},
                "variant": {"data": {"type": "variants", "id": variant_id}},
            },
        }
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{LS_BASE}/checkouts",
            headers={
                "Accept": "application/vnd.api+json",
                "Content-Type": "application/vnd.api+json",
                "Authorization": f"Bearer {LS_API_KEY}",
            },
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return {
            "url": data["data"]["attributes"]["url"],
            "checkout_id": data["data"]["id"],
            "plan": plan_id,
            "term": term,
        }


def verify_webhook(payload_bytes: bytes, signature: str) -> bool:
    """Verify Lemon Squeezy webhook signature."""
    if not LS_WEBHOOK_SECRET:
        return True  # Skip verification in demo mode
    expected = hmac.new(
        LS_WEBHOOK_SECRET.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def parse_webhook_event(payload: Dict) -> Dict[str, Any]:
    """
    Parse Lemon Squeezy webhook payload into an actionable event.
    Returns: {event, user_email, plan, status, ls_id, ls_customer_id, period_end}
    """
    meta = payload.get("meta", {})
    event = meta.get("event_name", "")
    data = payload.get("data", {})
    attrs = data.get("attributes", {})
    custom = meta.get("custom_data", {}) or attrs.get("first_subscription_item", {})

    # Map Lemon Squeezy event → our internal action
    action_map = {
        "subscription_created": "activate",
        "subscription_updated": "update",
        "subscription_cancelled": "cancel",
        "subscription_expired": "expire",
        "subscription_payment_failed": "past_due",
        "subscription_payment_success": "renew",
        "order_created": "activate",
    }

    return {
        "event": event,
        "action": action_map.get(event, "unknown"),
        "ls_id": str(data.get("id", "")),
        "ls_customer_id": str(attrs.get("customer_id", "")),
        "user_email": attrs.get("user_email", ""),
        "plan": attrs.get("product_name", "").lower().replace(" ", "_"),
        "status": attrs.get("status", "active"),
        "period_end": attrs.get("renews_at") or attrs.get("ends_at"),
        "custom_data": meta.get("custom_data", {}),
    }
