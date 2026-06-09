"""Single-operator HTTP basic auth (v1). Multi-user roles are a future phase."""
import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from core.config import settings

_security = HTTPBasic()


def require_operator(credentials: HTTPBasicCredentials = Depends(_security)) -> str:
    user_ok = secrets.compare_digest(credentials.username.encode(), settings.dashboard_user.encode())
    pass_ok = secrets.compare_digest(credentials.password.encode(), settings.dashboard_pass.encode())
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
