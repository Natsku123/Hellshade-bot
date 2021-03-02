from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from core.database.models.players import Player as PlayerModel


class Player(SQLAlchemyObjectType):
    class Meta:
        model = PlayerModel
        interfaces = (relay.Node,)
