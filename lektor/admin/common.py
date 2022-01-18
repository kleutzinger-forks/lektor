from typing import Any
from typing import NamedTuple
from typing import Optional
from typing import Sequence
from typing import TYPE_CHECKING
from typing import Union

from flask import Flask
from werkzeug.utils import cached_property

from lektor.builder import Builder
from lektor.buildfailures import FailureController
from lektor.db import Database
from lektor.db import Pad
from lektor.db import Tree
from lektor.environment import Environment
from lektor.environment.config import Config
from lektor.reporter import CliReporter

if TYPE_CHECKING:
    import os


class LektorInfo(NamedTuple):
    env: Environment
    output_path: Union[str, "os.PathLike[Any]"]
    verbosity: int = 0
    extra_flags: Optional[Sequence[str]] = None

    def make_lektor_context(self) -> "LektorContext":
        return LektorContext._make(self)


class LektorContext(LektorInfo):
    """Per-request object which provides the interface to Lektor for the Flask app(s).

    This does not provide any logic.  It just provides access to the
    needed Lektor internals and instances.
    """

    @property
    def project_id(self) -> str:
        return self.env.project.id

    @cached_property
    def database(self) -> Database:
        return Database(self.env)

    @cached_property
    def pad(self) -> Pad:
        return self.database.new_pad()

    @cached_property
    def tree(self) -> Tree:
        return Tree(self.pad)

    @property
    def config(self) -> Config:
        return self.database.config

    @cached_property
    def builder(self) -> Builder:
        return Builder(self.pad, self.output_path, self.extra_flags)

    @cached_property
    def failure_controller(self) -> FailureController:
        return FailureController(self.pad, self.output_path)

    def cli_reporter(self) -> CliReporter:
        return CliReporter(self.env, verbosity=self.verbosity)


class LektorApp(Flask):
    def __init__(
        self,
        lektor_info: LektorInfo,
        debug: bool = False,
        ui_lang: str = "en",
        **kwargs: Any,
    ) -> None:
        Flask.__init__(self, "lektor.admin", **kwargs)
        self.lektor_info = lektor_info
        self.config["lektor.ui_lang"] = ui_lang
        self.debug = debug
        self.config["PROPAGATE_EXCEPTIONS"] = True
