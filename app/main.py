from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

app = FastAPI()

# --- Demo data ---
CLIENTS = {
    1: {"id": 1, "owner": "alice", "name": "Dupont", "iban": "FR76..."},
    2: {"id": 2, "owner": "bob",   "name": "Martin", "iban": "FR14..."},
    3: {"id": 3, "owner": "bob",   "name": "Durand", "iban": "FR22..."},
}
USERS = {
    "alice": {"id": 1, "name": "Alice", "internal_email": "alice@corp",
              "password_hash": "$2b$12$...", "is_admin": False},
    "bob":   {"id": 2, "name": "Bob", "internal_email": "bob@corp",
              "password_hash": "$2b$12$...", "is_admin": True},
}

# --- Identity: a real application would use JWTs signed by an identity provider ---
TOKENS = {"tok-alice": "alice", "tok-bob": "bob"}
bearer = HTTPBearer()

def get_current_user(request: Request,
                     creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    user = TOKENS.get(creds.credentials)
    if user is None:
        raise HTTPException(401, "invalid token")
    request.state.user = user
    return user

@app.middleware("http")
async def identity_for_logs(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-User"] = getattr(request.state, "user", "-")
    return response

@app.get("/clients/{client_id}")
def read_client(client_id: int, user: str = Depends(get_current_user)):
    client = CLIENTS.get(client_id)
    if not client:
        raise HTTPException(404, "unknown")
    
    if client["owner"] != user:                 # Act 2
        raise HTTPException(403, "forbidden")   # Act 2
    
    return client

# Simulate a model by calculating a text score
def calculate_text_score(text: str) -> float:
    return sum(ord(character) for character in text) / (len(text) + 1)

class PredictIn(BaseModel):
    text: str# = Field(max_length=512)

@app.post("/predict")
def predict(payload: PredictIn, user: str = Depends(get_current_user)):
    return {"score": calculate_text_score(payload.text)}

@app.get("/me")
def me(user: str = Depends(get_current_user)):
    return USERS[user]