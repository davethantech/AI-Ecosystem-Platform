import re
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from .config import settings
from .db import Base, engine, get_db
from .models import Organization, User, Agent, AuditEvent, Conversation
from .schemas import RegisterIn, LoginIn, UserOut, AgentIn, AgentOut, ChatIn, ChatOut
from .security import hash_password, verify_password, create_access_token, decode_access_token
from .ai import generate

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="AI Ecosystem Platform API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",") if x.strip()], allow_credentials=False, allow_methods=["GET","POST","PUT","DELETE"], allow_headers=["Authorization","Content-Type"])
security = HTTPBearer(auto_error=False)

@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api/auth") else "no-cache"
    return response

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub", ""))
        org_id = int(payload.get("org", 0))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token claims") from exc
    user = db.scalar(select(User).where(User.id == user_id, User.organization_id == org_id, User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def audit(db: Session, user: User, action: str, details: dict | None = None):
    db.add(AuditEvent(organization_id=user.organization_id, user_id=user.id, action=action, details=details or {}))

def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:120]
    return value or "workspace"

@app.get("/api/health")
def health():
    return {"status":"ok","service":"ai-ecosystem-api","version":"0.1.0"}

@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    base_slug = slugify(payload.organization_name)
    slug = base_slug
    suffix = 2
    while db.scalar(select(Organization.id).where(Organization.slug == slug)):
        slug = f"{base_slug[:130]}-{suffix}"
        suffix += 1
    org = Organization(name=payload.organization_name.strip(), slug=slug)
    db.add(org); db.flush()
    user = User(email=email, password_hash=hash_password(payload.password), full_name=payload.full_name.strip(), role="owner", organization_id=org.id)
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token(str(user.id), user.organization_id)
    return {"access_token":token,"token_type":"bearer","user":UserOut.model_validate(user)}

@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = str(payload.email).lower()
    user = db.scalar(select(User).where(User.email == email, User.is_active.is_(True)))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id), user.organization_id)
    audit(db, user, "auth.login")
    db.commit()
    return {"access_token":token,"token_type":"bearer","user":UserOut.model_validate(user)}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user

@app.get("/api/organization")
def organization(user: User = Depends(current_user), db: Session = Depends(get_db)):
    org = db.get(Organization, user.organization_id)
    return {"id":org.id,"name":org.name,"slug":org.slug,"created_at":org.created_at}

@app.get("/api/dashboard")
def dashboard(user: User = Depends(current_user), db: Session = Depends(get_db)):
    org = user.organization_id
    return {"agents":db.scalar(select(func.count()).select_from(Agent).where(Agent.organization_id == org)) or 0,
            "conversations":db.scalar(select(func.count()).select_from(Conversation).where(Conversation.organization_id == org)) or 0,
            "audit_events":db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.organization_id == org)) or 0,
            "provider_status":{"openai_configured":bool(settings.openai_api_key),"ollama_configured":bool(settings.ollama_base_url)}}

@app.get("/api/agents", response_model=list[AgentOut])
def list_agents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return list(db.scalars(select(Agent).where(Agent.organization_id == user.organization_id).order_by(Agent.id.desc())).all())

@app.post("/api/agents", response_model=AgentOut, status_code=201)
def create_agent(payload: AgentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    agent = Agent(organization_id=user.organization_id, **payload.model_dump())
    db.add(agent); db.flush(); audit(db, user, "agent.created", {"agent_id":agent.id}); db.commit(); db.refresh(agent)
    return agent

@app.put("/api/agents/{agent_id}", response_model=AgentOut)
def update_agent(agent_id: int, payload: AgentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    agent = db.scalar(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id))
    if not agent: raise HTTPException(status_code=404, detail="Agent not found")
    for key, value in payload.model_dump().items(): setattr(agent, key, value)
    audit(db, user, "agent.updated", {"agent_id":agent.id}); db.commit(); db.refresh(agent); return agent

@app.delete("/api/agents/{agent_id}", status_code=204)
def delete_agent(agent_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    agent = db.scalar(select(Agent).where(Agent.id == agent_id, Agent.organization_id == user.organization_id))
    if not agent: raise HTTPException(status_code=404, detail="Agent not found")
    audit(db, user, "agent.deleted", {"agent_id":agent.id}); db.delete(agent); db.commit()

@app.post("/api/chat", response_model=ChatOut)
async def chat(payload: ChatIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    response, chosen_model = await generate(payload.provider, payload.model, payload.system_prompt, payload.prompt)
    row = Conversation(organization_id=user.organization_id, user_id=user.id, provider=payload.provider, model=chosen_model, prompt=payload.prompt, response=response)
    db.add(row); db.flush(); audit(db, user, "chat.completed", {"provider":payload.provider,"model":chosen_model,"conversation_id":row.id}); db.commit()
    return ChatOut(response=response, provider=payload.provider, model=chosen_model, conversation_id=row.id)

@app.get("/api/conversations")
def conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Conversation).where(Conversation.organization_id == user.organization_id, Conversation.user_id == user.id).order_by(Conversation.created_at.desc()).limit(50)).all()
    return [{"id":r.id,"provider":r.provider,"model":r.model,"prompt":r.prompt,"response":r.response,"created_at":r.created_at} for r in rows]

@app.get("/api/audit")
def audit_log(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(AuditEvent).where(AuditEvent.organization_id == user.organization_id).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [{"id":r.id,"user_id":r.user_id,"action":r.action,"details":r.details,"created_at":r.created_at} for r in rows]
