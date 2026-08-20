"""UserProfile CRUD + plan-generation routes."""
from fastapi import APIRouter, Depends, HTTPException, Response

from src.auth.dependencies import get_current_user, require_own_user
from src.auth.schemas import User
from src.core.planning import PlanRecommendation, generate_plan
from src.core.profiles import delete_profile, load_profile, save_profile
from src.core.schemas import UserProfile, WeightEntry
from src.core.weight_log import get_weight_log, save_weight

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/{user_id}", response_model=UserProfile)
def get_profile(user_id: str = Depends(require_own_user)) -> UserProfile:
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile for {user_id!r}")
    return profile


@router.post("", response_model=UserProfile, status_code=201)
def post_profile(profile: UserProfile, current_user: User = Depends(get_current_user)) -> UserProfile:
    # No {user_id} path param here -- the ownership check is against the
    # body's user_id instead (see src/auth/dependencies.py's docstring
    # for why every other route uses require_own_user as a dependency).
    if profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create a profile for another user")
    if load_profile(profile.user_id) is not None:
        raise HTTPException(
            status_code=409, detail=f"Profile for {profile.user_id!r} already exists"
        )
    save_profile(profile)
    return profile


@router.put("/{user_id}", response_model=UserProfile)
def put_profile(profile: UserProfile, user_id: str = Depends(require_own_user)) -> UserProfile:
    if profile.user_id != user_id:
        raise HTTPException(status_code=400, detail="user_id in body must match path")
    if load_profile(user_id) is None:
        raise HTTPException(status_code=404, detail=f"No profile for {user_id!r}")
    save_profile(profile)
    return profile


@router.delete("/{user_id}", status_code=204, response_class=Response)
def delete_profile_route(user_id: str = Depends(require_own_user)) -> None:
    try:
        delete_profile(user_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No profile for {user_id!r}")


@router.get("/{user_id}/plan", response_model=PlanRecommendation)
def get_plan(user_id: str = Depends(require_own_user)) -> PlanRecommendation:
    profile = load_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"No profile for {user_id!r}")
    return generate_plan(profile)


@router.get("/{user_id}/weight", response_model=dict[str, float])
def get_weight(user_id: str = Depends(require_own_user)) -> dict[str, float]:
    """Every weight this user has logged, keyed by date. Empty if
    they've never used the optional weight-logging feature."""
    return get_weight_log(user_id)


@router.post("/{user_id}/weight", response_model=WeightEntry, status_code=201)
def post_weight(entry: WeightEntry, user_id: str = Depends(require_own_user)) -> WeightEntry:
    if entry.user_id != user_id:
        raise HTTPException(status_code=400, detail="user_id in body must match path")
    return save_weight(entry)
