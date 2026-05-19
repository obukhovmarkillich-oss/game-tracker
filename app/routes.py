from datetime import date, datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict, Field

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app import auth
from app.achievements import AchievementCreate, AchievementResponse, AchievementUpdate
from app.external_api import get_game_details, search_games
from app.models import Achievement, Game, User
from app.utils import format_playtime, minutes_to_hours

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GameCreate(BaseModel):
    title: str
    platform: Optional[str] = None
    release_date: Optional[date] = None
    tags: Optional[str] = None
    rating: Optional[int] = None
    play_time_minutes: int = 0
    external_id: Optional[int] = None


class GameUpdate(BaseModel):
    title: Optional[str] = None
    platform: Optional[str] = None
    release_date: Optional[date] = None
    tags: Optional[str] = None
    rating: Optional[int] = None
    external_id: Optional[int] = None


class GameResponse(BaseModel):
    id: int
    title: str
    platform: Optional[str]
    release_date: Optional[date]
    user_id: int
    rating: Optional[int]
    tags: Optional[str]
    play_time_minutes: int
    external_id: Optional[int]
    details: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GameListResponse(BaseModel):
    items: list[GameResponse]
    total: int
    page: int
    size: int
    pages: int


class PlayTimeUpdate(BaseModel):
    minutes_to_add: int


class TopGame(BaseModel):
    title: str
    play_time_minutes: int
    play_time_hours: float


class StatsResponse(BaseModel):
    total_play_time_minutes: int
    total_play_time_hours: float
    total_achievements: int
    earned_achievements: int
    top_games: list[TopGame]
    games_count: int
    average_rating: Optional[float]


# ── Auth endpoints ────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=Token,
    summary="Register a new user",
    description="Create a new user account and return an access token. Password must be at least 8 characters.",
)
def register(user_data: UserCreate, db: Session = Depends(auth.get_db)):
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=auth.hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/login",
    response_model=Token,
    summary="Login and get access token",
    description="Authenticate with username (or email) and password. Returns a bearer token for subsequent requests.",
)
def login(user_data: UserLogin, db: Session = Depends(auth.get_db)):
    if not user_data.username and not user_data.email:
        raise HTTPException(status_code=400, detail="Username or email required")

    user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if not user or not auth.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# ── Games endpoints ───────────────────────────────────────────────

