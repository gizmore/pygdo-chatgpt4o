import json
import os

from gdo.base.Application import Application
from gdo.base.GDT import GDT
from gdo.base.Method import Method
from gdo.base.ModuleLoader import ModuleLoader
from gdo.base.Util import Files, Strings
from gdo.chatgpt4o.GDO_ChappyMessage import GDO_ChappyMessage
from gdo.core.GDO_Permission import GDO_Permission
from gdo.core.GDT_Bool import GDT_Bool
from gdo.core.GDT_String import GDT_String
from gdo.core.GDT_UInt import GDT_UInt
from gdo.date.Time import Time


class tune(Method):

	DATE_FORMAT: str = '%Y_%m_%d_%H_%M_%S'

	@classmethod
	def gdo_trigger(cls) -> str:
		return "gpt.tune"

	def gdo_user_permission(self) -> str | None:
		return GDO_Permission.ADMIN

	def gdo_connectors(self) -> str:
		return 'bash'

	def gdo_parameters(self) -> list[GDT]:
		return [
			GDT_UInt('pygdo').not_null().initial('0'),
			GDT_Bool('mark').not_null().initial('0'),
			GDT_Bool('v').not_null().initial('0'),
			GDT_String('model').not_null().initial('gpt-4o'),  # gpt-4o-mini | ft:gpt-4o-2024-08-06:personal:chappy:Ae1HhgnK | gpt-4o
		]

	def gdo_execute(self) -> GDT:
		if level := self.param_value('pygdo'):
			return self.train_pygdo(level)
		else:
			return self.train_messages()

	def is_verbose(self) -> bool:
		return self.param_value('v')

	def get_model(self) -> str:
		return self.param_value('model')

	def train_messages(self):
		messages = GDO_ChappyMessage.table().select().where(f'cm_training IS NULL').order('cm_id ASC').exec()
		output_path = Application.temp_path(f"pygdo_chappy_{Time.get_date(None, )}.jsonl")
		count = 0
		count_too_long = 0
		count_too_short = 0
		count_no_chappy = 0
		count_invalid_words = 0
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
			if self.param_value('mark'):
				message.save_val('cm_training', Time.get_date())
		with open(output_path, 'w') as out:
			for thread in grouped:
				example = {"messages": thread}
				jsonl = json.dumps(example)
				if len(jsonl) > 1024:
					count_too_long += 1
					continue
				if len(thread[0]['content']) < 60:
					count_too_short += 1
					continue
				if thread[-1]['role'] != "assistant":
					count_no_chappy += 1
					continue
				if len(thread[-1]['content']) < 60:
					count_too_short += 1
					continue
				if '<|diff'+'_mar'+'ker|>' in jsonl:  # Forbidden word!
					count_invalid_words += 1
					continue
				out.write(jsonl)
				out.write('\n')
				count += 1
		return self.reply('msg_training_file_generated', (count, output_path, count_too_long, count_too_short, count_no_chappy, count_invalid_words))

	def train_pygdo(self, level: int):
		src_files = []
		examples = []
		date = Time.get_date(None, self.DATE_FORMAT)
		output_path = Application.temp_path(f"pygdo_sourcecode_training_{date}.jsonl")
		count = 0

		loader = ModuleLoader.instance()
		modules = loader.load_modules_db()

		folders = []

		folders.append(Application.file_path('DOCS'))
		for module in modules:
			folders.append(module.file_path())
		for folder in folders:
			for root, _, files in os.walk(folder):
				for file in sorted(files):
					if file.endswith('.py') or file.endswith('.css') or file.endswith('.js') or file.endswith('.md') or file.endswith('.toml') or file.endswith('.html'):
						if 'secret' not in file and '__init__' not in file and 'node_modules' not in root and not file.startswith('.') and 'vendor' not in root:
							full_path = os.path.join(root, file)
							src_files.append(full_path)
							if self.is_verbose():
								print(Strings.substr_from(full_path, '/gdo/'))
		if level == 1:
			total_bytes = 0
			for full_path in src_files:
				total_bytes += os.path.getsize(full_path)
			return self.reply('msg_pygdo_src_training', (len(src_files), Files.human_file_size(total_bytes)))
		elif level >= 2:
			now = False
			with open(output_path, 'a') as out:
				for full_path in src_files:
					if full_path.endswith("chatgpt4o/test/test_gpt4o.py"):
						now = True
					if now:
						if example := self.train_pygdo_file(full_path):
							out.write(json.dumps(example))
							out.write('\n')
							count += 1
					else:
						print(f'Skipping {full_path}')
		return self.reply('msg_source_training_file_generated', (count, output_path))

	def train_pygdo_file(self, full_path: str) -> object:
		messages = []
		messages.append(self.system_prompt_sourcecode_generator())
		messages.append(self.gizmore_prompt_sourcecode_generator(full_path))
		from gdo.chatgpt4o.module_chatgpt4o import module_chatgpt4o
		mod = module_chatgpt4o.instance()
		api = mod.get_openai()
		if self.is_verbose():
			print(f"Training for {full_path}...", end="", flush=True)
		response = api.chat.completions.create(
			model=self.get_model(),
			messages=messages,
			temperature=0.0,
			max_tokens=1024,
		)
		if self.is_verbose():
			print(" Done!")
		text = response.choices[0].message.content
		messages.append(self.chappy_prompt_sourcecode_generator(text))
		return {'messages': messages}

	def system_prompt_sourcecode_generator(self) -> object:
		return {
			'role': 'system',
			'content': "You are chappy, artificial life, brought to life by the pygdo chat system from gizmore.\n"
					   "You will read a pygdo source file and generate a brief documentation for it, like it's features or method inheritance.",
		}

	def gizmore_prompt_sourcecode_generator(self, full_path: str) -> object:
		stripped_path = Strings.substr_from(full_path, '/pygdo/')
		with open(full_path, 'r') as f:
			return {
				'role': 'user',
				'content': f'Sourcecode of pygdo/{stripped_path}: {f.read()}',
			}

	def chappy_prompt_sourcecode_generator(self, text: str):
		return {
			'role': 'assistant',
			'content': text,
		}

