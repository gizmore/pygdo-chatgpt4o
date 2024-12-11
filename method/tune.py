import json
import os

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_String import GDT_String
from gdo.date.Time import Time


class tune(Method):
	def gdo_trigger(self) -> str:
		return "gpt.tune"

	def gdo_user_permission(self) -> str | None:
		return GDO_Permission.ADMIN

	def gdo_parameters(self) -> [GDT]:
		return [
			GDT_Bool('pygdo').initial('0'),
		]

	def gdo_execute(self):
		if self.param_value('pygdo'):
			return self.train_pygdo()
		else:
			return self.train_messages()

	def train_messages(self):
		# from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
		# mod = module_chatgpt4o.instance()
		# api = mod.get_openai()
		messages = GDO_ChappyMessage.table().select().where(f'cm_training IS NULL').order('cm_id ASC').exec()
		output_path = Application.temp_path('pygdo_training.jsonl')
		count = 0
		count_too_long = 0
		count_no_chappy = 0
		current = []
		grouped = []
		has_chappy = False
		for message in messages:
			if message.is_from_user():
				if current and has_chappy:
					grouped.append(current)
				current = []
				has_chappy = False
			elif message.is_from_chappy():
				has_chappy = True
			current.append({'role': message.get_role(), 'content': message.get_gpt_content()})
			message.save_val('cm_training', Time.get_date())
		with open(output_path, 'w') as out:
			for thread in grouped:
				example = {"messages": thread}
				jsonl = json.dumps(example)
				if len(jsonl) > 1024:
					count_too_long += 1
					continue
				if thread[-1]['role'] != "assistant":
					count_no_chappy += 1
					continue
				out.write(jsonl)
				out.write('\n')
				count += 1
		return self.reply('msg_training_file_generated', [count, output_path, count_too_long, count_no_chappy])

	def train_pygdo(self):
		from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
		mod = module_chatgpt4o.instance()
		api = mod.get_openai()

		output_path = Application.temp_path('pygdo_training.jsonl')
		count = 0
		with open(output_path, 'w') as out:
			for root, _, files in os.walk(Application.file_path()):
				for file in files:
					if file.endswith('.py') or file.endswith('.css') or file.endswith('.js') or file.endswith('.md') or file.endswith('.toml'):
						if 'secret' not in file and '__init__' not in file and 'node_modules' not in root and not file.startswith('.'):
							with open(os.path.join(root, file), 'r') as f:
								code = f.read()
								fullpath = f"{root}/{file}".replace('//', '/')
								example = {
									"messages": [
										{"role": "user", "content": f"What is the sourcecode of {fullpath}?"},
										{"role": "assistant", "content": f"{code}"},
									],
								}
								out.write(json.dumps(example))
								out.write('\n')
								count += 1
		return self.reply('msg_training_file_generated', [count, output_path])
		# api.files.create(
		# 	file=open(output_path, "rb"),
		# 	purpose="fine-tune"
		# )
