import functools

import tomlkit
from openai import OpenAI

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Util import Files
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_User import GDT_User
from gdo.core.connector.Bash import Bash


class module_chatgpt4o(GDO_Module):

    PERM_CHAPPY_USER = 'chappy_user'
    PERM_CHAPPY_BOT = 'chappy_bot'

    def __init__(self):
        super().__init__()

    ##########
    # Config #
    ##########
    def gdo_module_config(self) -> list[GDT]:
        apikey = ''
        try:
            path = self.file_path('secrets.toml')
            with open(path, 'r') as file:
                toml = tomlkit.load(file)
                apikey = toml['chatgpt_api_key']
        except FileNotFoundError:
            pass
        return [
            GDT_Secret('chatgpt4o_api_key').initial(apikey),
            GDT_User('chatgpt4o_chappy'),
        ]

    def cfg_api_key(self) -> str:
        return self.get_config_val('chatgpt_api_key')

    def cfg_chappy(self) -> GDO_User:
        return self.get_config_value('chatgpt4o_chappy')

    #############
    ### Hooks ###
    #############

    def gdo_install(self):
        Files.create_dir(Application.file_path(Application.config('file.directory') + 'chatgpt4o/'))
        chappy = Bash.get_server().get_or_create_user('chappy')
        self.save_config_val('chatgpt_chappy', chappy.get_id())
        GDO_Permission.get_or_create(self.PERM_CHAPPY_BOT)
        GDO_Permission.get_or_create(self.PERM_CHAPPY_USER)
        GDO_UserPermission.grant(chappy, self.PERM_CHAPPY_BOT)

    def gdo_init(self):
        Application.EVENTS.subscribe('new_message', self.on_new_message)
        Application.EVENTS.subscribe('msg_sent', self.on_message_sent)

    ##########
    # Events #
    ##########

    def on_new_message(self, message: Message):
        if not message._env_user.get_setting_value('chappy_no'):
            genome = GDO_ChatGenome.for_message(message)
            if genome:
                ChappyEventListener().env_copy(message).on_new_message(genome, message)

    def on_message_sent(self, message: Message):
        if not message._env_user.get_setting_value('chappy_no'):
            genome = GDO_ChatGenome.for_message(message)
            if genome:
                if message._result.lower().startswith('chappy:'):
                    message._message = message._result
                    ChappyEventListener().env_copy(message).on_new_message(genome, message)
                else:
                    chappy = genome.get_chappy()
                    ChappyEventListener().env_copy(message).on_message_sent(genome, message, chappy)

    #######
    # API #
    #######
    @functools.cache
    def get_openai(self) -> OpenAI:
        client = OpenAI(api_key=self.cfg_api_key())
        return client
