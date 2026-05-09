from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_password_hash, verify_password
from app.config import get_settings
from app.deps import get_current_user, get_db
from app.enums import UserRole
from app.models import User
from app.schemas import AuthResponse, UserCreate, UserLogin, UserPublic


router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def set_auth_cookie(response: Response, user_id: int) -> None:
    token = create_access_token(str(user_id))
    response.set_cookie(
        key="access_token",
        value=token,
        path="/",
        httponly=True,
        samesite=settings.cookie_samesite,
        secure=settings.secure_cookies,
        domain=settings.cookie_domain,
        max_age=settings.access_token_expire_minutes * 60,
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, response: Response, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email already exists.")

    is_first_user = db.query(User).count() == 0
    requested_role = payload.role
    if is_first_user:
        if requested_role != UserRole.manager:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The first account must be created as a manager.",
            )
    elif requested_role == UserRole.manager:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager accounts must be created or promoted by an existing manager.",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        role=requested_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    set_auth_cookie(response, user.id)
    return {"user": UserPublic.model_validate(user)}


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
    if payload.expected_role is not None and user.role != payload.expected_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"This account is registered as a {user.role.value}.")

    set_auth_cookie(response, user.id)
    return {"user": UserPublic.model_validate(user)}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.cookie_domain,
        secure=settings.secure_cookies,
        samesite=settings.cookie_samesite,
    )


@router.get("/me", response_model=AuthResponse)
def me(current_user: User = Depends(get_current_user)):
    return {"user": UserPublic.model_validate(current_user)}
