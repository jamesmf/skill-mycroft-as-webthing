# The MIT License (MIT)
# Copyright (c) 2019 jamesmf
from __future__ import division
from adapt.intent import IntentBuilder
from mycroft.skills.core import MycroftSkill, intent_handler
from mycroft.util.log import LOG
from webthing import Action, Event, Property, SingleThing, Thing, Value, WebThingServer
from mycroft.messagebus.message import Message
import asyncio
import logging
import time
import uuid


class QuestionAction(Action):
    """
    This action sends questions to Mycroft. It can be accessed through the
    Mozilla IoT Gateway
    """

    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, "question", input_=input_)

    def perform_action(self):
        print(self.input)
        self.thing.client.emit(
            Message("question:query", data={"phrase": self.input["query"]})
        )


class SpeakEvent(Event):
    """
    The SpeakEvents will show up in the gateway's logs and will briefly
    appear as a notifiaction on the UI.
    """

    def __init__(self, thing, data):
        Event.__init__(self, thing, "mycroftsaid", data=data)


class MycroftAsWoTSkill(MycroftSkill):
    def __init__(self):
        super(MycroftAsWoTSkill, self).__init__(name="MIoTSkill")
        self.thing = self.make_thing()
        self.server = None
        self.server_running = False

    def initialize(self):
        self.define_server()

    def define_server(self):

        # define the function that handles a message
        def print_utterance(message):
            # if they asked a question, we'll get an answer
            if message.data.get("answer") is not None:
                print('Mycroft said "{}"'.format(message.data.get("answer")))
                self.thing.add_event(SpeakEvent(self.thing, message.data.get("answer")))
            else:
                # otherwise just look for utterances
                if "utterance" in message.data:
                    print('Mycroft said "{}"'.format(message.data["utterance"]))
                    self.thing.add_event(
                        SpeakEvent(self.thing, data=message.data["utterance"])
                    )

        # watch for utterances and query responses
        self.bus.on("question:query.response", print_utterance)
        self.bus.on("speak", print_utterance)

        # this is not working; it works when run by itself on port 8888,
        # but here we need to use a different port. More importantly,
        # we can't start the WebThingServer here. If we define a new event_loop,
        # Mycroft hangs on skill initialization. If we don't, there's no loop
        # so we get an error and the server is useless.
        self.server = WebThingServer(SingleThing(self.thing), port=9191)
        # asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            self.server.start()
        except KeyboardInterrupt:
            self.server.stop()

    def make_thing(self):
        # define the Mycroft as a Thing
        thing = Thing(
            "test:mycroft:mycroft-hook-1234", "Mycroft", [], "A controller for Mycroft"
        )
        # Defining this action makes it availabe in the gateway
        thing.add_available_action(
            "question",
            {
                "title": "Question",
                "description": "Send a query to Mycroft",
                "input": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {"query": {"type": "string"}},
                },
            },
            QuestionAction,
        )
        # these events will pop up in the UI when they are emitted
        thing.add_available_event(
            "mycroftsaid", {"description": "Mycroft Said:", "type": "string"}
        )

        return thing


def create_skill():
    return MycroftAsWoTSkill()
