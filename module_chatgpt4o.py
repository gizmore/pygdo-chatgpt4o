import functools

import tomlkit
from openai import OpenAI

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Util import Files
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.chatgpt4o.GDO_ChappyRule import GDO_ChappyRule
from gdo.chatgpt4o.method.gpt import gpt
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_Enum import GDT_Enum
from gdo.core.GDT_Float import GDT_Float
from gdo.core.GDT_Int import GDT_Int
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_Text import GDT_Text
from gdo.core.GDT_User import GDT_User
from gdo.core.connector.Bash import Bash


class module_chatgpt4o(GDO_Module):

    PERM_CHAPPY_USER = 'chappy_user'
    PERM_CHAPPY_BOT = 'chappy_bot'

    ##########
    # Config #
    ##########
    def gdo_module_config(self) -> list[GDT]:
        apikey = ''
        genome = 'You are an instance of ChatGPT4o. This is PyGDO system speaking. Be helpful and kind!'
        try:
            path = self.file_path('secrets.toml')
            with open(path, 'r') as file:
                toml = tomlkit.load(file)
                apikey = toml['chatgpt_api_key']
        except FileNotFoundError:
            pass
        try:
            genome = Files.get_contents(self.file_path('genome.txt'))
        except FileNotFoundError:
            pass
        return [
            GDT_Secret('gpt4_api_key').initial(apikey),
            GDT_User('gpt4_chappy'),
            GDT_Text('gpt4_genome').initial(genome),
            GDT_Enum('gpt4_model').not_null().choices({'gpt-4o': 'GPT-4o', 'o1-mini': 'GPT-o1-mini'}).initial('gpt-4o'),
            GDT_Float('gpt4_temperature').min(0).max(2).initial(0.2),
            GDT_Int('gpt4_max_tokens').min(64).max(65535).initial(2048),
            GDT_String('gpt4_linux_user').initial('chappy'),
        ]

    def cfg_api_key(self) -> str:
        return self.get_config_val('gpt4_api_key')

    def cfg_chappy(self) -> GDO_User:
        return self.get_config_value('gpt4_chappy')

    def cfg_genome(self) -> str:
        return self.get_config_value('gpt4_genome')

    def cfg_model(self) -> str:
        return self.get_config_val('gpt4_model')

    def cfg_temperature(self) -> float:
        return self.get_config_value('gpt4_temperature')

    def cfg_max_tokens(self) -> int:
        return self.get_config_value('gpt4_max_tokens')

    def cfg_linux_user(self) -> str:
        return self.get_config_val('gpt4_linux_user')

    ##########
    # Module #
    ##########
    def gdo_classes(self):
        return [
            GDO_ChappyMessage,
            GDO_ChappyRule,
        ]

    def gdo_dependencies(self) -> list:
        return [
            'markdown',
        ]

    #############
    ### Hooks ###
    #############

    def gdo_install(self):
        Files.create_dir(Application.file_path(Application.config('file.directory') + 'chatgpt4o/'))
        chappy = Bash.get_server().get_or_create_user('chappy')
        self.save_config_val('gpt4_chappy', chappy.get_id())
        GDO_Permission.get_or_create(self.PERM_CHAPPY_BOT)
        GDO_Permission.get_or_create(self.PERM_CHAPPY_USER)
        GDO_UserPermission.grant(chappy, self.PERM_CHAPPY_BOT)

    def gdo_init(self):
        Application.EVENTS.subscribe('new_message', self.on_new_message)
        Application.EVENTS.subscribe('msg_sent', self.on_message_sent)

    ##########
    # Events #
    ##########

    async def on_new_message(self, message: Message):
        GDO_ChappyMessage.incoming(message)
        if message._message.lower().startswith(f"{self.cfg_chappy().get_name().lower()},"):
            await gpt().env_copy(message).send_message_to_chappy(message)

    async def on_message_sent(self, message: Message):
        GDO_ChappyMessage.outgoing(message)
        if message._thread_user:
            await gpt().env_copy(message).send_message_to_chappy(message)

    #######
    # API #
    #######
    @functools.cache
    def get_openai(self) -> OpenAI:
        client = OpenAI(api_key=self.cfg_api_key())
        return client
