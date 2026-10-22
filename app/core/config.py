import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def load_public_key() -> str:
    key_path_value = os.getenv( "JWT_PUBLIC_KEY_PATH", "app/lib/test_public.pem",)
    key_path = Path(key_path_value)

    if not key_path.is_absolute():
        key_path = PROJECT_ROOT / key_path
        
    if not key_path.is_file():
        raise RuntimeError(f"JWT public key file not found: {key_path}")

    return key_path.read_text(encoding="utf-8")



JWT_PUBLIC_KEY = load_public_key()
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")


def validate_jwt_config() -> None:
    missing = [
        name  for name, value in {
            "JWT_PUBLIC_KEY": JWT_PUBLIC_KEY,
            "JWT_ISSUER": JWT_ISSUER,
            "JWT_AUDIENCE": JWT_AUDIENCE
        }.items()
        if not value
    ]

    if missing:
        raise ValueError(f"Missing JWT configuration: {', '.join(missing)}")