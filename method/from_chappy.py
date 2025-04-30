from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.core.GDT_RestOfText import GDT_RestOfText


class from_chappy(Method):
    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('message').not_null(),
        ]

    def gdo_execute(self) -> GDT:
        pass
