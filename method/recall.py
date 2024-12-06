from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Util import Arrays, html
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.core.GDT_Name import GDT_Name


class recall(Method):

    def gdo_trigger(self) -> str:
        return 'recall'

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_Name('key').positional(),
        ]

    def gdo_execute(self):
        if key := self.param_val('key'):
            return self.memories(key)
        return self.keys()

    def keys(self) -> GDT:
        keys = GDO_ChappyBrain.table().select('cb_key').exec().fetch_column()
        return self.reply('msg_memory_keys', [Arrays.human_join(keys)])

    def memories(self, key: str) -> GDT:
        memories = GDO_ChappyBrain.table().select().where(f"cb_key LIKE '%{GDO.escape(key)}%'").exec().fetch_all()
        aggregated = []
        for memory in memories:
            aggregated.append(f"{memory.gdo_val('cb_key')}: {html(memory.gdo_val('value'))}")
        return self.reply('msg_memories', ["\n".join(memories)])
