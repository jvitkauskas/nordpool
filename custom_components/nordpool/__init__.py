import logging

from collections import defaultdict

import pendulum
from .misc import *

from homeassistant.const import CONF_CURRENCY
import voluptuous as vol

DOMAIN = "nordpool"
_LOGGER = logging.getLogger(__name__)

_CURRENCY_LIST = ["DKK", "EUR", "NOK", "SEK"]


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {}
        )
    },
    extra=vol.ALLOW_EXTRA,
)


NAME = DOMAIN
VERSION = '0.0.1'
ISSUEURL = 'https://github.com/Hellowlol/nordpool/issues'

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
""".format(name=NAME, version=VERSION, issueurl=ISSUEURL)


class NordpoolData:
    def __init__(self):
        self.spot = None
        self._last_update_tomorrow_date = None
        self._last_tick = None
        self._data = defaultdict(dict)
        self.currency = []

    def update(self, force=False):
        """Update any required info."""
        from nordpool import elspot

        if self._last_update_tomorrow_date is None:
            if pendulum.now("Europe/Stockholm") > pendulum.now("Europe/Stockholm").at(14):
                self._last_update_tomorrow_date = pendulum.tomorrow("Europe/Stockholm").at(14)
            else:
                self._last_update_tomorrow_date = pendulum.today("Europe/Stockholm").at(14)

        if self._last_tick is None:
            self._last_tick = pendulum.now()

        if force:
            for currency in self.currency:
                spot = elspot.Prices(currency)
                today = spot.hourly(end_date=pendulum.now())
                self._data[currency]['today'] = today["areas"]

                tomorrow = self.spot.hourly()
                if tomorrow:
                    self._data[currency]['tomorrow'] = tomorrow["areas"]

            return

        for currency in self.currency:
            # Add any missing power prices for today in the currency we track
            if self._data.get(currency, {}).get('today') is None:
                spot = elspot.Prices(currency)
                today = spot.hourly(end_date=pendulum.now())
                if today:

                    self._data[currency]["today"] = today["areas"]

            # Add missing prices for tomorrow.
            if self._data.get(currency, {}).get('tomorrow') is None:
                if pendulum.now("Europe/Stockholm") > pendulum.now("Europe/Stockholm").at(14):
                    self._last_update_tomorrow_date = pendulum.tomorrow("Europe/Stockholm").at(14)
                    spot = elspot.Prices(currency)
                    tomorrow = spot.hourly()
                    if tomorrow:
                        self._data[currency]["tomorrow"] = tomorrow["areas"]
                else:
                    _LOGGER.info("New api data for tomorrow isnt posted yet")

        # Check if there is any "new tomorrows data"
        if (self._last_tick.in_timezone("Europe/Stockholm") > self._last_update_tomorrow_date):
            self._last_update_tomorrow_date = pendulum.tomorrow("Europe/Stockholm").at(14)
            for currency in self.currency:
                spot = elspot.Prices(currency)
                tomorrow = spot.hourly(pendulum.now().add(days=1))
                if tomorrow:
                    _LOGGER.info(
                        "New data was posted updating tomorrow prices in NordpoolData %s", currency
                    )
                    self._data[currency]["tomorrow"] = tomorrow["areas"]

        if is_new(self._last_tick, typ="day"):
            for currency in self.currency:
                spot = elspot.Prices(currency)
                today = spot.hourly(end_date=pendulum.now())
                if today:
                    self._data[currency]["today"] = today["areas"]
                # We could swap, but ill rather do a extrac api call.
                # self._data[currency]["today"] = self._data[currency]["tomorrow"]

        self._last_tick = pendulum.now()

    def _someday(self, area, currency, day):
        """Returns todays or tomorrows prices in a area in the currency"""
        if currency not in _CURRENCY_LIST:
            raise ValueError("%s is a invalid currency possible values are %s" % (currency, ', '.join(_CURRENCY_LIST)))

        if currency not in self.currency:
            self.currency.append(currency)

        self.update()
        return self._data.get(currency, {}).get(day, {}).get(area)

    def today(self, area, currency) -> dict:
        """Returns todays prices in a area in the currency"""
        return self._someday(area, currency, "today")

    def tomorrow(self, area, currency):
        """Returns tomorrows prices in a area in the currency"""
        return self._someday(area, currency, "tomorrow")


async def async_setup(hass, config) -> bool:
    """Set up using yaml config file."""
    _LOGGER.info("async_setup nordpool")
    api = NordpoolData()
    hass.data[DOMAIN] = api
    return True


async def async_setup_entry(hass, config_entry):
    """Set up nordpool as config entry."""
    _LOGGER.info("async_setup_entry nordpool")
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )
    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    return True


''' #org
def setup(hass, config):
    """Setup the integration"""




    if config.get(DOMAIN) is None:
        # We get her if the integration is set up using config flow
        return True

    api = NordpoolData()
    hass.data[DOMAIN] = api
    _LOGGER.info(STARTUP)

    # Return boolean to indicate that initialization was successful.
    return True
'''

'''
async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    _LOGGER.info("ZOMG!")
    conf = hass.data.get(DOMAIN)
    if config_entry.source == config_entries.SOURCE_IMPORT:
        if conf is None:
            hass.async_create_task(
                hass.config_entries.async_remove(config_entry.entry_id)
            )
        return False

    _LOGGER.info(STARTUP)

    # Do we need a data dict for something?
    # Create DATA dict
    hass.data[DOMAIN] = {}

    # Get "global" configuration.
    #username = config_entry.data.get(CONF_USERNAME)
    #password = config_entry.data.get(CONF_PASSWORD)

    # Configure the client.
    hass.data[DOMAIN] = NordpoolData()

    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    return True
'''
