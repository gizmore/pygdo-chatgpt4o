import re

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDT_Float import GDT_Float
from gdo.core.GDT_RestOfText import GDT_RestOfText
from gdo.markdown.MDConvert import MDConvert


class gpt(Method):

    PROCESSING: bool = False
    # LAST_RESPONSE: str = ""

    def gdo_trigger(self) -> str:
        return 'gpt'

    def gdo_default_enabled(self) -> bool:
        return False

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_RestOfText('message').not_null(),
        ]

    def gdo_method_config_user(self) -> [GDT]:
        return [
            GDT_Float('temperature').min(0).max(2).initial("0.2"),
        ]

    def gdo_method_config_channel(self) -> [GDT]:
        return [
            GDT_Float('temperature').min(0).max(2).initial("0.2"),
        ]

    def cfg_temperature(self, message: Message) -> float:
        if message._env_channel:
            return self.get_config_channel_value('temperature')
        else:
            return self.get_config_user_value('temperature')

    async def gdo_execute(self):
        text = self.param_value('message')
        msg = Message(text, self._env_mode).env_copy(self)
        GDO_ChappyMessage.incoming(msg)
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
        messages = GDO_ChappyMessage.get_messages_for_channel(message._env_channel)
        return await self.send_to_chappy(message, messages)

    async def send_user_to_chappy(self, message: Message):
        messages = GDO_ChappyMessage.get_messages_for_user(message._thread_user if message._thread_user else message._env_user)
        return await self.send_to_chappy(message, messages)

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
                # n=n,
                # stop=stop,
                # presence_penalty=presence_penalty,
                # frequency_penalty=frequency_penalty,
            )
            self.__class__.PROCESSING = False
            text = response.choices[0].message.content
            text = self.trim_chappies_bad_response(text)
            text = MDConvert(text).to(message._env_mode)
            message.result(text)
            comrade = message._thread_user if message._thread_user else message._env_user
            message.comrade(comrade)
            await message.deliver(False, False)
            # if text != self.__class__.LAST_RESPONSE:
            Application.MESSAGES.put(self.generate_chappy_response(text, message))
                # self.__class__.LAST_RESPONSE = text
        except Exception as ex:
            Logger.exception(ex)
        return self.empty()

    def generate_chappy_response(self, text: str, msg: Message) -> Message:
        chappy = msg._env_server.get_connector().gdo_get_dog_user()
        comrade = msg._thread_user if msg._thread_user else msg._env_user
        new = msg.message_copy().env_user(chappy).env_session(GDO_Session.for_user(chappy)).message(text).result(None).comrade(comrade)
        return new

    def trim_chappies_bad_response(self, text: str) -> str:
        pattern = r'^\d{14}: '
        text = re.sub(pattern, '', text)
        chappy_name = self._env_server.get_connector().gdo_get_dog_user().render_name()
        chappy_name = chappy_name.replace('{', '\\{').replace('}', '\\}')
        pattern = r'^' + chappy_name + r'[^:]*: '
        text = re.sub(pattern, '', text)
        return text
