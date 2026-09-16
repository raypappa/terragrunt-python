from .models import CommandResult


class TerragruntError(RuntimeError):
    def __init__(self, message: str, resp: CommandResult | None = None) -> None:
        super().__init__(message)
        self.resp = resp


class TerragruntVersionError(TerragruntError):
    pass


class UnsupportedCommandError(TerragruntError):
    pass
