from asyncio import subprocess

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.Trans import t
from gdo.base.Util import html
from gdo.core.GDT_RestOfText import GDT_RestOfText


class bash(Method):
    """
    This method is exclusively for admins and chappy.
    Usage: $bash command here
    """

    def gdo_trigger(self) -> str:
        return 'bash'

    # def gdo_user_permission(self) -> str | None:
    #     return f"{module_chatgpt.PERM_CHAPPY_BOT},{GDO_Permission.ADMIN}"

    def gdo_parameters(self) -> [GDT]:
        return [
            GDT_RestOfText('cmd').not_null(),
        ]

    async def gdo_execute(self):
        cmd = self.param_value('cmd')
        process =  await subprocess.create_subprocess_exec(
            "sudo", "-u", "chappy", "bash", "-c", f"cd ~ && {cmd}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        stdout_decoded = stdout.decode('utf-8').strip().splitlines()
        stderr_decoded = stderr.decode('utf-8').strip().splitlines()
        if process.returncode != 0:
            return self.error_raw(f"Error({process.returncode}): {html('\n'.join(stderr_decoded)) or t('msg_unknown_error')}")
        return self.reply('%s', [html('\n'.join(stdout_decoded)) or t("msg_success")])
