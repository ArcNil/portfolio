from pydantic import BaseModel, Field, ConfigDict
from typing import List

class InMessages(BaseModel):
    message_text: str =  Field(min_length=5, max_length=512)
    message_history_id: int

class OutMessages(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    message_text: str
    message_history_id: int



class InMessagesHistory(BaseModel):
    title: str =  Field(min_length=5, max_length=25)

class OutMessagesHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    messages: List[OutMessages] | None