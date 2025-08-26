# Plugin for getting catfacts, randomly or on command

from errbot import BotPlugin, botcmd

import requests
import logging

from itertools import chain

# Set up logging for this plugin
logger = logging.getLogger(__name__)

CONFIG_TEMPLATE = {'MAX_FACTS': 5,
                   'FACT_PERIOD_S': 86400,
                   'FACT_CHANNEL': '#random'
                   }


class Catfacts(BotPlugin):
    """Plugin for all your cat fact needs!"""
    min_err_version = '3.0.0'  # Optional, but recommended

    def get_catfacts(self, number):
        logger.info(f"get_catfacts called with number={number}")
        facts = []
        for i in range(number):
            logger.info(f"Making API request #{i+1}/{number} to catfact.ninja")
            r = requests.get("https://catfact.ninja/fact")
            logger.info(f"API response: status_code={r.status_code}, url={r.url}")
            
            if r.status_code == 200:
                data = r.json()
                if 'fact' in data:
                    fact = data['fact']
                    facts.append(fact)
                    logger.info(f"Received fact #{i+1}: {fact[:50]}{'...' if len(fact) > 50 else ''}")
                else:
                    logger.warning(f"API response missing 'fact' field: {data}")
            else:
                logger.warning(f"API request failed with status {r.status_code}")
            
            # Small delay to avoid rate limiting when getting multiple facts
            if len(facts) < number:
                import time
                time.sleep(0.1)
                
        logger.info(f"get_catfacts returning {len(facts)} facts")
        return facts

    @botcmd
    def catfact(self, mess, args):
        """A command which returns some number of catfacts"""
        logger.info(f"catfact command called with args='{args}' from user {mess.frm}")
        try:
            number = max(1, min(self.config['MAX_FACTS'], int(args))) if args else 1
            logger.info(f"Requesting {number} facts (max allowed: {self.config.get('MAX_FACTS', 'unknown')})")
            facts = self.get_catfacts(number)
            logger.info(f"catfact command yielding {len(facts)} facts")
            for i, fact in enumerate(facts):
                logger.info(f"Yielding fact #{i+1}: {fact[:50]}{'...' if len(fact) > 50 else ''}")
                yield fact
        except Exception as e:
            logger.error(f"Exception in catfact command: {e}")
            pass

    @botcmd(admin_only=True)
    def catfact_trigger(self, mess, args):
        """Triggers a catfact in the configured channel"""
        logger.info(f"catfact_trigger called by {mess.frm if mess else 'system'}")
        if 'FACT_CHANNEL' in self.config and self.build_identifier(self.config['FACT_CHANNEL']):
            fact_channel = self.config['FACT_CHANNEL']
            logger.info(f"Triggering random fact to channel: {fact_channel}")
            self.random_fact()
        else:
            logger.warning("catfact_trigger called but FACT_CHANNEL not configured or invalid")

    def random_fact(self):
        logger.info("random_fact called (triggered by poller or catfact_trigger)")
        channel = self.config['FACT_CHANNEL']
        logger.info(f"Getting single random fact for channel: {channel}")
        
        facts = self.get_catfacts(1)
        
        if facts:
            fact = facts[0]
            logger.info(f"random_fact sending to {channel}: {fact[:60]}{'...' if len(fact) > 60 else ''}")
            self.send(self.build_identifier(channel), fact)
        else:
            logger.error("random_fact: No facts returned from get_catfacts(1)")
            self.send(self.build_identifier(channel), "🐱 Cat fact service is temporarily unavailable!")

    def _poller_callback(self):
        """Wrapper method for poller to avoid method caching issues"""
        logger.info("_poller_callback called by poller")
        self.random_fact()

    def activate(self):
        """Activates plugin, activating the random facts if the period is positive seconds"""
        logger.info("Catfacts plugin activating")
        super(Catfacts, self).activate()
        
        period = self.config.get('FACT_PERIOD_S', 0)
        channel = self.config.get('FACT_CHANNEL', 'not set')
        logger.info(f"Configuration: FACT_PERIOD_S={period}, FACT_CHANNEL={channel}")
        
        if period > 0:
            logger.info(f"Starting poller with {period} second interval")
            self.start_poller(period, self._poller_callback)
        else:
            logger.info("Poller disabled (FACT_PERIOD_S <= 0)")

    def get_configuration_template(self):
        """Defines the configuration structure this plugin supports

        You should delete it if your plugin doesn't use any configuration like this"""
        return CONFIG_TEMPLATE

    def configure(self, configuration):
        logger.info(f"Catfacts plugin configure called with: {configuration}")
        if configuration is not None and configuration != {}:
            config = dict(chain(CONFIG_TEMPLATE.items(),
                                configuration.items()))
        else:
            config = CONFIG_TEMPLATE
        logger.info(f"Final configuration: {config}")
        super(Catfacts, self).configure(config)
