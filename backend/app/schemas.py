from pydantic import BaseModel, ConfigDict, EmailStr, Field

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=160)
    organization_name: str = Field(min_length=2, max_length=120)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    role: str
    organization_id: int

class AgentIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    system_prompt: str = Field(default="You are a helpful AI assistant.", max_length=12000)
    provider: str = Field(default="openai", pattern="^(openai|ollama)$")
    model: str = Field(default="", max_length=120)
    enabled: bool = True

class AgentOut(AgentIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int

class ChatIn(BaseModel):
    prompt: str = Field(min_length=1, max_length=20000)
    system_prompt: str = Field(default="You are a helpful AI assistant.", max_length=12000)
    provider: str = Field(default="openai", pattern="^(openai|ollama)$")
    model: str = Field(default="", max_length=120)

class ChatOut(BaseModel):
    response: str
    provider: str
    model: str
    conversation_id: int
