from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_UserType import GDT_UserType


class forget(Method):

    def gdo_trigger(self) -> str:
        return 'forget'

    def gdo_user_type(self) -> str | None:
        return GDT_UserType.CHAPPY

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Name('key').not_null(),
        ]

    async def gdo_execute(self) -> GDT:
        key = self.param_val('key')
        GDO_ChappyBrain.table().delete_where(f'cb_key="{key}"')
        return self.reply('msg_gpt_forgot', [key])
