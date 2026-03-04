from pydantic import BaseModel, Field
from typing import Optional

# ====== Topics ======
class TopicCreate(BaseModel):
    title: str = Field(..., max_length=128)
    theory_text: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True

class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=128)
    theory_text: Optional[str] = None
    image_url: Optional[str] = None

class TopicResponse(BaseModel):
    id: int
    title: str
    theory_text: Optional[str]
    image_url: Optional[str]
    is_active: bool
    questions_count: int

    class Config:
        from_attributes = True

# ====== Questions ======
class QuestionCreate(BaseModel):
    topic_id: int
    text: str
    option_a: str = Field(..., max_length=256)
    option_b: str = Field(..., max_length=256)
    option_c: str = Field(..., max_length=256)
    option_d: str = Field(..., max_length=256)
    correct_option: str = Field(..., max_length=1, pattern="^[a-d]$")
    difficulty: int = Field(1, ge=1, le=3)
    explanation: Optional[str] = None
    image_url: Optional[str] = None

class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    option_a: Optional[str] = Field(None, max_length=256)
    option_b: Optional[str] = Field(None, max_length=256)
    option_c: Optional[str] = Field(None, max_length=256)
    option_d: Optional[str] = Field(None, max_length=256)
    correct_option: Optional[str] = Field(None, max_length=1, pattern="^[a-d]$")
    difficulty: Optional[int] = Field(None, ge=1, le=3)
    explanation: Optional[str] = None
    image_url: Optional[str] = None

class QuestionResponse(BaseModel):
    id: int
    topic_id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    difficulty: int
    explanation: Optional[str]
    image_url: Optional[str]

    class Config:
        from_attributes = True

# ====== Users ======
class UserResponse(BaseModel):
    id: int
    username: Optional[str]
    first_name: str
    xp: int
    level: str
    streak_days: int
    accuracy_rate: float
    is_banned: bool
    created_at: str

class UserSendMessage(BaseModel):
    text: str

# ====== Broadcast ======
class BroadcastRequest(BaseModel):
    text: str

class BroadcastResponse(BaseModel):
    status: str
    sent: int
    failed: int
    total: int

# ====== Attachments ======
class AttachmentResponse(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    attachment_type: str
    file_name: str
    file_size: int
    mime_type: str
    url: str
    created_at: str

    class Config:
        from_attributes = True
