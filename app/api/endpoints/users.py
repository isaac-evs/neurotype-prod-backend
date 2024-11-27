from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm


from app import schemas
from app.api import deps
from app.core.security import create_access_token, verify_password
from app.core.s3 import upload_file_to_s3
from app.core.config import settings
from app.models.user import User
from app.services.user_service import create_user, get_user_by_email, update_user_plan, update_user_profile

router = APIRouter()

@router.post(
    "/register",
    response_model=schemas.User,
    summary="Register a new user",
    description="Create a new user account by providing a valid email and password."
)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate
):
    """
    Registers a new user in the system.

    - **email**: Unique email address of the user.
    - **password**: Password for the user account (will be hashed).
    """
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = create_user(db, user_in=user_in)
    return user


@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Login and get access token",
    description="Authenticate a user and generate an access token using their email and password."
)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Authenticates a user and returns a JWT access token.

    - **username**: User's email (used as the username).
    - **password**: User's password.
    """
    user = get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


### Ensure your backend’s /select-plan endpoint accepts a string ("lite" or "plus").
### If necessary, update the frontend to send the plan in the expected format (e.g., as a JSON object).
@router.put(
    "/select-plan",
    response_model=schemas.User,
    summary="Select a plan",
    description="Allows the user to select a plan: lite or plus."
)
def select_plan(
    *,
    db: Session = Depends(deps.get_db),
    plan_in: schemas.PlanType,
    current_user: User = Depends(deps.get_current_user)
):

    if plan_in not in schemas.PlanType:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    user = update_user_plan(db, user=current_user, plan=plan_in)
    return user

@router.put(
    "/profile",
    response_model=schemas.User,
    summary="Update user profile",
    description="Allows the user to update their name and upload a profile photo."
)
def update_profile(
    *,
    db: Session = Depends(deps.get_db),
    name: str = Form(None),
    file: UploadFile = File(None),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Updates the user's profile.

    - **name**: The user's name.
    - **file**: The profile photo to upload.
    """
    update_data = {}
    if name:
        update_data["name"] = name

    if file:
        # Upload the file to S3
        s3_url = upload_file_to_s3(file, settings.AWS_S3_BUCKET_NAME)
        update_data["profile_photo_url"] = s3_url

    if update_data:
        user = update_user_profile(db, user=current_user, update_data=update_data)
        return user
    else:
        raise HTTPException(status_code=400, detail="No data to update")
