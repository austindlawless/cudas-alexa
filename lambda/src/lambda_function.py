
from __future__ import print_function

import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key

# --------------- Globals ------------------------------------------------------

NOT_UNDERSTOOD = "Charlie says what now? "

WELCOME_MESSAGE = "Welcome to the Cudas Alexa Skill. Find out when the Cudas next play by asking me. "

RE_WELCOME_MESSAGE = "Try asking, when do the Cudas play next? Or, should I stack on Sacko?"

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


def get_current_season():
    seasons_table = boto3.resource('dynamodb').Table('cudas_schedule')
    current_season = seasons_table.scan(
        FilterExpression=Key('currentSeason').eq(True)
    )['Items'][0]
    print("season_id=" + current_season['season'])
    print("season_currentSeason=" + str(current_season['currentSeason']))
    return current_season


def get_next_game_datetime_from(current_season):
    print("Getting next game from current season.")
    next_game_datetime = None
    current_date = datetime.today()
    print("Current datetime=" + str(current_date))
    games = current_season['games']
    for game in games:
        print("Checking game with date=" + game['date'])
        status = game['status']
        print("Status=" + status)
        if status is not None and status == "upcoming":
            game_datetime = datetime_from_game(game)
            if current_date < game_datetime and (next_game_datetime is None or game_datetime < next_game_datetime):
                print("updating next_game_datetime to " + str(game_datetime))
                next_game_datetime = game_datetime
    return next_game_datetime


def datetime_from_game(game):
    return datetime.strptime(game['date'] + "-" + game['time'] + "m", "%m-%d-%Y-%I:%M%p")


def get_next_game_text():
    next_game_datetime = get_next_game_datetime_from(get_current_season())
    if next_game_datetime is None:
        return "I don't see a next game on the calendar."
    else:
        return "The next game is on " + next_game_datetime.strftime("%A, %B %d at %I:%M%p")


def get_next_game_response():
    card_title = "Cudas: Next Game"
    session_attributes = {}
    should_end_session = True
    speech_output = get_next_game_text()
    reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session
    ))


def get_stack_sacko_response():
    card_title = "Cudas: Don't you stack on Sacko"
    session_attributes = {}
    should_end_session = True
    speech_output = "Don't you stack on Sacko!"
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
        return get_next_game_response()
    elif intent_name == "StackSacko":
        return get_stack_sacko_response()
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
