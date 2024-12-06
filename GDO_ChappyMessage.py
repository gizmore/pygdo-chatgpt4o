from datetime import datetime

from gdo.base.Application import Application
from gdo.base.GDO import GDO
from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Message import Message
from gdo.core.GDO_Channel import GDO_Channel
from gdo.core.GDO_User import GDO_User
from gdo.core.GDT_AutoInc import GDT_AutoInc
from gdo.core.GDT_Channel import GDT_Channel
from gdo.core.GDT_String import GDT_String
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
            GDT_String('cm_message').not_null().maxlen(1024),
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
        channel = f"#{chan.get_name()}" if chan is not None else ''
        sid = "{" + user.get_server_id() + "}"
        content = f"{timestamp}: {user.get_displayname()}{sid}{channel}: {self.gdo_val('cm_message')}"
        Logger.debug(content)
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
        cls.blank({
            'cm_sender': GDO_User.system().get_id(),
            'cm_user': message._thread_user.get_id() if message._thread_user else message._env_user.get_id(),
            'cm_channel': message._env_channel.get_id() if message._env_channel else None,
            'cm_message': message._result,
            'cm_sent': Time.get_date() if mark_sent else None,
        }).insert()

    @classmethod
    def genome_message(cls):
        from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
        mod = module_chatgpt4o.instance()
        role = 'user' if mod.cfg_model().startswith('o1') else 'system'
        return {"role": role, "content": mod.cfg_genome()}

    @classmethod
    def get_messages_for_channel(cls, channel: GDO_Channel, with_genome: bool = True, mark_sent: bool = True):
        cut = Time.get_date(Application.TIME - Time.ONE_DAY * 7)
        condition = f"cm_channel={channel.get_id()} AND cm_created >= '{cut}'"
        return cls.get_messages_for_condition(condition, with_genome, mark_sent)

    @classmethod
    def get_messages_for_user(cls, user: GDO_User, with_genome: bool = True, mark_sent: bool = True):
        cut = Time.get_date(Application.TIME - Time.ONE_DAY * 7)
        condition = f"cm_user={user.get_id()} AND cm_created > '{cut}'"
        return cls.get_messages_for_condition(condition, with_genome, mark_sent)

    @classmethod
    def get_messages_for_condition(cls, condition: str, with_genome: bool = True, mark_sent: bool = True):
        back = []
        if with_genome:
            back.append(cls.genome_message())
        messages = cls.table().select().where(condition).order('cm_id DESC, cm_created DESC').limit(1000).exec().fetch_all()
        messages.reverse()
        for message in messages:
            back.append({
                "role": message.get_role(),
                "content": message.get_gpt_content(),
            })
            if mark_sent and message.gdo_val('cm_sent') is None:
                message.save_val('cm_sent', Time.get_date())
        return back