@router.get(
    "/games",
    response_model=GameListResponse,
    summary="List user's games",
    description="Return a paginated list of games owned by the authenticated user. Supports filtering by tag and minimum rating.",
)
def list_games(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=50, description="Items per page (max 50)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    min_rating: Optional[int] = Query(None, description="Filter by minimum rating"),
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    query = db.query(Game).filter(Game.user_id == current_user.id)

    if tag:
        query = query.filter(Game.tags.contains(tag))

    if min_rating is not None:
        query = query.filter(Game.rating >= min_rating)

    total = query.count()
    pages = (total + size - 1) // size if total > 0 else 0
    items = [GameResponse.model_validate(g) for g in query.order_by(Game.created_at.desc()).offset((page - 1) * size).limit(size).all()]

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


@router.post(
    "/games",
    response_model=GameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new game",
    description="Create a new game entry in the authenticated user's collection.",
)
def create_game(
    game_data: GameCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = Game(
        title=game_data.title,
        platform=game_data.platform,
        release_date=game_data.release_date,
        tags=game_data.tags,
        rating=game_data.rating,
        play_time_minutes=game_data.play_time_minutes,
        external_id=game_data.external_id,
        user_id=current_user.id,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return GameResponse.model_validate(game)


@router.get(
    "/games/{game_id}",
    response_model=GameResponse,
    summary="Get game details",
    description="Return details of a specific game. Includes external API data if an external_id is set.",
)
def get_game(
    game_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    result = GameResponse.model_validate(game)
    if game.external_id:
        result.details = get_game_details(game.external_id)
    return result


@router.put(
    "/games/{game_id}",
    response_model=GameResponse,
    summary="Update a game",
    description="Update fields of an existing game. Only provided fields will be changed.",
)
def update_game(
    game_id: int,
    game_data: GameUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    update_data = game_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(game, field, value)

    db.commit()
    db.refresh(game)
    return GameResponse.model_validate(game)


@router.delete(
    "/games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a game",
    description="Permanently remove a game from the user's collection.",
)
def delete_game(
    game_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    db.delete(game)
    db.commit()


@router.patch(
    "/games/{game_id}/playtime",
    response_model=GameResponse,
    summary="Add playtime to a game",
    description="Add minutes to the total playtime of an existing game.",
)
def add_playtime(
    game_id: int,
    playtime_data: PlayTimeUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    game.play_time_minutes += playtime_data.minutes_to_add
    db.commit()
    db.refresh(game)
    return GameResponse.model_validate(game)


# ── Achievements endpoints ────────────────────────────────────────

@router.post(
    "/games/{game_id}/achievements",
    response_model=AchievementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an achievement to a game",
    description="Create a new achievement entry for a specific game in the user's collection.",
)
def create_achievement(
    game_id: int,
    achievement_data: AchievementCreate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    game = db.query(Game).filter(Game.id == game_id, Game.user_id == current_user.id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    achievement = Achievement(
        game_id=game_id,
        name=achievement_data.name,
        description=achievement_data.description,
        date_earned=achievement_data.date_earned,
        is_earned=achievement_data.is_earned,
    )
    db.add(achievement)
    db.commit()
    db.refresh(achievement)
    return AchievementResponse.model_validate(achievement)


@router.put(
    "/achievements/{achievement_id}",
    response_model=AchievementResponse,
    summary="Update an achievement",
    description="Update fields of an existing achievement. Only provided fields will be changed.",
)
def update_achievement(
    achievement_id: int,
    achievement_data: AchievementUpdate,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    achievement = db.query(Achievement).join(Game).filter(
        Achievement.id == achievement_id, Game.user_id == current_user.id
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    update_data = achievement_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(achievement, field, value)

    db.commit()
    db.refresh(achievement)
    return AchievementResponse.model_validate(achievement)


@router.delete(
    "/achievements/{achievement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an achievement",
    description="Permanently remove an achievement from a game.",
)
def delete_achievement(
    achievement_id: int,
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    achievement = db.query(Achievement).join(Game).filter(
        Achievement.id == achievement_id, Game.user_id == current_user.id
    ).first()
    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")
    db.delete(achievement)
    db.commit()


# ── Stats endpoint ────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Get user collection statistics",
    description="Return aggregate statistics for the authenticated user's game collection: total playtime, achievements progress, top games, and average rating.",
)
def get_stats(
    current_user: User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db),
):
    games = db.query(Game).filter(Game.user_id == current_user.id).all()
    achievements = db.query(Achievement).join(Game).filter(Game.user_id == current_user.id).all()

    total_minutes = sum(g.play_time_minutes for g in games)
    total_achievements = len(achievements)
    earned_achievements = sum(1 for a in achievements if a.is_earned)

    top_games = (
        sorted(games, key=lambda g: g.play_time_minutes, reverse=True)[:3]
    )
    top_games_list = [
        TopGame(title=g.title, play_time_minutes=g.play_time_minutes, play_time_hours=minutes_to_hours(g.play_time_minutes))
        for g in top_games
    ]

    ratings = [g.rating for g in games if g.rating is not None]
    average_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    return {
        "total_play_time_minutes": total_minutes,
        "total_play_time_hours": minutes_to_hours(total_minutes),
        "total_achievements": total_achievements,
        "earned_achievements": earned_achievements,
        "top_games": top_games_list,
        "games_count": len(games),
        "average_rating": average_rating,
    }


# ── Search endpoint ───────────────────────────────────────────────

@router.get(
    "/search",
    summary="Search games via external API",
    description="Search for games using an external game database. Returns matching titles with metadata.",
)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
):
    results = search_games(q, limit=limit)
    return {"query": q, "results": results}
