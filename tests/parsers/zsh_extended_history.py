#!/usr/bin/python
# -*_ coding: utf-8 -*-
"""Tests for the Zsh extended_history parser."""
import unittest

from plaso.lib import timelib
from plaso.parsers import zsh_extended_history
from tests.parsers import test_lib


class ZshExtendedHistoryTest(test_lib.ParserTestCase):
  """Tests for the Zsh extended_history parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = zsh_extended_history.ZshExtendedHistoryParser()

  def testParse(self):
    """Tests for the Parse method."""
    test_file = self._GetTestFilePath([u'zsh_extended_history.txt'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    self.assertEqual(len(event_objects), 4)

    event = event_objects[0]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-12 08:26:50')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.elapsed_seconds, 0)
    self.assertEqual(event.command, u'cd plaso')

    event = event_objects[2]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-26 11:54:53')
    expected_command = u'echo dfgdfg \\\\\n& touch /tmp/afile'
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(event.command, expected_command)

    event = event_objects[3]
    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2016-03-26 11:54:57')
    self.assertEqual(event.timestamp, expected_timestamp)

  def testVerification(self):
    """Tests for the VerifyStructure method"""
    mediator = None
    valid_lines = u': 1457771210:0;cd plaso'
    self.assertTrue(self._parser.VerifyStructure(mediator, valid_lines))

    invalid_lines = u': 2016-03-26 11:54:53;0;cd plaso'
    self.assertFalse(self._parser.VerifyStructure(mediator, invalid_lines))


if __name__ == '__main__':
  unittest.main()