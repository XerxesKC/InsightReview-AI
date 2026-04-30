from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user

DBSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict[str, str], Depends(get_current_user)]  
