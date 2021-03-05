import unittest
from unittest.mock import MagicMock, patch

from json import dumps, load
import psutil
import os

import main
# Mock commandline arguments
from optparse import Values

class TestProcessNetcat(unittest.TestCase):
    def setUp(self):
        global main
        options = Values({"client": "127.0.0.1", "port": 1876, "whitelist": None,
            "send": None, "file": "tasks.json"})
        self.pn = main.ProcessNetcat(options)
        self.pn.transport = Values() # Fake being connected
        self.pn.transport.write = lambda x: x # Fake send command
        self.pn.addr = Values()
        self.pn.addr.host = "MockTestHost"
        main.log = lambda x: None # Don't print anything

    def test_parse_hello(self):
        self.assertIsNone(self.pn.parse({"type": "hello"})) # No send var

    def test_parse_hello_fail(self):
        self.pn.send_err = MagicMock()
        self.pn.options.send = True
        self.pn.parse({"type": "hello", "send": True}) # Both parties sending
        self.pn.send_err.assert_called_once()

        self.pn.send_err = MagicMock()
        self.pn.options.send = False
        self.pn.parse({"type": "hello", "send": False}) # Neither party sending
        self.pn.send_err.assert_called_once()

    def test_parse_hello_pass(self):
        self.pn.options.send = False
        self.pn.send_ok = MagicMock()
        self.pn.parse({"type": "hello", "send": True}) # They are sending
        self.pn.send_ok.assert_called_once()

        self.pn.send_ok = MagicMock()
        self.pn.options.send = True
        self.pn.parse({"type": "hello", "send": False}) # We are sending
        self.pn.send_ok.assert_called_once()

    def test_parse_tasks(self):
        self.pn.store_tasks = MagicMock()
        self.pn.parse({"type": "tasks", "tasks": {}}) # Storing tasks
        self.pn.store_tasks.assert_called_once()

    def test_parse_err(self):
        self.assertIsNone(self.pn.parse({"type": "err"})) # No msg var

        self.pn.parse({"type": "err", "msg": "Test"}) # Let's just check if it doesn't crash

    def test_parse_ok(self):
        self.pn.options.send = True
        self.pn.send_tasks = MagicMock()
        self.pn.parse({"type": "ok"}) # Other party says OK
        self.pn.send_tasks.assert_called_once()

    def test_dataReceived(self): # Test the fancy multiple line simultaneous parser
        self.pn.parse = MagicMock()
        dict1 = {"type": "hello", "send": True}
        dict2 = {"test": "test"}
        payload1 = dumps(dict1).encode("utf-8")
        payload2 = dumps(dict2).encode("utf-8")
        payload = payload1+b"\r\n"+payload2
        self.pn.dataReceived(payload)
        self.pn.parse.called_with({"type": "hello", "send": True})
        self.pn.parse.called_with({"test": "test"})

    def test_say(self):
        self.pn.transport.write = MagicMock()
        self.pn.say("hello")
        self.pn.transport.write.assert_called_once_with(b"hello\r\n")

    def test_send_hello(self):
        self.pn.options.send = True
        self.pn.transport.write = MagicMock()
        self.pn.send_hello()
        self.pn.transport.write.assert_called_once_with(b'{"type": "hello", "send": true}\r\n')

        self.pn.options.send = False
        self.pn.transport.write = MagicMock()
        self.pn.send_hello()
        self.pn.transport.write.assert_called_once_with(b'{"type": "hello", "send": false}\r\n')
        
    def test_send_ok(self):
        self.pn.transport.write = MagicMock()
        self.pn.send_ok()
        self.pn.transport.write.assert_called_once_with(b'{"type": "ok"}\r\n')

    def test_send_err(self):
        self.pn.transport.write = MagicMock()
        self.pn.send_err("err")
        self.pn.transport.write.assert_called_once_with(b'{"type": "err", "msg": "err"}\r\n')

    def test_send_tasks(self): # Compare task output
        self.pn.get_tasks = lambda: {"1": {"name": "init", "username": "root"}}
        self.pn.transport.write = MagicMock()
        self.pn._send_tasks()
        self.pn.transport.write.assert_called_once_with(b'{"type": "tasks", "tasks": {"1": {"name": "init", "username": "root"}}}\r\n')

    def test_store_tasks(self): # Test storing tasks, then load and compare with what we stored
        self.pn.get_tasks = lambda: {"1": {"name": "init", "username": "root"}}
        self.pn.options.file = "_tasks.test.json"
        self.pn.store_tasks(self.pn.get_tasks())

        with open(self.pn.options.file, "r") as f:
            data = load(f)
        os.remove(self.pn.options.file) # Clean up our temporary file
        self.assertEqual(data, self.pn.get_tasks())

if __name__ == "__main__":
    unittest.main()


