from __future__ import annotations

from typing import Any

from fastapi import Header


async def get_current_user(
    x_user_id: str | None = Header(default="system", alias="X-User-Id"),
    x_user_type: str | None = Header(default="admin", alias="X-User-Type"),
) -> dict[str, Any]:
    user_type = (x_user_type or "admin").strip().lower()
    if user_type not in {"user", "merchant", "admin"}:
        user_type = "admin"

    final_user_id = (x_user_id or "system").strip() or "system"

    return {
        "user_id": final_user_id,
        "user_type": user_type,
    }
