# -*- coding: utf-8 -*-

import random
import logging
import requests
import json
import hashlib
import re

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

SKILL_NAME = 'Switch Game or Not'
sb = StandardSkillBuilder(table_name="Switch-Game-or-Not", auto_create_table=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

with open('real_games.txt') as w:
    real_games = w.readlines()
with open('fake_games.txt') as w:
    fake_games = w.readlines()


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input):
    """Handler for Skill Launch.

    Get the persistence attributes, to figure out the game state.
    """
    # type: (HandlerInput) -> Response
    attr = handler_input.attributes_manager.persistent_attributes
    if not attr:
        attr['ended_session_count'] = 0
        attr['games_played'] = 0
        attr['score'] = 0
        attr['game_state'] = 'ENDED'

    handler_input.attributes_manager.session_attributes = attr

    speech_text = (
        "Welcome to Switch Game or Not. If you need a reminder of how to play, just say 'help'. "
        "Are you ready to play?".format(attr["games_played"]))
    reprompt = "Say yes to start the game or no to quit."

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = (
        "I've given you two names which may or may not be real games released "
        "for the Nintendo Switch. "
        "Say 1 if you think the first game is fake, "
        "2 if you think the second game is fake, "
        "3 if you think they're both fake or "
        "4 if you think neither is fake."
    )
    reprompt = "Pick a response, 1, 2, 3 or 4."

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
    is_intent_name("AMAZON.CancelIntent")(input) or
    is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    """Single handler for Cancel and Stop Intent."""
    # type: (HandlerInput) -> Response
    speech_text = "Thanks for playing! Check us out online at Switch Game or Not dot Com!"

    handler_input.response_builder.speak(
        speech_text).set_should_end_session(True)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    """Handler for Session End."""
    # type: (HandlerInput) -> Response
    logger.info(
        "Session ended with reason: {}".format(
            handler_input.request_envelope.request.reason))
    return handler_input.response_builder.response


def currently_playing(handler_input):
    """Function that acts as can handle for game state."""
    # type: (HandlerInput) -> bool
    is_currently_playing = False
    session_attr = handler_input.attributes_manager.session_attributes

    if ("game_state" in session_attr
            and session_attr['game_state'] == "STARTED"):
        is_currently_playing = True

    return is_currently_playing


def get_games(right_answer):
    if right_answer in [1, 3]:
        game1 = random.sample(fake_games, 1)
    else:
        game1 = random.sample(real_games, 1)
    game2 = game1
    while game2 == game1:
        if right_answer in [2, 3]:
            game2 = random.sample(fake_games, 1)
        else:
            game2 = random.sample(real_games, 1)
    return [re.sub('\n', '', x) for x in [game1[0], game2[0]]]


@sb.request_handler(can_handle_func=lambda input:
not currently_playing(input) and
is_intent_name("AMAZON.YesIntent")(input))
def yes_handler(handler_input):
    """Handler for Yes Intent, only if the player said yes for
    a new game.
    """
    # type: (HandlerInput) -> Response
    right_answer = random.sample([1, 4], 1)[0]
    games = get_games(right_answer)

    session_attr = handler_input.attributes_manager.session_attributes    
    session_attr['game_state'] = "STARTED"
    session_attr['games'] = games
    session_attr['correct_answer'] = right_answer

    speech_text = (
            "Here are two games. First game: <break time='500ms'/>" + games[0] + ". <break time='500ms'/>"
            "Second game: <break time='500ms'/>" + games[1] + ". <break time='500ms'/>"
            )
    
    if session_attr['games_played'] == 0:
        speech_text += (" Say 1 if you think the first game is fake, "
                        "2 if you think the second game is fake, "
                        "3 if you think they're both fake or "
                        "4 if you think neither is fake. ")
    
    reprompt = "First game: <break time='500ms'/>" + games[0] + ". Second game: <break time='500ms'/>" + games[1]

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input:
not currently_playing(input) and
is_intent_name("AMAZON.NoIntent")(input))
def no_handler(handler_input):
    """Handler for No Intent, only if the player said no for
    a new game.
    """
    # type: (HandlerInput) -> Response
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr['game_state'] = "ENDED"
    session_attr['ended_session_count'] += 1

    handler_input.attributes_manager.persistent_attributes = session_attr
    handler_input.attributes_manager.save_persistent_attributes()

    speech_text = "Thanks for playing!"

    handler_input.response_builder.speak(speech_text)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input:
currently_playing(input) and
is_intent_name("RepeatGameIntent")(input))
def repeat_request_handler(handler_input):
    """Handler for Repeating game names."""
    # type: (HandlerInput) -> Response
    session_attr = handler_input.attributes_manager.session_attributes
    games = session_attr['games']
    try:
        val = int(handler_input.request_envelope.request.intent.slots["GameOrder"].value)
        if val == 1:
            speech_text = "First game: <break time='500ms'/>{game1}"
        else:
            speech_text = "Second game: <break time='500ms'/>{game2}"
    except:
        speech_text = "First game: <break time='500ms'/>{game1}<break time='500ms'/>. Second Game: <break time='500ms'/>{game2}<break time='500ms'/>."
    speech_text = speech_text.format(game1=games[0],
                                     game2=games[1])
    reprompt = speech_text
    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input:
