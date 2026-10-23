import jwt
import logging
from fastapi import FastAPI, Request, HTTPException
from jwt.exceptions import InvalidTokenError
from app.core.config import ( JWT_PUBLIC_KEY, JWT_ISSUER, JWT_AUDIENCE )

logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    pass


def verify_access_token(token: str, *, public_key: str, issuer: str, audience: str, algorithm: str = "RS256") -> dict:
        try:
            claims = jwt.decode(
                token,
                key=public_key,
                algorithms=[algorithm],
                issuer=issuer,
                audience=audience,
                options={
                    "require" : ["exp", "iss", "aud", "sub"],
                },    
            )
        except InvalidTokenError as exc:
            raise AuthenticationError(str(exc)) from exc
            
        subject = claims.get("sub")

        if not isinstance(subject, str) or not subject.strip():
            raise AuthenticationError("Invalid access token subject")
        
        return claims



def authenticated_user(request: Request) -> str:
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException( status_code=401, detail="Authentication required.")
    
    if not JWT_PUBLIC_KEY or not JWT_ISSUER or not JWT_AUDIENCE:
        logger.error("JWT config missing")
        raise HTTPException( status_code=500, detail="Server configuration error.")
    
    try:
        claims = verify_access_token( token, public_key=JWT_PUBLIC_KEY, issuer=JWT_ISSUER, audience=JWT_AUDIENCE)

    except AuthenticationError as exc:
        logger.warning("Authentication error: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid access token.") from exc
    
    authenticated_user_id = claims.get("sub")

    if not authenticated_user_id:
        raise HTTPException( status_code=401, detail="Invalid acccess token.")
    
    return authenticated_user_id






