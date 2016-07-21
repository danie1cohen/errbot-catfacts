# Plugin for getting catfacts, randomly or on command

from errbot import BotPlugin, botcmd, webhook

import requests

from itertools import chain

CONFIG_TEMPLATE = {'MAX_FACTS': 5,
                'FACT_PERIOD_S': 86400,
                'FACT_CHANNEL': '#random'
                }

class Catfacts(BotPlugin):
    """Plugin for all your cat fact needs!"""
    min_err_version = '3.0.0' # Optional, but recommended

    def get_catfacts(self, number):
        payload = {'number': number}
        r = requests.get("http://catfacts-api.appspot.com/api/facts", params=payload)
        return r.json()['facts']

    @botcmd
    def catfact(self, mess, args):
        """A command which returns some number of catfacts"""
        try:
            number = max(1, min(self.config['MAX_FACTS'], int(args))) if args else None
            facts = self.get_catfacts(number)
            for ii in facts:
                yield ii
        except Exception:
            pass

    @botcmd(admin_only=True)
    def catfact_trigger(self, mess, args):
        """Triggers a catfact in the configured channel"""
        if 'FACT_CHANNEL' in self.config and self.build_identifier(self.config['FACT_CHANNEL']):
            self.random_fact()

    def random_fact(self):
        facts = self.get_catfacts(1)
        self.send(self.build_identifier(self.config['FACT_CHANNEL']), facts[0])

    def activate(self):
        """Activates plugin, activating the random facts if the period is positive seconds"""
        super(Catfacts, self).activate()
        if self.config['FACT_PERIOD_S'] > 0:
            self.start_poller(self.config['FACT_PERIOD_S'], self.random_fact)

    def get_configuration_template(self):
        """Defines the configuration structure this plugin supports

        You should delete it if your plugin doesn't use any configuration like this"""
        return CONFIG_TEMPLATE

    def configure(self, configuration):
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CONFIG_TEMPLATE
        super(Catfacts, self).configure(config)
