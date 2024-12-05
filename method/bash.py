from asyncio import subprocess

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Trans import t
from gdo.base.Util import html
from gdo.chatgpt.module_chatgpt import module_chatgpt
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_RestOfText import GDT_RestOfText


class bash(Method):
    """
    This method is exclusively for admins and chappy.
    Usage: $bash command here
    """

    def gdo_trigger(self) -> str:
        return 'bash'

    def gdo_user_permission(self) -> str | None:
        return f"{module_chatgpt.PERM_CHAPPY_BOT},{GDO_Permission.ADMIN}"

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_RestOfText('cmd').not_null(),
        ]

    async def gdo_execute(self):
        cmd = self.param_value('cmd')
        process = await subprocess.create_subprocess_exec(
            "runuser", "--user", "gizmore", "bash", "-c", cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = process.communicate()

        stdout_decoded = stdout.decode('utf-8').strip()
        stderr_decoded = stderr.decode('utf-8').strip()

        if process.returncode != 0:
            return self.error_raw(f"Error({process.returncode}): " + html(stderr_decoded))

        return self.reply('%s', [html(stdout_decoded) or t("msg_success")])
