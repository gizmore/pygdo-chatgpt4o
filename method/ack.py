from gdo.base.Method import Method


class ack(Method):

    def gdo_trigger(self) -> str:
        return 'ack'

    # def gdo_user_permission(self) -> str | None:
    #     from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
    #     return module_chatgpt4o.PERM_CHAPPY_BOT

    def gdo_execute(self):
        return self.empty()
