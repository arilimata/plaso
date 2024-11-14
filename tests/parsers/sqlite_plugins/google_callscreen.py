# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google CallScreen database files."""

import json
from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class GoogleCallScreenEventData(events.EventData):
    """Android Google CallScreen event data.
    
    Attributes:
        conversation (str): text conversation from the CallScreen feature.
        audio_recording_file_path (str): path to the audio recording file.
        start_time (dfdatetime.DateTimeValues): timestamp of the event.
    """
    DATA_TYPE = 'android:google:callscreen'

    def __init__(self):
        """Initializes event data."""
        super(GoogleCallScreenEventData, self).__init__(data_type=self.DATA_TYPE)
        self.conversation = None
        self.audio_recording_file_path = None
        self.start_time = None


class GoogleCallScreenPlugin(interface.SQLitePlugin):
    """SQLite parser plugin for Google CallScreen database files."""

    NAME = 'google_callscreen'
    DATA_FORMAT = 'Google CallScreen database file'

    REQUIRED_STRUCTURE = {
        'Transcript': frozenset([
            'id', 'conversation', 'audioRecordingFilePath', 'AppId']),
    }

    QUERIES = [
        ('SELECT id AS timestamp, conversation, audioRecordingFilePath FROM Transcript', 
         'ParseCallsRow')
    ]

    SCHEMAS = [{
        'Transcript': (
            'CREATE TABLE Transcript (id TEXT NOT NULL, conversation BLOB, '
            'audioRecordingFilePath TEXT, isRated INTEGER NOT NULL, '
            'revelioCallType INTEGER, lastModifiedMillis INTEGER NOT NULL, '
            'callScreenFeedbackData BLOB, PRIMARY KEY(id))'),
        'android_metadata': (
            'CREATE TABLE android_metadata (locale TEXT)'),
        'room_master_table': (
            'CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)')
    }]

    def _GetDateTimeRowValue(self, query_hash, row, value_name):
        """Retrieves a date and time value from the row.

        Args:
            query_hash (int): hash of the query, that uniquely identifies the query
                that produced the row.
            row (sqlite3.Row): row.
            value_name (str): name of the value.

        Returns:
            dfdatetime.PosixTime: date and time value or None if not available.
        """
        timestamp = self._GetRowValue(query_hash, row, value_name)
        if timestamp is None:
            return None
        return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

    def ParseCallsRow(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a Google CallScreen row.

        Args:
            parser_mediator (ParserMediator): mediates interactions between parsers
                and other components, such as storage and dfVFS.
            query (str): query that created the row.
            row (sqlite3.Row): row.
        """
        query_hash = hash(query)

        # Convert the conversation BLOB data to a JSON object.
        conversation_json_bytes = bytes(self._GetRowValue(query_hash, row, 'conversation'))
        conversation_json_string = conversation_json_bytes.decode('utf-8')
        conversation_data = json.loads(conversation_json_string)

        # Extract relevant conversation text or metadata if available.
        conversation_text = conversation_data.get('convo_text', None)

        # Extract audio recording file path.
        audio_recording_file_path = self._GetRowValue(query_hash, row, 'audioRecordingFilePath')

        # Prepare the event data
        event_data = GoogleCallScreenEventData()
        event_data.conversation = conversation_text
        event_data.audio_recording_file_path = audio_recording_file_path
        event_data.start_time = self._GetDateTimeRowValue(query_hash, row, 'timestamp')

        # Produce the event data.
        parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(GoogleCallScreenPlugin)
