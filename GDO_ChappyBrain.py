from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Result import ResultType
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Name import GDT_Name
from gdo.core.GDT_String import GDT_String
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_Deleted import GDT_Deleted


class GDO_ChappyBrain(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('cb_id'),
            GDT_Name('cb_key').unique().ascii().maxlen(32).not_null(),
            GDT_String('cb_value').maxlen(256).not_null(),
            GDT_Deleted('cb_deleted'),
            GDT_Created('cb_created'),
        ]

    @classmethod
    def get_content(cls) -> str:
        back = ''
        result = cls.table().select('cb_key, cb_value').where('cb_deleted IS NULL').exec().iter(ResultType.ROW)
        for row in result:
            back += f"{row[0]}: {row[1]}\n"
        return back
