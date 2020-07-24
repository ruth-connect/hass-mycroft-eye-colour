import asyncio
import logging

from mycroftapi import MycroftAPI

from homeassistant.const import (CONF_DEVICES, CONF_HOST, CONF_NAME,
                                 CONF_TYPE, STATE_ON, STATE_OFF)
try:
  from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                              ATTR_HS_COLOR,
                                              LightEntity,
                                              PLATFORM_SCHEMA,
                                              SUPPORT_BRIGHTNESS,
                                              SUPPORT_COLOR)
except ImportError:
  from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                              ATTR_HS_COLOR,
                                              Light as LightEntity,
                                              PLATFORM_SCHEMA,
                                              SUPPORT_BRIGHTNESS,
                                              SUPPORT_COLOR)
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

CONF_DEFAULT_COLOR = 'default_rgb'
CONF_DEFAULT_LEVEL = 'default_level'
CONF_DEFAULT_TYPE = 'default_type'

# Default color if not specified in configuration
COLOR_MAP = [255, 255, 255]

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_DEFAULT_LEVEL, default=255): cv.byte,
    vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Optional(CONF_NAME): cv.string,
            vol.Optional(CONF_DEFAULT_LEVEL): cv.byte,
            vol.Optional(CONF_DEFAULT_COLOR): vol.All(
                vol.ExactSequence((cv.byte, cv.byte, cv.byte)),
                vol.Coerce(tuple)),
        }
    ]),
})


@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    lights = (MycroftInstance(light) for light in
              config[CONF_DEVICES])
    async_add_devices(lights)

    return True


class MycroftInstance(LightEntity):
    """Representation of a Mycrof instance."""

    def __init__(self, light):

        # Fixture configuration
        self._host = light.get(CONF_HOST)

        self._name = light.get(CONF_NAME)
        
        self._brightness = light.get(CONF_DEFAULT_LEVEL,
                                     dmx_gateway.default_level)
        self._rgb = light.get(CONF_DEFAULT_COLOR, COLOR_MAP.get(self._type))

        # Brightness needs to be set to the maximum default RGB level, then
        # scale up the RGB values to what HA uses
        self._brightness = max(self._rgb) * (self._brightness/255)

        if self._brightness > 0:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF

        # Create Mycroft API.
        self._mycroft = MycroftAPI(self._host)
        
        _LOGGER.debug(f"Intialized Mycroft {self._name}")
        
    @property
    def host(self):
        """Return the Mycroft host."""
        return self._host

    @property
    def name(self):
        """Return the display name of this Mycroft."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of Mycroft's eyes."""
        return self._brightness
    
    @property
    def rgb(self):
        """Return the RGB values of Mycroft's eyes."""
        return self._rgb

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state == STATE_ON

    @property
    def hs_color(self):
        """Return the HS color value."""
        if self._rgb:
            return color_util.color_RGB_to_hs(*self._rgb)
        else:
            return None

    @property
    def min_mireds(self):
        """Return the coldest color_temp that this light supports."""
        # Default to the Philips Hue value that HA has always assumed
        # https://developers.meethue.com/documentation/core-concepts
        return 192

    @property
    def max_mireds(self):
        """Return the warmest color_temp that this light supports."""
        # Default to the Philips Hue value that HA has always assumed
        # https://developers.meethue.com/documentation/core-concepts
        return 448

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._features

    @property
    def should_poll(self):
        return False

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        self._state = STATE_ON

        # Update state from service call
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]

        if self._brightness == 0:
            self._brightness = 255

        if ATTR_HS_COLOR in kwargs:
            self._rgb = color_util.color_hs_to_RGB(*kwargs[ATTR_HS_COLOR])

        if self_.mycroft is not None:
            self._mycroft.eyes_color(*self._rgb)

        self.async_schedule_update_ha_state()
        
        _LOGGER.debug(f"Turned on Mycroft {self._name}")

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        self._state = STATE_OFF
        if self_.mycroft is not None:
            self._mycroft.eyes_color(0, 0, 0)
        self.async_schedule_update_ha_state()
        _LOGGER.debug(f"Turned off Mycroft {self._name}")

    def update(self):
        """Fetch update state."""
        # Nothing to return

def scale_rgb_to_brightness(rgb, brightness):
    brightness_scale = (brightness / 255)
    scaled_rgb = [round(rgb[0] * brightness_scale),
                  round(rgb[1] * brightness_scale),
                  round(rgb[2] * brightness_scale)]
    return scaled_rgb
