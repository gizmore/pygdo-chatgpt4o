from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_RestOfText import GDT_RestOfText


class remember(Method):

    def gdo_trigger(self) -> str:
        return 'remember'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Name('key').not_null(),
            GDT_RestOfText('value').not_null(),
        ]

    def gdo_execute(self):
        GDO_ChappyBrain.table().blank({
            'cb_key': self.param_val('key'),
            'cb_value': self.param_value('value'),
        }).insert()
        return self.reply('msg_remembered')
