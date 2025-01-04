import os
import unittest

from gdo.base.Application import Application
from gdo.base.Message import Message
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Render import Mode
from gdo.chatgpt4o.method.gpt import gpt
from gdo.core.GDO_Server import GDO_Server
from gdo.core.GDO_Session import GDO_Session
from gdotest.TestUtil import cli_plug, reinstall_module, cli_gizmore


class GPT4oTest(unittest.TestCase):

    def setUp(self):
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        Application.init_cli()
        Application.set_session(GDO_Session.for_user(cli_gizmore()))
        loader = ModuleLoader.instance()
        loader.load_modules_db()
        loader.init_modules(load_vals=True)
        reinstall_module('chatgpt4o')
        return self

    def test_00_bash(self):
        out = cli_plug(cli_gizmore(), "$bash ls -asl")
        self.assertIn('..', out, 'Bash does not work')
        
    def test_01_cfg_window_size(self):
        server = GDO_Server.get_by_connector('bash')
        channel = server.get_or_create_channel('test')
        message = Message("$gpt.goal", Mode.CLI).env_server(server).env_channel(channel).env_user(cli_gizmore(), True)
        method = gpt().env_copy(message)
        self.assertEqual("50", method.cfg_window_size(), "Getting window size for channels does not work.")

if __name__ == '__main__':
    unittest.main()
