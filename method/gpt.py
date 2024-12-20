import asyncio
import re

from openai import InternalServerError, RateLimitError

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.base.Render import Mode
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_Float import GDT_Float
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.core.GDT_UInt import GDT_UInt
from gdo.markdown.MDConvert import MDConvert


class gpt(Method):


    PROCESSING: bool = False
    # LAST_RESPONSE: str = ""

    def gdo_trigger(self) -> str:
        return 'gpt'

    def gdo_default_enabled(self) -> bool:
        return False

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('message').not_null(),
        ]

    def gdo_method_config_user(self) -> [GDT]:
        return [
            GDT_Float('temperature').min(0).max(0.5).initial("0.1"),
            GDT_Float('window_size').min(0).max(50).initial("25"),
        ]

    def gdo_method_config_channel(self) -> [GDT]:
        return [
            GDT_Float('temperature').min(0).max(0.8).initial("0.1"),
            GDT_UInt('window_size').min(0).max(100).initial("50"),
        ]

    async def cfg_temperature(self, message: Message) -> float:
        if message._env_channel:
            return await self.get_config_channel_value('temperature')
        else:
            return await self.get_config_user_value('temperature')

    async def cfg_window_size(self, message: Message) -> int:
        if message._env_channel:
            return await self.get_config_channel_value('window_size')
        else:
            return await self.get_config_user_value('window_size')

    async def gdo_execute(self) -> GDT:
        text = await self.param_value('message')
        msg = Message(text, self._env_mode).env_copy(self)
        await GDO_ChappyMessage.incoming(msg)
        if self._env_channel:
            return await self.send_channel_to_chappy(msg)
        else:
            return await self.send_user_to_chappy(msg)

    async def send_message_to_chappy(self, message: Message):
        if message._env_channel:
            return await self.send_channel_to_chappy(message)
        else:
            return await self.send_user_to_chappy(message)

    async def send_channel_to_chappy(self, message: Message):
        messages = GDO_ChappyMessage.get_messages_for_channel(message)
        return await self.send_to_chappy(message, messages)

    async def send_user_to_chappy(self, message: Message):
        messages = GDO_ChappyMessage.get_messages_for_user(message)
        return await self.send_to_chappy(message, messages)

    async def send_wakeup_to_chappy(self, channel: GDO_Channel):
        system = GDO_User.system()
        msg = Message(f"", Mode.TXT).env_user(system).env_channel(channel).env_server(channel.get_server())
        self.env_copy(msg)
        GDO_ChappyMessage.blank({
            'cm_sender': system.get_id(),
            'cm_channel': channel.get_id(),
            'cm_message': 'chappy: WakeUp call! Do not answer with $ack, but look back into the history to answer a question or improve the conversation. Maybe remember something important. If you have nothing to say, say you are bored.',
        }).insert()
        return await self.send_channel_to_chappy(msg)

    async def send_to_chappy(self, message: Message, messages: list):
        try:
            from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
            mod = module_chatgpt4o.instance()
            api = mod.get_openai()
            response = api.chat.completions.create(
                model=mod.cfg_model(),
                messages=messages,
                temperature=self.cfg_temperature(message),
                max_tokens=mod.cfg_max_tokens(),
            )
            self.__class__.PROCESSING = False
            text = response.choices[0].message.content
            text = self.trim_chappies_bad_response(text)
            comrade = message._thread_user if message._thread_user else message._env_user
            message.comrade(comrade)
            chappy_msg = self.generate_chappy_response(text, message)
            text = MDConvert(text).to(message._env_mode)
            message.result(text)
            await message.deliver(False, False)
            await asyncio.sleep(0.3141)
            Application.MESSAGES.put(chappy_msg)
        except RateLimitError as ex:
            message.result("Not enough money!")
            await message.deliver(False, False)
        except InternalServerError as ex:
            raise ex
        except Exception as ex:
            Logger.exception(ex)
        return self.empty()

    def generate_chappy_response(self, text: str, msg: Message) -> Message:
        chappy = msg._env_server.get_connector().gdo_get_dog_user()
        new = msg.message_copy().env_user(chappy).env_session(GDO_Session.for_user(chappy)).message(text).result(None)
        return new

    def trim_chappies_bad_response(self, text: str) -> str:
        pattern = r'^\d{14}: '
        text = re.sub(pattern, '', text)
        chappy_name = self._env_server.get_connector().gdo_get_dog_user().render_name()
        chappy_name = chappy_name.replace('{', '\\{').replace('}', '\\}')
        pattern = r'^' + chappy_name + r'[^:]*: '
        text = re.sub(pattern, '', text)
        return text
