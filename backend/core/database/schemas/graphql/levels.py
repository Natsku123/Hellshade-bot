from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from core.database.models.levels import Level as LevelModel


class Level(SQLAlchemyObjectType):
    class Meta:
        model = LevelModel
        interfaces = (relay.Node,)
