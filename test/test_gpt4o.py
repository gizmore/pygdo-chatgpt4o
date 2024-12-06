import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
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


if __name__ == '__main__':
    unittest.main()
