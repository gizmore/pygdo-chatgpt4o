from gdo.base.GDT import GDT
from gdo.form.GDT_Form import GDT_Form
from gdo.form.MethodForm import MethodForm
from gdo.message.GDT_Message import GDT_Message


class chat(MethodForm):

    @classmethod
    def gdo_trigger(cls) -> str:
        return ''

    def gdo_create_form(self, form: GDT_Form) -> None:
        form.add_field(GDT_Message('text').not_null())
        super().gdo_create_form(form)

    def form_submitted(self):
        pass
