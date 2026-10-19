from fastapi import APIRouter
from portfolio_workers.chats.schema import (
    InMessagesHistory, 
    OutMessagesHistory
)
from portfolio_workers.database import DbSession

from portfolio_workers.chats.services import ChatService

router = APIRouter(prefix="/chats")

@router.post("/message_history")
async def create_chat_history(data: InMessagesHistory, db: DbSession) -> OutMessagesHistory:
    message_history = await ChatService(db).create_message_history(data)
    return OutMessagesHistory.model_validate(message_history)
    