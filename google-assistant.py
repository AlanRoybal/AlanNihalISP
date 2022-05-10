# Importing API and Libraries
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os.path
import json
from time import sleep

import RPi.GPIO as GPIO

import google.oauth2.credentials
from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file

PIN_BTN = 17
PIN_LED = 22
ASSISTANT = None

def callback(channel):
    global CREDENTIALS
    if not CREDENTIALS:
        return
    print("callback")
    assistant = Assistant(CREDENTIALS)
    ret = assistant.start_conversation()
    print(ret)

# Initializing connection to LEDs
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_BTN, GPIO.IN, GPIO.PUD_UP)
GPIO.setup(PIN_LED, GPIO.OUT)
GPIO.output(PIN_LED, GPIO.LOW)

# Remotely connecting to Google Assistant
def callback_start_conversation(channel):
    global ASSISTANT
    if not ASSISTANT:
        return
    ASSISTANT.start_conversation()

# Describing each possible event 
def process_event(event):
    # Clarifies that Google Assistant is connected and responding
    if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        print('Google Assistant is listening to you now.')
        GPIO.output(PIN_LED, GPIO.HIGH)
    # Response following user audio input
    if event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED:
        print("You:", event.args['text'])
    # Signaling that response has been received
    if event.type == EventType.ON_ALERT_STARTED:
        print('An alert has started sounding.')
    if event.type == EventType.ON_ALERT_FINISHED:
        print('The alert has finished sounding.')
    # Google Assistant has received response and is processing it
    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and event.args['with_follow_on_turn'] == True):
        #print('Google Assistant is listening to your response.')
        pass
    # In event of unclear statement
    if event.type == EventType.ON_END_OF_UTTERANCE:
        print('Google Assistant may not have understood what you has said')
    # Terminates interaction with Google Assistant
    if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
            event.args and event.args['with_follow_on_turn'] == False):
        print('Conversation finished.')
        GPIO.output(PIN_LED, GPIO.LOW)

def main():
    global ASSISTANT

    # Creates an argparse that states that argument is required
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)
    # Argument needed is the credentials for the API 
    parser.add_argument('--credentials', type=existing_file,
                        metavar='OAUTH2_CREDENTIALS_FILE',
                        default=os.path.join(
                            os.path.expanduser('~/.config'),
                            'google-oauthlib-tool',
                            'credentials.json'
                        ),
                        help='Path to store and read OAuth2 credentials')
    args = parser.parse_args()
    with open(args.credentials, 'r') as f:
        credentials = google.oauth2.credentials.Credentials(token=None,
                                                            **json.load(f))
    # Setting ASSISTANT to be the credential specific assistant
    ASSISTANT = Assistant(credentials)
    # When assistant is called upon wait 300 ms for response
    GPIO.add_event_detect(PIN_BTN, GPIO.FALLING,
                callback=callback_start_conversation, bouncetime=300)
    # If assistant is activated then process the request
    # Utilizes commands from the API
    # Events can be any action called for by the user; in our case it is changing the color of the lights
    for event in ASSISTANT.start():
        process_event(event)

    while True:
        pass

if __name__ == '__main__':
    try:
        main()
    # When event is finished clear the API request handler
    except KeyboardInterrupt:
        print("Google Assistant finised.")
        GPIO.cleanup()
