from graphene import relay, ObjectType, Schema, Field, String, Int, Boolean, List
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

    level = List(
        Level,
        uuid=String(),
        value=Int(),
        title=String(),
        exp=Int()
    )
    server = List(
        Server,
        uuid=String(),
        discord_id=String(),
        name=String(),
        server_exp=Int(),
        channel=String()
    )
    member = List(
        Member,
        uuid=String(),
        exp=Int(),
        player_uuid=String(),
        server_uuid=String(),
        level_uuid=String()
    )
    player = List(
        Player,
        uuid=String(),
        discord_id=String(),
        name=String(),
        hidden=Boolean()
    )

    def resolve_level(self, info, **kwargs):
        query = Level.get_query(info).filter_by(**kwargs)
        return query.all()

    def resolve_server(self, info, **kwargs):
        query = Server.get_query(info).filter_by(**kwargs)
        return query.all()

    def resolve_member(self, info, **kwargs):
        query = Member.get_query(info).filter_by(**kwargs)
        return query.all()

    def resolve_player(self, info, **kwargs):
        query = Player.get_query(info).filter_by(**kwargs)
        return query.all()


schema = Schema(query=Query)
