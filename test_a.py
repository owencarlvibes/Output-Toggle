import io
import json
import tempfile
import unittest
from pathlib import Path

import a


class TodoCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.td = tempfile.TemporaryDirectory()
        self.data = Path(self.td.name) / "todos.json"

    def tearDown(self) -> None:
        self.td.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        code = a.run(["--data", str(self.data), *args], stdout=out, stderr=err)
        return code, out.getvalue(), err.getvalue()

    def test_add_and_list_open(self) -> None:
        code, out, err = self.run_cli("add", "buy", "milk")
        self.assertEqual(code, 0)
        self.assertIn("Added 1: buy milk", out)
        self.assertEqual(err, "")

        code, out, err = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("[ ] 1: buy milk", out)
        self.assertEqual(err, "")

    def test_done_filters(self) -> None:
        self.run_cli("add", "a")
        self.run_cli("add", "b")
        self.run_cli("done", "1")

        code, out, _ = self.run_cli("list")
        self.assertIn("[ ] 2: b", out)
        self.assertNotIn("1:", out)

        code, out, _ = self.run_cli("list", "--done")
        self.assertIn("[x] 1: a", out)
        self.assertNotIn("2:", out)

        code, out, _ = self.run_cli("list", "--all")
        self.assertIn("[x] 1: a", out)
        self.assertIn("[ ] 2: b", out)

    def test_json_output(self) -> None:
        self.run_cli("add", "hello")
        code, out, err = self.run_cli("list", "--json", "--all")
        self.assertEqual(code, 0)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 1)
        self.assertEqual(data[0]["text"], "hello")
        self.assertFalse(data[0]["done"])

    def test_rm_and_clear_done(self) -> None:
        self.run_cli("add", "x")
        self.run_cli("add", "y")
        self.run_cli("done", "1")

        code, out, err = self.run_cli("clear-done")
        self.assertEqual(code, 0)
        self.assertIn("Removed 1 completed todo(s).", out)
        self.assertEqual(err, "")

        code, out, err = self.run_cli("rm", "2")
        self.assertEqual(code, 0)
        self.assertIn("Removed 2: y", out)
        self.assertEqual(err, "")

    def test_error_on_missing_id(self) -> None:
        code, out, err = self.run_cli("done", "999")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("error: No todo with id 999", err)


if __name__ == "__main__":
    unittest.main()

