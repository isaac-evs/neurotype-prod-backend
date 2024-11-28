from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import logging
import secrets

from app import schemas
from app.api import deps
from app.core.security import create_access_token, verify_password
from app.core.s3 import upload_file_to_s3
from app.core.config import settings
from app.models.user import User
from app.services.user_service import create_user, get_user_by_email, update_user_plan, update_user_profile

logger = logging.getLogger(__name__)

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


# users.py

@router.post(
    "/login",
    response_model=schemas.Token,
    summary="Login and get access token",
    description="Authenticate a user and generate an access token using their email and password."
)
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    user = get_user_by_email(db, email=form_data.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # If the user was created via Google, they shouldn't use password login
    if user.hashed_password == form_data.password:
        raise HTTPException(status_code=400, detail="Use Google Sign-In to authenticate")

    if not verify_password(form_data.password, user.hashed_password):
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

class GoogleAuth(BaseModel):
    id_token: str

@router.post(
    "/auth/google",
    response_model=schemas.Token,
    summary="Authenticate with Google",
    description="Authenticate a user using Google Sign-In and return a JWT token."
)
def authenticate_google(
    *,
    db: Session = Depends(deps.get_db),
    google_auth: GoogleAuth
):
    logger.info("Received Google authentication request.")
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            google_auth.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        logger.info("Google ID token verified successfully.")

        # Extract user information
        email = idinfo['email']
        name = idinfo.get('name', '')
        logger.debug(f"Google Email: {email}, Name: {name}")

        # Validate token claims (optional)
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            logger.error("Invalid issuer in Google ID token.")
            raise HTTPException(status_code=400, detail="Invalid issuer in ID token")

    except ValueError as e:
        logger.error(f"Invalid Google ID token: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google ID token")
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Check if user exists
    user = get_user_by_email(db, email=email)
    if user:
        logger.info(f"User with email {email} already exists.")
        is_new_user = False
    else:
        logger.info(f"Creating new user with email {email}.")
        # Generate a secure random password
        random_password = secrets.token_urlsafe(16)
        user_in = schemas.UserCreate(
            email=email,
            password=random_password,
            name=name
        )
        try:
            user = create_user(db, user_in=user_in)
            db.commit()
            db.refresh(user)
            logger.info(f"User {user.id} created successfully.")
            is_new_user = True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail="Error creating user")

    # Generate JWT token
    try:
        access_token = create_access_token(subject=str(user.id))
        logger.info(f"Access token created for user {user.id}.")
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise HTTPException(status_code=500, detail="Error generating access token")

    return {"access_token": access_token, "token_type": "bearer", "is_new_user": is_new_user}


@router.get(
    "/users/me",
    response_model=schemas.User,
    summary="Get current user",
    description="Retrieve the current authenticated user's information."
)
def read_users_me(current_user: User = Depends(deps.get_current_user)):
    """
    Retrieves the current authenticated user's information.

    - **current_user**: Retrieved via dependency injection from the JWT token.
    """
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    return current_user
