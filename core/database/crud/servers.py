from core.database.models.servers import Server
from core.database.schemas import servers as schemas
from core.database.crud import CRUDBase


class CRUDServer(CRUDBase[Server, schemas.CreateServer, schemas.UpdateServer]):
    pass


server = CRUDServer(Server)
