import io
import json
from contextlib import redirect_stdout

from cybersentinel.cli import main


def test_cli_direct_analysis_mode() -> None:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exit_code = main(
            [
                "--source",
                "github",
                "--query",
                "acme leak",
                "--raw-text",
                "BEGIN RSA PRIVATE KEY",
            ]
        )

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["verdict"]["severity"] == "CRITICAL"
