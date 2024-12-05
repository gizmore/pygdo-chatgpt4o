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
        GDO_ChappyMessage.incoming_text(self._env_user, self._env_channel, text)
        msg = Message(text, self._env_mode).env_copy(self)
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
        messages = GDO_ChappyMessage.get_messages_for_user(message._comrade or message._env_user)
        return await self.send_to_chappy(message, messages)

    async def send_to_chappy(self, message: Message, messages: list):
        try:
            from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
            mod = module_chatgpt4o.instance()
            api = mod.get_openai()
            pprint(messages)
            response = api.chat.completions.create(
                model='gpt-4o',
                messages=messages,
                temperature=0.1, #self.get_temperature(message),
                # max_tokens=max_tokens,
                # n=n,
                # stop=stop,
                # presence_penalty=presence_penalty,
                # frequency_penalty=frequency_penalty,
            )
            # generated_texts = [
            #     choice.message["content"].strip() for choice in response["choices"]
            # ]
            # GDO_ChatMessage.change_state(prompt, msgs, 'answered')
            text = response.choices[0].message.content
            message.result(text)
            await message.deliver(False)
            Application.MESSAGES.put(self.generate_chappy_response(text, message))
        except Exception as ex:
            Logger.exception(ex)

    def generate_chappy_response(self, text: str, msg: Message) -> Message:
        from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
        chappy = msg._env_server.get_connector().gdo_get_dog_user()
        new = msg.message_copy().env_user(chappy).env_session(GDO_Session.for_user(chappy)).message(text).result(None).comrade(msg._env_user)
        return new

