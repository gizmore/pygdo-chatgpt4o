import os
import unittest

from gdo.base.Application import Application
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Util import module_enabled
from gdo.chatgpt4o.method.gpt import gpt
from gdo.core.GDO_Session import GDO_Session
from gdo.core.connector.Bash import Bash
from gdotest.TestUtil import web_plug, reinstall_module, web_gizmore, cli_gizmore


class AvatarTest(unittest.TestCase):

    def setUp(self):
        Application.init(os.path.dirname(__file__ + "/../../../../"))
        Application.init_cli()
        Application.set_session(GDO_Session.for_user(web_gizmore()))
        loader = ModuleLoader.instance()
        loader.load_modules_db()
        loader.init_modules(load_vals=True)
        reinstall_module('chatgpt4o')
        return self

    def test_00_simple_text(self):
        gpt().env_user(cli_gizmore()).env_server(Bash.get_server())
        reinstall_module('contact')
        self.assertTrue(module_enabled('contact'), 'cannot install contact')

    def test_01_form_rendering(self):
        web_gizmore()
        out = web_plug('contact.form.html').exec()
        self.assertIn('gizmore', out, 'Staff link not shown on contact form.')


if __name__ == '__main__':
    unittest.main()
