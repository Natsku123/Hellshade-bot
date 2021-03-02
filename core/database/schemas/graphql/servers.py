from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from core.database.models.servers import Server as ServerModel


class Server(SQLAlchemyObjectType):
    class Meta:
        model = ServerModel
        interfaces = (relay.Node,)
