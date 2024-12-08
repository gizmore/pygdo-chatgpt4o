from datetime import datetime

from gdo.base.Application import Application
from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Message import Message
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_Text import GDT_Text
from gdo.core.GDT_User import GDT_User
from gdo.date.GDT_Created import GDT_Created
from gdo.date.GDT_Timestamp import GDT_Timestamp
from gdo.date.Time import Time


class GDO_ChappyMessage(GDO):

    def gdo_columns(self) -> list[GDT]:
        return [
            GDT_AutoInc('cm_id'),
            GDT_User('cm_sender').not_null(),
            GDT_User('cm_user'),
            GDT_Channel('cm_channel'),
            GDT_Text('cm_message').not_null(),
            GDT_Timestamp('cm_sent'),
            GDT_Created('cm_created'),
        ]

    def get_sender(self) -> GDO_User:
        return self.gdo_value('cm_sender')

    def get_user(self) -> GDO_User:
        return self.gdo_value('cm_user')

    def get_channel(self) -> GDO_Channel | None:
        return self.gdo_value('cm_channel')

    def get_created(self) -> datetime:
        return self.gdo_value('cm_created')

    def get_role(self):
        user = self.get_sender()
        if user.is_type('system'):
            return 'user'
        if user == user.get_server().get_connector().gdo_get_dog_user():
            return 'assistant'
        return 'user'

    def get_gpt_content(self):
        timestamp = self.get_created().strftime('%Y%m%d%H%M%S')
        user = self.get_sender()
        chan = self.get_channel()
        channel = chan.render_name()if chan is not None else ''
        sid = "{" + user.get_server_id() + "}"
        content = f"{timestamp}: {user.get_displayname()}{sid}{channel}: {self.gdo_val('cm_message')}"
        return content

    @classmethod
    def incoming(cls, message: Message):
        mark_sent = message._env_user == message._env_server.get_connector().gdo_get_dog_user()
        user = None
        if not message._env_channel:
            user = message._thread_user if message._thread_user else message._env_user
            user = user.get_id()
        cls.blank({
            'cm_sender': message._env_user.get_id(),
            'cm_user': user,
            'cm_channel': message._env_channel.get_id() if message._env_channel else None,
            'cm_message': message._message,
            'cm_sent': Time.get_date() if mark_sent else None,
        }).insert()

    @classmethod
    def outgoing(cls, message: Message, mark_sent: bool = False):
        user = None
        if not message._env_channel:
            user = message._thread_user.get_id() if message._thread_user else message._env_user.get_id()
        cls.blank({
            'cm_sender': GDO_User.system().get_id(),
            'cm_user': user,
            'cm_channel': message._env_channel.get_id() if message._env_channel else None,
            'cm_message': message._result,
            'cm_sent': Time.get_date() if mark_sent else None,
        }).insert()

    @classmethod
    def genome_message(cls, message: Message):
        from gdo.chatgpt4o.method.goal import goal
        from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
        mod = module_chatgpt4o.instance()
        role = 'user' if mod.cfg_model().startswith('o1') else 'system'
        content = mod.cfg_genome()
        the_goal = goal().env_copy(message).cfg_goal()
        content += f"Your current goal here is: {the_goal}\n"
        return {"role": role, "content": content}

    @classmethod
    def get_messages_for_channel(cls, message: Message, with_genome: bool = True, mark_sent: bool = True):
        cut = Time.get_date(Application.TIME - Time.ONE_DAY * 7)
        condition = f"cm_channel={message._env_channel.get_id()} AND cm_created >= '{cut}'"
        return cls.get_messages_for_condition(message, condition, with_genome, mark_sent)

    @classmethod
    def get_messages_for_user(cls, message: Message, with_genome: bool = True, mark_sent: bool = True):
        cut = Time.get_date(Application.TIME - Time.ONE_DAY * 7)
        user = message._thread_user if message._thread_user else message._env_user
        condition = f"cm_user={user.get_id()} AND cm_created > '{cut}'"
        return cls.get_messages_for_condition(message, condition, with_genome, mark_sent)

    @classmethod
    def get_messages_for_condition(cls, message: Message, condition: str, with_genome: bool = True, mark_sent: bool = True):
        from gdo.chatgpt4o.method.gpt import gpt
        back = []
        if with_genome:
            back.append(cls.genome_message(message))
        context_window_size = gpt().env_copy(message).cfg_window_size(message)
        messages = cls.table().select().where(condition).order('cm_id DESC').limit(int(context_window_size)).exec().fetch_all()
        messages.reverse()
        for msg in messages:
            back.append({
                "role": msg.get_role(),
                "content": msg.get_gpt_content(),
            })
            if mark_sent and msg.gdo_val('cm_sent') is None:
                msg.save_val('cm_sent', Time.get_date())
        return back
