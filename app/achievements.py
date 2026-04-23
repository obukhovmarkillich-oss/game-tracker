from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AchievementCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    date_earned: Optional[date] = None
    is_earned: bool = False


class AchievementUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    date_earned: Optional[date] = None
    is_earned: Optional[bool] = None


class AchievementResponse(BaseModel):
    id: int
    game_id: int
    name: str
    description: Optional[str]
    date_earned: Optional[date]
    is_earned: bool

    model_config = ConfigDict(from_attributes=True)
