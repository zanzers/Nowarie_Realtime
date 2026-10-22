import jwt
from jwt.exceptions import InvalidTokenError

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