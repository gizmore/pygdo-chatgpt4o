import functools
import tomlkit

from typing import TYPE_CHECKING

from gdo.ui.GDT_Link import GDT_Link
from gdo.ui.GDT_Page import GDT_Page

if TYPE_CHECKING:
    from openai import OpenAI

from gdo.base.Application import Application
from gdo.base.GDO_Module import GDO_Module
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.base.Util import Files, href
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.chatgpt4o.GDO_ChappyBrain import GDO_ChappyBrain
from gdo.chatgpt4o.method.gpt import gpt
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDO_User import GDO_User
from gdo.core.GDO_UserPermission import GDO_UserPermission
from gdo.core.GDT_Int import GDT_Int
from gdo.core.GDT_Secret import GDT_Secret
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_Text import GDT_Text
from gdo.core.GDT_User import GDT_User
from gdo.core.GDT_UserType import GDT_UserType
from gdo.core.connector.Bash import Bash


class module_chatgpt4o(GDO_Module):

    PERM_CHAPPY_USER = 'chappy_user'
    PERM_CHAPPY_BOT = 'chappy_bot'

    def __init__(self):
        super().__init__()
        self._priority = 80

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
            # GDT_String('gpt4_model').not_null().initial('gpt-4o-mini'),  # gpt-4o
            # GDT_String('gpt4_model').not_null().initial('gpt-4o'),  # gpt-4o
            # GDT_String('gpt4_model').not_null().initial('ft:gpt-4o-2024-08-06:personal:chappy:Ae1HhgnK'),  # gpt-4o-ft
            GDT_String('gpt4_model').not_null().initial('ft:gpt-4o-2024-08-06:personal:source:Ae9lSf9i'),   # chappy + sourcecode 1 epoch

            GDT_Int('gpt4_max_tokens').min(32).max(8192).initial(512),
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
            GDO_ChappyBrain,
        ]

    def gdo_dependencies(self) -> list:
        return [
            'markdown',
        ]

    def gdo_init_sidebar(self, page: 'GDT_Page'):
        page._left_bar.add_field(GDT_Link().text('mt_chatgpt4o_chat').href(href('chatgpt4o', 'chat')))

    #############
    ### Hooks ###
    #############

    def gdo_install(self):
        Files.create_dir(Application.file_path(Application.config('file.directory') + 'chatgpt4o/'))
        chappy = Bash.get_server().get_or_create_user('chappy')
        chappy.save_val('user_type', GDT_UserType.CHAPPY)
        self.save_config_val('gpt4_chappy', chappy.get_id())
        GDO_Permission.get_or_create(self.PERM_CHAPPY_BOT)
        GDO_Permission.get_or_create(self.PERM_CHAPPY_USER)
        GDO_UserPermission.grant(chappy, self.PERM_CHAPPY_BOT)

    def gdo_subscribe_events(self):
        Application.EVENTS.subscribe('new_message', self.on_new_message)
        Application.EVENTS.subscribe('msg_sent', self.on_message_sent)
        Application.EVENTS.subscribe('user_list', self.on_got_users)
        Application.EVENTS.subscribe('user_joined_channel', self.on_user_joined_channel)
        Application.EVENTS.subscribe('user_joined_server', self.on_user_joined_server)
        # Application.EVENTS.add_timer(Time.ONE_MINUTE*20, self.on_chappy_timer, 1000000000)

    ##########
    # Events #
    ##########
    def gpt_enabled(self, message: Message) -> bool:
        if message._env_channel:
            return not gpt().env_copy(message).get_config_channel_value('disabled')
        else:
            return not gpt().env_copy(message).get_config_server_value('disabled')

    async def on_new_message(self, message: Message):
        if message._message and self.gpt_enabled(message):
            GDO_ChappyMessage.incoming(message)
            dog = self.cfg_chappy().get_displayname().lower()
            chappy = message._env_server.get_connector().gdo_get_dog_user().get_name().lower()
            text = message._message.lower().rstrip("!?,.{0123456789}\x00\x01\x02\x03").lstrip('$@!.?,')
            if text.startswith(chappy) or text.startswith('chap') or text.endswith(chappy) or text.startswith(dog) or text.endswith(dog):
                if not gpt.PROCESSING:
                    gpt.PROCESSING = True
                    try:
                        await gpt().env_copy(message).send_message_to_chappy(message)
                    except Exception as ex:
                        gpt.PROCESSING = False
                        raise ex

    async def on_message_sent(self, message: Message):
        if message._message and self.gpt_enabled(message):
            GDO_ChappyMessage.outgoing(message)
            if message._thread_user and not gpt.PROCESSING:
                gpt.PROCESSING = True
                try:
                    await gpt().env_copy(message).send_message_to_chappy(message)
                except Exception as ex:
                    gpt.PROCESSING = False
                    raise ex

    async def on_got_users(self, channel: GDO_Channel, users: list[GDO_User]):
        GDO_ChappyMessage.users_joined(channel, users)

    async def on_chappy_timer(self):
        channel = GDO_ChappyMessage.table().select('DISTINCT(cm_channel_t.chan_id), cm_channel_t.*').join_object('cm_channel').join_object('cm_sender').fetch_as(GDO_Channel.table()).where('cm_sender_t.user_type="chappy"').order('RAND()').first().exec().fetch_object()
        if channel.get_server().get_connector().is_connected():
            if not gpt.PROCESSING:
                gpt.PROCESSING = True
                try:
                    return await gpt().send_wakeup_to_chappy(channel)
                except Exception as ex:
                    gpt.PROCESSING = False
                    raise ex

    async def on_user_joined_channel(self, user: GDO_User, channel: GDO_Channel):
        GDO_ChappyMessage.users_joined(channel, [user])

    async def on_user_joined_server(self, user: GDO_User):
        GDO_ChappyMessage.users_joined(None, [user])

    #######
    # API #
    #######
    @functools.cache
    def get_openai(self) -> 'OpenAI':
        from openai import OpenAI
        client = OpenAI(api_key=self.cfg_api_key())
        return client
