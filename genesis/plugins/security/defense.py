import ConfigParser
import os

from genesis.com import *
from genesis.api import *
from genesis import apis


class F2BConfigNotFound(Exception):
	def __str__(self):
		return ('The intrusion prevention config file could not be found, '
			'or the system (fail2ban) is not installed.')


class F2BManager(Plugin):
	abstract = True
	jailconf = '/etc/fail2ban/jail.conf'
	filters = '/etc/fail2ban/filter.d'

	def get_jail_config(self):
		cfg = ConfigParser.RawConfigParser()
		if cfg.read(self.jailconf) == []:
			raise F2BConfigNotFound()
		return cfg

	def enable_jail(self, jailname):
		cfg = self.get_jail_config()
		cfg.set(jailname, 'enabled', 'true')
		f = open(self.jailconf, 'w')
		cfg.write(f)
		f.close()

	def disable_jail(self, jailname):
		cfg = self.get_jail_config()
		cfg.set(jailname, 'enabled', 'false')
		f = open(self.jailconf, 'w')
		cfg.write(f)
		f.close()

	def enable_all(self, obj):
		cfg = self.get_jail_config()
		for jail in obj['f2b']:
			cfg.set(jail['name'], 'enabled', 'true')
		f = open(self.jailconf, 'w')
		cfg.write(f)
		f.close()

	def disable_all(self, obj):
		cfg = self.get_jail_config()
		for jail in obj['f2b']:
			cfg.set(jail['name'], 'enabled', 'false')
		f = open(self.jailconf, 'w')
		cfg.write(f)
		f.close()

	def bantime(self, bantime=''):
		cfg = self.get_jail_config()
		if bantime == '':
			return cfg.get('DEFAULT', 'bantime')
		elif bantime != cfg.get('DEFAULT', 'bantime'):
			cfg.set('DEFAULT', 'bantime', bantime)
			f = open(self.jailconf, 'w')
			cfg.write(f)
			f.close()

	def findtime(self, findtime=''):
		cfg = self.get_jail_config()
		if findtime == '':
			return cfg.get('DEFAULT', 'findtime')
		elif findtime != cfg.get('DEFAULT', 'findtime'):
			cfg.set('DEFAULT', 'findtime', findtime)
			f = open(self.jailconf, 'w')
			cfg.write(f)
			f.close()

	def maxretry(self, maxretry=''):
		cfg = self.get_jail_config()
		if maxretry == '':
			return cfg.get('DEFAULT', 'maxretry')
		elif maxretry != cfg.get('DEFAULT', 'maxretry'):
			cfg.set('DEFAULT', 'maxretry', maxretry)
			f = open(self.jailconf, 'w')
			cfg.write(f)
			f.close()

	def upd_ignoreip(self, ranges):
		ranges.insert(0, '127.0.0.1/8')
		s = ' '.join(ranges)
		cfg = self.get_jail_config()
		if s != cfg.get('DEFAULT', 'ignoreip'):
			cfg.set('DEFAULT', 'ignoreip', s)
			f = open(self.jailconf, 'w')
			cfg.write(f)
			f.close()

	def get_all(self):
		lst = []
		remove = []
		cfg = self.get_jail_config()
		fcfg = ConfigParser.SafeConfigParser()
		for c in self.app.grab_plugins(ICategoryProvider):
			if hasattr(c.plugin_info, 'f2b') and \
			hasattr(c.plugin_info, 'f2b_name') and \
			c.plugin_info.f2b and c.plugin_info.f2b_name:
				lst.append({'name': c.plugin_info.f2b_name,
					'icon': c.plugin_info.f2b_icon,
					'f2b': c.plugin_info.f2b})
			elif hasattr(c.plugin_info, 'f2b') and c.plugin_info.f2b:
				lst.append({'name': c.text,
					'icon': c.plugin_info.iconfont,
					'f2b': c.plugin_info.f2b})
			elif hasattr(c, 'f2b') and hasattr(c, 'f2b_name') and \
			c.f2b and c.f2b_name:
				lst.append({'name': c.f2b_name,
					'icon': c.f2b_icon,
					'f2b': c.f2b})
			elif hasattr(c, 'f2b') and c.f2b:
				lst.append({'name': c.text,
					'icon': c.iconfont,
					'f2b': c.f2b})
		for s in apis.webapps(self.app).get_apptypes():
			if hasattr(s.plugin_info, 'f2b') and s.plugin_info.f2b:
				lst.append({'name': s.plugin_info.name, 
					'icon': 'gen-earth',
					'f2b': s.plugin_info.f2b})
		for p in lst:
			for l in p['f2b']:
				if not 'custom' in l:
					try:
						jail_opts = cfg.items(l['name'])
					except ConfigParser.NoSectionError:
						remove.append(p)
						continue
					filter_name = cfg.get(l['name'], 'filter')
					if "%(__name__)s" in filter_name:
						filter_name = filter_name.replace("%(__name__)s", l['name'])
					c = fcfg.read([self.filters+'/common.conf', 
						self.filters+'/'+filter_name+'.conf'])
					filter_opts = fcfg.items('Definition')
					l['jail_opts'] = jail_opts
					l['filter_name'] = filter_name
					l['filter_opts'] = filter_opts
				else:
					if not os.path.exists(self.filters+'/'+l['filter_name']+'.conf'):
						f = open(self.filters+'/'+l['filter_name']+'.conf', 'w')
						fcfg = ConfigParser.SafeConfigParser()
						fcfg.add_section('Definition')
						for o in l['filter_opts']:
							fcfg.set('Definition', o[0], o[1])
						fcfg.write(f)
						f.close()
					if not l['name'] in cfg.sections():
						f = open(self.jailconf, 'w')
						cfg.add_section(l['name'])
						for o in l['jail_opts']:
							cfg.set(l['name'], o[0], o[1])
						cfg.write(f)
						f.close()
					else:
						jail_opts = cfg.items(l['name'])
						filter_name = cfg.get(l['name'], 'filter')
						fcfg.read([self.filters+'/common.conf', 
							self.filters+'/'+filter_name+'.conf'])
						filter_opts = fcfg.items('Definition')
						l['jail_opts'] = jail_opts
						l['filter_name'] = filter_name
						l['filter_opts'] = filter_opts
		for x in remove:
			lst.remove(x)
		return lst
