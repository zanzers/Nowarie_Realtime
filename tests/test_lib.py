import jwt
from app.main import app
from pathlib import Path
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def create_test_token():
    private_key = ( PROJECT_ROOT / "app" / "lib" / "test_private.pem").read_text(encoding="utf-8")
    now = datetime.now(timezone.utc)

    return jwt.encode(
        {
            "sub" : "user-123",
            "iss" : "nowarie-test",
            "aud" : "nowarie-realtime",
            "iat" : now,
            "exp" : now + timedelta(minutes=15)
        },
        private_key,
        algorithm="RS256",
    )

def create_authenticated_client():
    client = TestClient(app)
    token = create_test_token()
    client.cookies.set("access_token", token)
    return client

def create_unauthenticated_client():
    return TestClient(app)

def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")

    
    assert response.status_code == 200
    assert response.json() == {
        "status":"Healthy",
        "service": "nowarie-realtime",
        "version":"0.1.0" 
    }
