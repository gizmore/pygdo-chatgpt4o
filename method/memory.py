from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Util import html
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_Name import GDT_Name


class memory(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'memory'

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_Bool('all').initial('0'),
            GDT_Bool('deleted').initial('0'),
            GDT_Name('key').positional(),
        ]

    def get_key(self) -> str:
        return self.param_value('key')

    def gdo_execute(self) -> GDT:
        if self.param_value('all'):
            return self.show_all_memory()
        elif key := self.get_key():
            return self.show_single_memory(key)
        else:
            return self.show_all_memory_keys()

    def show_all_memory(self) -> GDT:
        out = []
        query = GDO_ChappyBrain.table().select()
        if not self.param_value('deleted'):
            query.where('cb_deleted IS NULL')
        memories = query.exec()
        for memory in memories:
            out.append(f"{memory.get_mem_key()}: {html(memory.get_mem_value())}")
        return self.reply('msg_gpt_full_memory', ("\n".join(out),))

    def show_single_memory(self, key: str) -> GDT:
        value = GDO_ChappyBrain.table().get_by('cb_key', key).gdo_value('cb_value')
        return self.reply('msg_gpt_memory_key', (key, html(value)))

    def show_all_memory_keys(self) -> GDT:
        out = []
        memories = GDO_ChappyBrain.table().select('cb_key').exec().fetch_column()
        for memory in memories:
            out.append(memory)
        return self.reply('msg_gpt_memory_keys', (", ".join(out),))
