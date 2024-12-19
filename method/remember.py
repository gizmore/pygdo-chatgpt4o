from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Util import html
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_UserType import GDT_UserType


class remember(Method):

    def gdo_trigger(self) -> str:
        return 'remember'

    def gdo_user_type(self) -> str | None:
        return GDT_UserType.CHAPPY

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Name('key').not_null(),
            GDT_RestOfText('value').not_null(),
        ]

    def gdo_execute(self) -> GDT:
        key = self.param_val('key')
        value = self.param_value('value')
        GDO_ChappyBrain.table().blank({
            'cb_key': key,
            'cb_value': value,
        }).insert()
        return self.reply('msg_remembered', [key, html(value)])
