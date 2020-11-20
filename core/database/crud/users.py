from core.database.models.users import User
from core.database.schemas import users as schemas
from core.database.crud import CRUDBase


class CRUDUser(CRUDBase[User, schemas.CreateUser, schemas.UpdateUser]):
    pass


user = CRUDUser(User)
