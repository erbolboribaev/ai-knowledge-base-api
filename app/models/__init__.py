# Bu fayl barcha modellarni bir joyga to'playdi.
# Alembic autogenerate va boshqa joylar shu paket import qilinganda
# barcha modellar Base.metadata'ga ro'yxatdan o'tishini kafolatlaydi.
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.models.chunk import Chunk

__all__ = ["User", "Document", "DocumentStatus", "Chunk"]
