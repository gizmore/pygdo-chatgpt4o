from asyncio import subprocess

from gdo.base.GDT import GDT
from gdo.base.Logger import Logger
from gdo.base.Method import Method
from gdo.base.Trans import t
from gdo.base.Util import html
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
        return GDO_Permission.ADMIN

    def gdo_parameters(self) -> list[GDT]:
        return [
            GDT_RestOfText('cmd').not_null(),
        ]

    def get_command(self) -> str:
        return self.param_value('cmd')

    async def gdo_execute(self) -> GDT:
        cmd = self.get_command()  #.replace('"', '\\"')
        Logger.debug(cmd)
        process = await subprocess.create_subprocess_exec(
            "timeout", "10s", "bash", "-c", f"cd ~ && {cmd}",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        stdout_decoded = stdout.decode('utf-8').splitlines()
        stderr_decoded = stderr.decode('utf-8').splitlines()
        Logger.debug(str(stderr_decoded))
        if process.returncode != 0:
            return self.err('err_error', [html('\n'.join(stderr_decoded)) or t('unknown_error')])
        return self.reply('%s', [html('\n'.join(stdout_decoded), self._env_mode) or t("msg_success")])

