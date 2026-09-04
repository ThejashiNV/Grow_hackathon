"""Lightweight session mechanism (Part 34/35).

No passwords, no OAuth: a random user_id in an httpOnly cookie, persisted in
MongoDB. This is deliberately not full auth -- the problem statement asks for
cross-session/cross-device persistence with server-side state as the source
of truth, not a login system. Swappable for real auth later without touching
the watchlist/diff-engine services, which only ever see a `user_id` string.
"""

import uuid
from datetime import UTC, datetime

from fastapi import Request, Response

from app.core.database import get_db

SESSION_COOKIE = "sw_user_id"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365  # 1 year


async def get_current_user_id(request: Request, response: Response) -> str:
    user_id = request.cookies.get(SESSION_COOKIE)
    if not user_id:
        user_id = uuid.uuid4().hex
        response.set_cookie(
            SESSION_COOKIE,
            user_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
        )

    db = get_db()
    if db is not None:
        await db.users.update_one(
            {"user_id": user_id},
            {"$setOnInsert": {"user_id": user_id, "created_at": datetime.now(UTC)}},
            upsert=True,
        )
    return user_id