currently_playing(input) and
is_intent_name("NumberGuessIntent")(input))
def number_guess_handler(handler_input):
    """Handler for processing guess with target."""
    # type: (HandlerInput) -> Response
    session_attr = handler_input.attributes_manager.session_attributes
    target_num = session_attr["correct_answer"]
    games = session_attr['games']
    guess_num = int(handler_input.request_envelope.request.intent.slots[
                        "number"].value)
    print("GUESSED A NUMBER!!! "+str(guess_num))
    print("TARGET IS... {}".format(target_num))

    wrong_buzz = ['Oh, Snap!', 'Gotcha!', 'BUZZ!', 'Nailed it! Just kidding, you blew it.',
                  'Nope!', 'Tricked you!', 'No way!']
    right_buzz = ['Wow!!', 'Congratulations!', 'BUZZ! Just kidding, you got it!', 'Nailed it!',
                  'Yup!', 'Are you clairvoyant?', "I'm not going to bet money against you!"]
    
    if guess_num > 4 or guess_num < 1:
        speech_text = (
                "Sorry, I didn't get that."
                "First game: <break time='500ms'/>" + games[0] + "<break time='500ms'/>. "
                "Second game: <break time='500ms'/>" + games[1] + "<break time='500ms'/>. "
                "Say 1 if you think the first game is fake, "
                "2 if you think the second game is fake, "
                "3 if you think they're both fake or "
                "4 if you think neither is fake.")
    elif guess_num != target_num:
        speech_text = random.choice(wrong_buzz)
        if target_num < 3:
            speech_text += ' Actually, <break time="500ms"/> {} <break time="500ms"/> ' \
                           'is the only fake game.'.format(games[target_num - 1])
        elif target_num == 3:
            speech_text += ' Can you believe both <break time="500ms"/> {} <break time="500ms"/> and ' \
                           '<break time="500ms"/> {} <break time="500ms"/> ' \
                           'are fake?'.format(games[0], games[1])
        else:
            speech_text += ' Switch game names are so crazy, even two real games sound fake.'
        speech_text += " Would you like to play a new game?"
    elif guess_num == target_num:
        session_attr['score'] += 1
        speech_text = random.choice(right_buzz)
        if target_num < 3:
            speech_text += ' <break time="500ms"/> {} <break time="500ms"/> was the fake game. ' \
                           'Your score is {}'.format(games[target_num - 1], session_attr['score'])
        elif target_num == 3:
            speech_text += ' Both <break time="500ms"/> {} <break time="500ms"/> and <break time="500ms"/> {} ' \
                           '<break time="500ms"/> are fake games. ' \
                           'Your score is {}'.format(games[0], games[1], session_attr['score'])
        else:
            speech_text += ' Both <break time="500ms"/> {} <break time="500ms"/> and <break time="500ms"/> {} ' \
                           '<break time="500ms"/> are real games. ' \
                           'Your score is {}'.format(games[0], games[1], session_attr['score'])
        speech_text += " Would you like to play a new game?"
    else:
        speech_text = (
                "Sorry, I didn't get that."
                "First game: " + games[0] + ". "
                "Second game: " + games[1] + ". "
                "Say 1 if you think the first game is fake, "
                "2 if you think the second game is fake, "
                "3 if you think they're both fake or "
                "4 if you think neither is fake.")

    reprompt = "Say yes to start a new game or no to end the game"
    session_attr["games_played"] += 1
    session_attr["game_state"] = "ENDED"

    handler_input.attributes_manager.persistent_attributes = session_attr
    handler_input.attributes_manager.save_persistent_attributes()

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input:
is_intent_name("AMAZON.FallbackIntent")(input) or
is_intent_name("AMAZON.YesIntent")(input) or
is_intent_name("AMAZON.NoIntent")(input))
def fallback_handler(handler_input):
    """AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """
    # type: (HandlerInput) -> Response
    session_attr = handler_input.attributes_manager.session_attributes

    if ("game_state" in session_attr and
            session_attr["game_state"] == "STARTED"):
        speech_text = (
            "The {} skill can't help you with that.  "
            "Try picking out the fake switch game name.".format(SKILL_NAME))
        reprompt = (
            "Pick out the fake game, either 1 or 2. If you think they're both fake, "
            "say 3. If you think they're both real, say 4.")
    else:
        speech_text = (
            "The {} skill can't help you with that.  "
            "It presents two possible Switch game names and "
            "you try to guess which is fake, or if both are fake or both are real. "
            "Would you like to play?".format(SKILL_NAME))
        reprompt = "Say yes to start the game or no to quit."

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=lambda input: True)
def unhandled_intent_handler(handler_input):
    """Handler for all other unhandled requests."""
    # type: (HandlerInput) -> Response
    speech = "Say yes to continue or no to end the game!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    """Catch all exception handler, log exception and
    respond with custom message.
    """
    # type: (HandlerInput, Exception) -> Response
    logger.error(exception, exc_info=True)
    speech = "Sorry, I can't understand that. Please say again!!"
    handler_input.response_builder.speak(speech).ask(speech)
    return handler_input.response_builder.response


@sb.global_response_interceptor()
def log_response(handler_input, response):
    """Response logger."""
    # type: (HandlerInput, Response) -> None
    logger.info("Response: {}".format(response))


lambda_handler = sb.lambda_handler()
