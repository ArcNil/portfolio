
from sqlalchemy.ext.asyncio import AsyncSession

from portfolio_workers.chats.models import MessageHistories
from portfolio_workers.chats.schema import InMessagesHistory

import logging
logger = logging.getLogger(__name__)



class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message_history(self, data: InMessagesHistory) -> MessageHistories:
        message_history = MessageHistories(title=data.title, messages=[])
        self.db.add(message_history)
        await self.db.commit()
        # await self.db.refresh(message_history)
        logger.info("Create Message history id=%s", message_history.id)

        return message_history