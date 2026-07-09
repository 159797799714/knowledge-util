import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from config.jwt_config import jwt_config


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=jwt_config.expire_minutes)
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, jwt_config.secret_key, algorithm=jwt_config.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(request: Request) -> Dict[str, Any]:
    token = None
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
    
    if not token:
        token = request.query_params.get("token")
    
    if not token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = verify_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials")
    
    return payload