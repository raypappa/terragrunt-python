from pathlib import Path

import pytest

from terragrunt.errors import TerragruntError
from terragrunt.models import OutputMode
from terragrunt.runner import Runner


def test_runner_captures_output() -> None:
    result = Runner("printf", output_mode=OutputMode.CAPTURE).run(("hello",))

    assert result.stdout == "hello"
    assert result.succeeded


def test_runner_streams_output(tmp_path: Path) -> None:
    output_path = tmp_path / "stdout.txt"
    with output_path.open("w+") as output:
        result = Runner("printf", stdout=output).run(("hello",))

    assert result.stdout == ""
    assert output_path.read_text() == "hello"


def test_runner_raises_with_result() -> None:
    with pytest.raises(TerragruntError) as caught:
        Runner("sh", output_mode=OutputMode.CAPTURE).run(("-c", "printf failure >&2; exit 3"))

    assert caught.value.resp is not None
    assert caught.value.resp.returncode == 3
    assert caught.value.resp.stderr == "failure"
