#!/usr/bin/env python3
"""
Tests for the catfacts plugin
"""
from __future__ import print_function
from unittest.mock import patch, MagicMock

from nose.tools import ok_, eq_

import catfacts

pytest_plugins = ['errbot.backends.test']

extra_plugin_dir = '.'


@patch('catfacts.requests.get')
def test_get_single_catfact(mock_get):
    """Test getting a single cat fact"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'fact': 'Cats sleep 12-16 hours per day.',
        'length': 30
    }
    mock_get.return_value = mock_response

    facts = plugin.get_catfacts(1)

    eq_(len(facts), 1)
    eq_(facts[0], 'Cats sleep 12-16 hours per day.')
    mock_get.assert_called_once_with("https://catfact.ninja/fact")


@patch('catfacts.requests.get')
def test_get_multiple_catfacts(mock_get):
    """Test getting multiple cat facts"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    # Mock the API responses for multiple calls
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [
        {'fact': 'First cat fact', 'length': 15},
        {'fact': 'Second cat fact', 'length': 16},
        {'fact': 'Third cat fact', 'length': 15}
    ]
    mock_get.return_value = mock_response

    facts = plugin.get_catfacts(3)

    eq_(len(facts), 3)
    eq_(facts[0], 'First cat fact')
    eq_(facts[1], 'Second cat fact')
    eq_(facts[2], 'Third cat fact')
    eq_(mock_get.call_count, 3)

    # Verify all calls were to the single fact endpoint
    for call in mock_get.call_args_list:
        eq_(call[0][0], "https://catfact.ninja/fact")


@patch('catfacts.requests.get')
def test_catfact_command_single(mock_get):
    """Test the catfact command with single fact"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = catfacts.CONFIG_TEMPLATE

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'fact': 'Cats have excellent night vision.',
        'length': 33
    }
    mock_get.return_value = mock_response

    # Mock message object
    mock_message = MagicMock()

    # Test command without arguments (should default to None -> 1)
    results = list(plugin.catfact(mock_message, ''))

    eq_(len(results), 1)
    eq_(results[0], 'Cats have excellent night vision.')


@patch('catfacts.requests.get')
def test_catfact_command_multiple(mock_get):
    """Test the catfact command with multiple facts"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = catfacts.CONFIG_TEMPLATE

    # Mock the API responses
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [
        {'fact': 'Fact one', 'length': 8},
        {'fact': 'Fact two', 'length': 8}
    ]
    mock_get.return_value = mock_response

    mock_message = MagicMock()

    # Test command with argument for 2 facts
    results = list(plugin.catfact(mock_message, '2'))

    eq_(len(results), 2)
    eq_(results[0], 'Fact one')
    eq_(results[1], 'Fact two')


@patch('catfacts.requests.get')
def test_catfact_command_max_limit(mock_get):
    """Test that catfact command respects MAX_FACTS limit"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = {'MAX_FACTS': 3}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.side_effect = [
        {'fact': 'Fact one', 'length': 8},
        {'fact': 'Fact two', 'length': 8},
        {'fact': 'Fact three', 'length': 10}
    ]
    mock_get.return_value = mock_response

    mock_message = MagicMock()

    # Request 10 facts but should be limited to 3
    results = list(plugin.catfact(mock_message, '10'))

    eq_(len(results), 3)
    eq_(mock_get.call_count, 3)


@patch('catfacts.requests.get')
def test_catfact_command_exception_handling(mock_get):
    """Test that catfact command handles exceptions gracefully"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = catfacts.CONFIG_TEMPLATE

    # Mock requests to raise an exception
    mock_get.side_effect = Exception("API Error")

    mock_message = MagicMock()

    # Should not raise exception, just return empty generator
    results = list(plugin.catfact(mock_message, '1'))
    eq_(len(results), 0)


def test_random_fact_method():
    """Test the random_fact method"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = {'FACT_CHANNEL': '#test'}

    # Mock the methods
    with patch.object(plugin, 'get_catfacts') as mock_get_facts, \
         patch.object(plugin, 'send') as mock_send, \
         patch.object(plugin, 'build_identifier') as mock_build_id:

        mock_get_facts.return_value = ['Random cat fact']
        mock_build_id.return_value = 'channel_obj'

        plugin.random_fact()

        mock_get_facts.assert_called_once_with(1)
        mock_build_id.assert_called_once_with('#test')
        mock_send.assert_called_once_with('channel_obj', 'Random cat fact')


def test_configuration_template():
    """Test the configuration template"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    template = plugin.get_configuration_template()

    ok_('MAX_FACTS' in template)
    ok_('FACT_PERIOD_S' in template)
    ok_('FACT_CHANNEL' in template)
    eq_(template['MAX_FACTS'], 5)
    eq_(template['FACT_PERIOD_S'], 86400)
    eq_(template['FACT_CHANNEL'], '#random')


def test_configure_with_config():
    """Test plugin configuration with custom values"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    custom_config = {
        'MAX_FACTS': 10,
        'FACT_PERIOD_S': 3600,
        'FACT_CHANNEL': '#cats'
    }

    with patch('catfacts.BotPlugin.configure') as mock_super_configure:
        plugin.configure(custom_config)

        # Should call parent configure with merged config
        called_config = mock_super_configure.call_args[0][0]
        eq_(called_config['MAX_FACTS'], 10)
        eq_(called_config['FACT_PERIOD_S'], 3600)
        eq_(called_config['FACT_CHANNEL'], '#cats')


def test_configure_with_empty_config():
    """Test plugin configuration with empty config"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    with patch('catfacts.BotPlugin.configure') as mock_super_configure:
        plugin.configure({})

        # Should use default template
        called_config = mock_super_configure.call_args[0][0]
        eq_(called_config, catfacts.CONFIG_TEMPLATE)


def test_activate_with_poller():
    """Test plugin activation with positive poll period"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = {'FACT_PERIOD_S': 3600}

    with patch.object(plugin, 'start_poller') as mock_start_poller, \
         patch('catfacts.BotPlugin.activate') as mock_super_activate:

        plugin.activate()

        mock_super_activate.assert_called_once()
        mock_start_poller.assert_called_once_with(3600, plugin.random_fact)


def test_activate_without_poller():
    """Test plugin activation with zero poll period"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = {'FACT_PERIOD_S': 0}

    with patch.object(plugin, 'start_poller') as mock_start_poller, \
         patch('catfacts.BotPlugin.activate') as mock_super_activate:

        plugin.activate()

        mock_super_activate.assert_called_once()
        mock_start_poller.assert_not_called()


def test_catfact_trigger_command():
    """Test the catfact_trigger admin command"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")
    plugin.config = {'FACT_CHANNEL': '#test'}

    mock_message = MagicMock()

    with patch.object(plugin, 'random_fact') as mock_random_fact, \
         patch.object(plugin, 'build_identifier') as mock_build_id:

        mock_build_id.return_value = 'channel_obj'

        plugin.catfact_trigger(mock_message, '')

        mock_build_id.assert_called_once_with('#test')
        mock_random_fact.assert_called_once()


def test_get_catfacts_zero():
    """Test get_catfacts with zero input"""
    # Create plugin instance with mock bot
    mock_bot = MagicMock()
    mock_bot.repo_manager.plugin_dir = '/test/dir'
    plugin = catfacts.Catfacts(mock_bot, "catfacts")

    # Test with zero (edge case - should return empty list)
    facts = plugin.get_catfacts(0)
    eq_(len(facts), 0)
