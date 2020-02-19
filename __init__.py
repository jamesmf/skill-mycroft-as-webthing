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
    def __init__(self, thing, input_):
        Action.__init__(self, uuid.uuid4().hex, thing, "question", input_=input_)

    def perform_action(self):
        print(self.input)
        self.thing.client.emit(
            Message("question:query", data={"phrase": self.input["query"]})
        )


class SpeakEvent(Event):
    def __init__(self, thing, data):
        Event.__init__(self, thing, "mycroftsaid", data=data)


class MycroftAsWoTSkill(MycroftSkill):

    # The constructor of the skill, which calls MycroftSkill's constructor
    def __init__(self):
        super(MycroftAsWoTSkill, self).__init__(name="RasaSkill")
        self.thing = self.make_thing()
        self.server = None
        self.server_running = False

    def initialize(self):
        self.define_server()

    def define_server(self):
        def print_utterance(message):
            if message.data.get("answer") is not None:
                print('Mycroft said "{}"'.format(message.data.get("answer")))
                self.thing.add_event(SpeakEvent(self.thing, message.data.get("answer")))
            else:
                if "utterance" in message.data:
                    print('Mycroft said "{}"'.format(message.data["utterance"]))
                    self.thing.add_event(
                        SpeakEvent(self.thing, data=message.data["utterance"])
                    )

        self.bus.on("question:query.response", print_utterance)
        self.bus.on("speak", print_utterance)

        # If adding more than one thing, use MultipleThings() with a name.
        # In the single thing case, the thing's name will be broadcast.
        self.server = WebThingServer(SingleThing(self.thing), port=9191)
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            self.server.start()
        except KeyboardInterrupt:
            self.server.stop()

    def make_thing(self):
        thing = Thing(
            "test:mycroft:mycroft-hook-1234", "Mycroft", [], "A controller for Mycroft"
        )
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
        thing.add_available_event(
            "mycroftsaid", {"description": "Mycroft Said:", "type": "string"}
        )

        return thing


def create_skill():
    return MycroftAsWoTSkill()
