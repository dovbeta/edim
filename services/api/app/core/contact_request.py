from pydantic import BaseModel, ConfigDict
from typing import Optional


class ContactRequest(BaseModel):
    channel: str
    external_user_id: str
    phone: str

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None

    model_config = ConfigDict(extra="ignore")