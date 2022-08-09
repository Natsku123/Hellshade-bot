from core.database.models.players import Player
from core.database.schemas import players as schemas
from core.database.crud import CRUDBase


class CRUDPlayer(CRUDBase[Player, schemas.CreatePlayer, schemas.UpdatePlayer]):
    pass


player: CRUDPlayer = CRUDPlayer(Player)
