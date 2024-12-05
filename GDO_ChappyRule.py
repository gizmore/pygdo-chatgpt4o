from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_String import GDT_String


class GDO_ChappyRule(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('cg_id'),
            GDT_String('cg_rule'),
        ]

