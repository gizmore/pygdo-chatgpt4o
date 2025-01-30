from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Util import html
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_String import GDT_String


class goal(Method):

    def gdo_trigger(self) -> str:
        return 'gpt.goal'

    def gdo_user_permission(self) -> str | None:
        return GDO_Permission.STAFF

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('goal').not_null(),
        ]

    @classmethod
    def gdo_method_config_user(cls) -> [GDT]:
        return [
            GDT_String('goal').initial('Be a kind and helpful - real - AI User!'),
        ]

    @classmethod
    def gdo_method_config_channel(cls) -> [GDT]:
        return [
            GDT_String('goal').initial('Be a kind and helpful - real - AI User!'),
        ]

    def cfg_goal(self) -> str:
        if self._env_channel:
            return self.get_config_channel_val('goal')
        else:
            return self.get_config_user_val('goal')

    def gdo_execute(self) -> GDT:
        the_goal = self.param_value('goal')
        if self._env_channel:
            self.save_config_channel('goal', the_goal)
        else:
            self.save_config_user('goal', the_goal)
        return self.reply('msg_goal_saved', (html(the_goal),))
