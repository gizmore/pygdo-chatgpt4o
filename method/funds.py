import json
import urllib.parse
from pprint import pprint

import httplib2

from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.date.Time import Time


class funds(Method):

    @classmethod
    def gdo_trigger(cls) -> str:
        return 'funds'

    def gdo_execute(self) -> GDT:
        from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
        api_key = module_chatgpt4o.instance().cfg_api_key()
        http = httplib2.Http()
        headers = {"Authorization": f"Bearer {api_key}"}
        start = urllib.parse.quote_plus(Time.get_date(None, '%Y-%m-%d'))
        url = f"https://api.openai.com/v1/dashboard/activity?start_date={start}&end_date={start}"
        response = http.request(url, headers=headers)
        data = json.loads(response[1])
        pprint(data)

        amount = 0

        return self.reply('msg_funds', (amount,))
