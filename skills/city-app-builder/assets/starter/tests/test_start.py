"""A preview must belong to the launched app, even when another app is running."""

import socket
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import start


class StartupTests(unittest.TestCase):
    def response(self, identity):
        response = MagicMock()
        response.status = 200
        response.read.return_value = (
            "<title>Budget Explorer</title>"
            f'<meta content="{identity}" name="storyboard-preview-id" />'
        ).encode()
        response.__enter__.return_value = response
        return response

    def test_occupied_port_gets_another_port_without_stopping_listener(self):
        with socket.socket() as existing:
            existing.bind(("127.0.0.1", 0))
            existing.listen()
            occupied = existing.getsockname()[1]
            self.assertNotEqual(start.choose_port(occupied), occupied)
            with socket.create_connection(("127.0.0.1", occupied), timeout=1):
                pass

    def test_ready_response_requires_this_launch_identity(self):
        process = MagicMock()
        process.poll.return_value = None
        with patch.object(start, "urlopen", return_value=self.response("new-app")):
            start.wait_for_preview(process, "http://127.0.0.1:1234", "new-app")
        with (
            patch.object(start, "urlopen", return_value=self.response("older-app")),
            self.assertRaisesRegex(RuntimeError, "unverified app"),
        ):
            start.wait_for_preview(process, "http://127.0.0.1:1234", "new-app")

    def test_dead_child_cannot_validate_an_existing_server(self):
        process = MagicMock()
        process.poll.return_value = 1
        with (
            patch.object(start, "urlopen") as read,
            self.assertRaisesRegex(RuntimeError, "server exited"),
        ):
            start.wait_for_preview(process, "http://127.0.0.1:1234", "new-app")
        read.assert_not_called()

    def test_failed_preview_stops_only_the_child_it_started(self):
        child = MagicMock()
        child.poll.return_value = None
        with (
            patch.object(start, "choose_port", return_value=1234),
            patch.object(start.subprocess, "Popen", return_value=child) as spawn,
            patch.object(
                start, "wait_for_preview", side_effect=RuntimeError("wrong app")
            ),
            self.assertRaises(RuntimeError),
        ):
            start.start_server(Path("python"), Path("new-app"))
        self.assertEqual(spawn.call_args.kwargs["cwd"], Path("new-app"))
        self.assertTrue(spawn.call_args.kwargs["env"]["STORYBOARD_PREVIEW_ID"])
        child.terminate.assert_called_once()
        child.wait.assert_called_once()


if __name__ == "__main__":
    unittest.main()
