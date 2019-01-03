# -*- coding: utf-8 -*-

import random
import logging
import requests
import json
import hashlib

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

SKILL_NAME = 'Switch Game or Not'
sb = StandardSkillBuilder(table_name="Switch-Game-or-Not", auto_create_table=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
        "Welcome to Switch Game or Not. You have played {} times. "
        "Would you like to play?".format(attr["games_played"]))
    reprompt = "Say yes to start the game or no to quit."

    handler_input.response_builder.speak(speech_text).ask(reprompt)
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    """Handler for Help Intent."""
    # type: (HandlerInput) -> Response
    speech_text = (
        "I've give you two names which may or may not be real games released "
        "for the Nintendo Switch. You need to guess which is fake, or, guess "
        "that neither is fake or both are fake.")
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
    speech_text = "Thanks for playing! Check us out online at Switch Game or Not dot Com"

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


@sb.request_handler(can_handle_func=lambda input:
not currently_playing(input) and
is_intent_name("AMAZON.YesIntent")(input))
def yes_handler(handler_input):
    """Handler for Yes Intent, only if the player said yes for
    a new game.
    """
    # type: (HandlerInput) -> Response
    api_call = requests.get('http://switchgameornot.com/api/alexa/')
    games = json.loads(api_call.content.decode("utf-8"))
    real_games = [g['real'] for g in games]
    correct_answer = 0
    if real_games[0] == 1 and real_games[1] == 0:
        correct_answer = 2
    elif real_games[0] == 0 and real_games[1] == 1:
        correct_answer = 1
    elif real_games[0] == 1 and real_games[1] == 1:
        correct_answer = 4
    elif real_games[0] == 0 and real_games[1] == 0:
        correct_answer = 3

    session_attr = handler_input.attributes_manager.session_attributes
    session_attr['game_state'] = "STARTED"
    session_attr['games'] = games
    session_attr['correct_answer'] = correct_answer

    speech_text = (
            "Here are two games. First game: " + games[0]['game'] + ". "
            "Second game: " + games[1]['game'] + ". "
            "Say 1 if you think the first game is fake, "
            "2 if you think the second game is fake, "
            "3 if you think they're both fake or "
            "4 if you think neither is fake.")
    reprompt = "First game: " + games[0]['game'] + ". Second game: " + games[1]['game']

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

    speech_text = "Ok. Check us out online at Switch Game or Not dot com"

    handler_input.response_builder.speak(speech_text)
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
    step1 = handler_input.__dict__
    step2 = step1['request_envelope'].__dict__
    step3 = step2['session'].__dict__
    step4 = step3['user'].__dict__
    uuid = hashlib.md5(step4['user_id'].encode('utf-8')).hexdigest()
    guess_num = int(handler_input.request_envelope.request.intent.slots[
                        "number"].value)
    
    answers = [1, 1]
    if(guess_num == 1):
        answers = [0, 1]
    elif(guess_num == 2):
        answers = [1, 0]
    elif(guess_num == 3):
        answers = [0, 0]
    correct1 = int(answers[0] == games[0]['real'])
    correct2 = int(answers[1] == games[1]['real'])
    game1 = {
        "week_id": 9999,
        "game_id": games[0]['game_id'],
        "user_id": uuid,
        "correct": correct1
    }
    game2 = {
        "week_id": 9999,
        "game_id": games[1]['game_id'],
        "user_id": uuid,
        "correct": correct2
    }
    print("DATA TO POST:")
    print(game1)
    print(game2)

    wrong_buzz = ['Oh, Snap!', 'Gotcha!', 'BUZZ!', 'Nailed it! Just kidding, you blew it.',
                  'Nope!', 'Tricked you!', 'No way!']
    right_buzz = ['Wow!!', 'Congratulations!', 'BUZZ! Just kidding, you got it!', 'Nailed it!',
                  'Yup!', 'Are you clairvoyant?', "I'm not going to bet money against you!"]
    
    if guess_num > 4 or guess_num < 1:
        speech_text = (
                "Sorry, I didn't get that."
                "First game: " + games[0]['game'] + ". "
                "Second game: " + games[1]['game'] + ". "
                "Say 1 if you think the first game is fake, "
                "2 if you think the second game is fake, "
                "3 if you think they're both fake or "
                "4 if you think neither is fake.")
    elif guess_num != target_num:
        speech_text = random.choice(wrong_buzz)
        if target_num < 3:
            speech_text += ' Actually, {} is the only fake game.'.format(games[target_num - 1]['game'])
        elif target_num == 3:
            speech_text += ' Can you believe both {} and {} are fake?'.format(games[0]['game'], games[1]['game'])
        else:
            speech_text += ' Switch game names are so crazy, even two real games sound fake.'
        speech_text += " Your score is {}. Would you like to play a new game?".format(session_attr['score'])
        _ = requests.post(url = 'http://switchgameornot.com/api/alexa/', data = game1)
        _ = requests.post(url = 'http://switchgameornot.com/api/alexa/', data = game2)
    elif guess_num == target_num:
        session_attr['score'] += 1
        speech_text = random.choice(right_buzz)
        if target_num < 3:
            speech_text += ' {} was the fake game. Your score is {}'.format(games[target_num - 1]['game'],
                                                                            session_attr['score'])
        elif target_num == 3:
            speech_text = ' Both {} and {} are fake games. Your score is {}'.format(games[0]['game'], games[1]['game'],
                                                                                    session_attr['score'])
        else:
            speech_text = ' Both {} and {} are real games. Your score is {}'.format(games[0]['game'], games[1]['game'],
                                                                                    session_attr['score'])
        speech_text += " Would you like to play a new game?"
        _ = requests.post(url = 'http://switchgameornot.com/api/alexa/', data = game1)
        _ = requests.post(url = 'http://switchgameornot.com/api/alexa/', data = game2)
    else:
        speech_text = (
                "Sorry, I didn't get that."
                "First game: " + games[0]['game'] + ". "
                "Second game: " + games[1]['game'] + ". "
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
