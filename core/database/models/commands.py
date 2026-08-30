import uuid
from core.database.models import Base
from core.database.types import GUID
from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database.models.servers import Server


class Command(Base):
    __tablename__ = "commands"

    uuid: Mapped[str] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    server_uuid: Mapped[str] = mapped_column(GUID(), ForeignKey('servers.uuid'))
    status: Mapped[bool] = mapped_column(Boolean, default=True)

    server: Mapped[Server] = relationship(
        'Server', uselist=False
    )
