from gdo.base.GDT import GDT
from gdo.form.GDT_Form import GDT_Form
from gdo.form.MethodForm import MethodForm
from gdo.message.GDT_Message import GDT_Message


class chat(MethodForm):

    def gdo_trigger(self) -> str:
        return ''

    def gdo_create_form(self, form: GDT_Form) -> None:
        form.add_field()
        super().gdo_create_form(form)

    def gdo_create_form_parameters(self) -> [GDT]:
        return [
            GDT_Message('text').not_null()
        ]