# -*- coding: utf-8 -*-

"""
Example demonstrating:

- Followall for different kinds of things, private owned and public non-owned
"""

# Python 2 backwards compatibility
from __future__ import unicode_literals, print_function

from time import sleep
import logging
logging.basicConfig(format='%(asctime)s,%(msecs)03d %(levelname)s [%(name)s] {%(threadName)s} %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger('IoticAgent.Core.Client').setLevel(logging.WARNING)
logging.getLogger('IoticAgent.IOT').setLevel(logging.WARNING)

from IoticAgent import ThingRunner, Datatypes, Units
from IoticAgent.IOT.RemotePoint import RemoteFeed
from IoticAgent.IOT.Exceptions import IOTUnknown

KEY_ID = 'id'
KEY_PARSED = 'parsed'
KEY_DATA = 'data'
KEY_TEMP = 'temp'
KEY_POWER = 'power_consumption'
KEY_FEED_NAME = 'Readings'


class DemoThing(ThingRunner):
    # pylint: disable=attribute-defined-outside-init

    thing_lid = 'demo_thing'
    thing_label = 'DemoThing instance'
    thing_description = 'Example thing only!'
    # Set to None to not have location set
    thing_location = None
    thing_tags = ['DemoThing', 'specialDemoTag']
    thing_public = False

    def __init__(self, config=None):
        super(DemoThing, self).__init__(config=config)
        self.__thing = None
        self.__hvacs = []

    def on_startup(self):
        self.__thing = self.client.create_thing(self.thing_lid)
        with self.__thing.get_meta() as meta:
            meta.set_label(self.thing_label)
            meta.set_description(self.thing_description)
            if self.thing_location:
                meta.set_location(*self.thing_location)  # pylint: disable=not-an-iterable
            else:
                meta.delete_location()

        self.__thing.create_tag(self.thing_tags)

        self.__thing.set_public(self.thing_public)

        self.client.register_callback_subscribed(self.__cb_subscribed)  # I've been subscribed to something

        self.__find_and_bind("HVAC")

    def main(self):
        # loop indefinitely until shutdown
        while True:
            logger.debug('main loop')

            # better than using time.sleep() as this will break immediately
            if self.wait_for_shutdown(1):
                return

    # Things I am subscribed to - remote Feeds I am following, remote Controls I am attached to
    def __cb_subscribed(self, arg):
        if isinstance(arg, RemoteFeed):
            logger.info("example_demo_device: Subscribed to a new remote Feed")
            rm_feed_info = self.client.describe(arg)
            logger.debug("remote describe %s", rm_feed_info)
            if not rm_feed_info['meta']['values']:  # Not a public feed or feed has no values
                logger.info("example_demo_device: Following known Feed")
                self.__thing.follow(arg.guid, callback=self.__known_feed_callback)
            else:
                logger.info("example_demo_device: Following public or owned Feed")
                self.__thing.follow(arg.guid, callback_parsed=self.__public_feed_callback_parsed)

    def __find_and_bind(self, search_text):
        thing_list = self.client.list(all_my_agents=True)
        for thing_name in thing_list:
            if search_text in thing_name:
                try:
                    self.__thing.follow((thing_name, KEY_FEED_NAME), callback=self.__known_feed_callback)
                except IOTUnknown:
                    logger.warning("trying to follow unknown device thing: %s, feed %s", thing_name, KEY_FEED_NAME)

    @staticmethod
    def __known_feed_callback(args):
        try:
            hvac_id = args[KEY_DATA][KEY_ID]
            temp = args[KEY_DATA][KEY_TEMP]
            power = args[KEY_DATA][KEY_POWER]
            logger.info('HVAC %.d: Temperature: %.d C, Power: %.d', hvac_id, temp, power)
        except KeyError:
            logger.warning('Id, Temperature or power not found in followed feed')

    @staticmethod
    def __public_feed_callback_parsed(args):
        hvac_id = -1
        for value in args[KEY_PARSED].filter_by(text=["HVAC", "hvac", "Id", "number"]):
            logger.debug('HVAC text found in value %s', value.label)
            hvac_id = value.value
            break
        if hvac_id == -1:
            logger.debug('HVAC id not found, ignoring')

        temp = None
        for value in args[KEY_PARSED].filter_by(units=[Units.CELSIUS]):
            logger.debug('Temperature found in value %s', value.label)
            temp = value.value
            break
        if temp is None:
            logger.debug('Temperature not found, ignoring')

        power = None
        for value in args[KEY_PARSED].filter_by(units=[Units.WATT]):
            logger.debug('Power found in value %s', value.label)
            power = value.value
            break
        if power is None:
            logger.debug('Power not found, ignoring')

        if temp is not None and power is not None:  # it's an HVAC
            logger.info('HVAC %.d: Temperature: %.d C, Power: %.d', hvac_id, temp, power)
        else:
            # Find a number in the feed data
            number = None
            for value in args[KEY_PARSED].filter_by(
                    types=[Datatypes.DOUBLE, Datatypes.INTEGER, Datatypes.INT, Datatypes.DECIMAL]):
                logger.debug('Number found %s', value.label)
                number = value.value
                break
            if number is None:
                logger.debug('Number not found, ignoring')
            else:
                logger.info('External temperature: %d', number)


def in_background(runner):
    runner.run(background=True)
    try:
        while True:
            logger.debug('Runner-unrelated action goes here')
            sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        runner.stop()


def main():
    runner = DemoThing(config='isc2_followall.ini')
    in_background(runner)


if __name__ == "__main__":
    main()
