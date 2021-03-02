from graphene import relay, ObjectType, Schema
from graphene_sqlalchemy import SQLAlchemyConnectionField
from core.database.schemas.graphql.levels import Level
from core.database.schemas.graphql.servers import Server
from core.database.schemas.graphql.members import Member
from core.database.schemas.graphql.players import Player


class Query(ObjectType):
    node = relay.Node.Field()
    all_levels = SQLAlchemyConnectionField(Level.connection)
    all_servers = SQLAlchemyConnectionField(Server.connection)
    all_members = SQLAlchemyConnectionField(Member.connection)
    all_players = SQLAlchemyConnectionField(Player.connection)


schema = Schema(query=Query)
