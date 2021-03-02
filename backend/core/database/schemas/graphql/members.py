from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType
from core.database.models.members import Member as MemberModel


class Member(SQLAlchemyObjectType):
    class Meta:
        model = MemberModel
        interfaces = (relay.Node,)
