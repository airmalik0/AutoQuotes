import hashlib
import hmac
import json
from urllib.parse import parse_qs, unquote


def validate_init_data(init_data: str, bot_token: str) -> dict | None:
    """Validate Telegram Mini App init_data using HMAC-SHA256.
    Returns parsed user data if valid, None otherwise.
    """
    parsed = parse_qs(init_data)

    if "hash" not in parsed:
        return None

    received_hash = parsed.pop("hash")[0]

    # Build data-check-string
    data_check_pairs = []
    for key in sorted(parsed.keys()):
        data_check_pairs.append(f"{key}={unquote(parsed[key][0])}")
    data_check_string = "\n".join(data_check_pairs)

    # Compute secret key
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()

    # Compute hash
    computed_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return None

    # Extract user info
    user_data = parsed.get("user")
    if not user_data:
        return None

    return json.loads(unquote(user_data[0]))
