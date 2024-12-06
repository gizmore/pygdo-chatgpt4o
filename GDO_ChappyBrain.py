from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_String import GDT_String
from gdo.date.GDT_Created import GDT_Created


class GDO_ChappyBrain(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('cb_id'),
            GDT_Name('cb_key').unique().ascii().maxlen(32).not_null(),
            GDT_String('cb_value').maxlen(256).not_null(),
            GDT_Created('cb_created'),
        ]

