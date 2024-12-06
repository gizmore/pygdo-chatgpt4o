from pprint import pprint

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.base.Method import Method
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.core.GDO_Session import GDO_Session
from gdo.core.GDT_RestOfText import GDT_RestOfText


class gpt(Method):

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_RestOfText('message').not_null(),
        ]

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
               # temperature=mod.cfg_temperature(),
                # max_tokens=max_tokens,
                # n=n,
                # stop=stop,
                # presence_penalty=presence_penalty,
                # frequency_penalty=frequency_penalty,
            )
            text = response.choices[0].message.content
            message.result(text)
            await message.deliver(False)
            Application.MESSAGES.put(self.generate_chappy_response(text, message))
        except Exception as ex:
            Logger.exception(ex)

    def generate_chappy_response(self, text: str, msg: Message) -> Message:
        chappy = msg._env_server.get_connector().gdo_get_dog_user()
        comrade = msg._thread_user if msg._thread_user else msg._env_user
        new = msg.message_copy().env_user(chappy).env_session(GDO_Session.for_user(chappy)).message(text).result(None).comrade(comrade)
        return new

