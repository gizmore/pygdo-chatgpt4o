from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_UserType import GDT_UserType


class ack(Method):

    def gdo_trigger(self) -> str:
        return 'ack'

    def gdo_user_type(self) -> str | None:
        return GDT_UserType.CHAPPY

    async def gdo_execute(self) -> GDT:
        return self.empty()
