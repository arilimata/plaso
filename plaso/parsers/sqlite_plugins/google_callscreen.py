# -*- coding: utf-8 -*-
"""SQLite parser plugin for Google CallScreen database files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class WindowsTimelineUserEngagedEventData(events.EventData):
  """Android Google CallScreen data
  
  Attributes:
    active_duration_seconds (int): the number of seconds the user spent
        interacting with the program.
    package_identifier (str): the package ID or location of the executable
        the user interacted with.
    reporting_app (str): the name of the application that reported the user's
        interaction. This is the name of a monitoring tool, for example
        "ShellActivityMonitor".
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the activity.
  """

  DATA_TYPE = 'android:google:callscreen'

  def __init__(self):
    """Initialize event data."""
    super(WindowsTimelineUserEngagedEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.active_duration_seconds = None
    self.package_identifier = None
    self.reporting_app = None
    self.start_time = None


class WindowsTimelinePlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Windows 10 timeline database files.

  The Windows 10 timeline database file is typically stored in:
  %APPDATA%\\Local\\ConnectedDevicesPlatform\\L.<username>\\ActivitiesCache.db
  """

  NAME = 'google_callscreen'
  DATA_FORMAT = 'Google callscreen (callscreen_transcript) file'

  REQUIRED_STRUCTURE = {
      'Transcript': frozenset([
          'id', 'conversation', 'audioRecordingFilePath', 'AppId']),
      }

  QUERIES = [
      ('SELECT id as TimeStamp, conversation, audioRecordingFilePath FROM Transcript', 
       'ParseCallsRow')]

  SCHEMAS = [{
      'Transcript': (
					'CREATE TABLE Transcript (id TEXT NOT NULL, conversation BLOB, audioRecordingFilePath'
					'TEXT, isRated INTEGER NOT NULL, revelioCallType INTEGER, lastModifiedMillis' 
					'INTEGER NOT NULL, callScreenFeedbackData BLOB, PRIMARY KEY(id))'),
      'android_metadata': (
          'CREATE TABLE android_metadata (locale TEXT)'),
      'room_master_table': (
          'CREATE TABLE room_master_table (id INTEGER PRIMARY KEY,identity_hash TEXT)')}]

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
    """Parses a Google Call Screen row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    # Payload is JSON serialized as binary data in a BLOB field, with the text
    # encoded as UTF-8.
    conversation_json_bytes = bytes(self._GetRowValue(query_hash, row, 'conversation'))
    conversation_json_string = conversation_json_bytes.decode('utf-8')
    conversation = json.loads(conversation_json_string)

    application_display_name = conversation.get('convo_text', None)

    # AppId is JSON stored as unicode text.
    appid_entries_string = self._GetRowValue(query_hash, row, 'AppId')
    appid_entries = json.loads(appid_entries_string)

    package_identifier = None

    # Attempt to populate the package_identifier field by checking each of
    # these fields in the AppId JSON.
    package_id_locations = [
        'packageId', 'x_exe_path', 'windows_win32', 'windows_universal',
        'alternateId']
    for location in package_id_locations:
      for entry in appid_entries:
        if entry['platform'] == location and entry['application'] != '':
          package_identifier = entry['application']
          break
      if package_identifier is None:
        # package_identifier has been populated and we're done.
        break

    event_data = WindowsTimelineGenericEventData()
    event_data.application_display_name = application_display_name
    event_data.description = payload.get('description', None)
    event_data.package_identifier = package_identifier
    event_data.start_time = self._GetDateTimeRowValue(
        query_hash, row, 'StartTime')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(WindowsTimelinePlugin)
