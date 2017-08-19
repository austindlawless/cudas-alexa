
from __future__ import print_function

import boto3
import random
from datetime import datetime

# --------------- Globals ------------------------------------------------------

NOT_UNDERSTOOD = "Charlie says what now? "

WELCOME_MESSAGE = "Welcome to the Cudas Alexa Skill. " \
                  "Find out when the Cudas next play by asking me. "

RE_WELCOME_MESSAGE = "Try asking, when do the Cudas play next? "

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_unknown_response():
    """ The standard response when we get an invalid prompt """
    session_attributes = {}
    card_title = "Hmm"
    speech_output = NOT_UNDERSTOOD + "" + WELCOME_MESSAGE
    reprompt_text = RE_WELCOME_MESSAGE
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session
    ))


def get_welcome_response():
    """ The standard welcome response """
    session_attributes = {}
    card_title = "Welcome"
    speech_output = WELCOME_MESSAGE
    reprompt_text = RE_WELCOME_MESSAGE
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for supporting the Cudas! " \
                    "Have a nice day!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def get_next_game():
    seasons_table = boto3.resource('dynamodb').Table('cudas_schedule')
    seasons = seasons_table.scan()['Items']
    season = seasons[0]
    games = season['games']
    game = games[0]
    return datetime.strptime(game['date'] + "-" + game['time'] + "m", "%m-%d-%Y-%I:%M%p")


def get_next_game_text():
    game_datetime = get_next_game()
    current_date = datetime.today()
    if current_date > game_datetime:
        return "I don't see a next game on the calendar."
    else:
        return "The next game is on " + str(game_datetime.date()) + " at " + str(game_datetime.time())


def get_random_note_response():
    card_title = "Cudas: Next Game"
    session_attributes = {}
    should_end_session = True
    speech_output = get_next_game_text()
    reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session
    ))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent_name = intent_request['intent']['name']

    print("intent_name=" + intent_name)

    # Dispatch to your skill's intent handlers
    if intent_name == "NextGame":
        return get_random_note_response()
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        return get_unknown_response()


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Prevent someone else from configuring a skill that sends requests to this
    function.
    """
    if (event['session']['application']['applicationId'] !=
            "amzn1.ask.skill.5ea15a2f-cee1-42f1-a689-b50aed8de3d0"):
        raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        print("LaunchRequest")
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        print("IntentRequest")
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        print("SessionEndedRequest")
        return on_session_ended(event['request'], event['session'])
