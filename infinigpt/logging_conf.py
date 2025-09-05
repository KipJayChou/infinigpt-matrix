import logging
import logging.config
import re


class MatrixHighlighter:
    _user_re = re.compile(r"@[A-Za-z0-9_.\-:]+\b")
    _room_re = re.compile(r"[#!][^\s:]+:[A-Za-z0-9_.\-]+")
    _model_re = re.compile(r"\bModel set to\s+(?P<model>\S+)")
    _sent_msg_re = re.compile(r"\bsent\s+(?P<msg>.+?)\s+in\s+")
    _joined_re = re.compile(r"^(?P<bot>.+?)\s+joined\s+(?P<room>\S+)")
    _sent_line_re = re.compile(r"^(?P<display>.+?)\s+\((?P<id>@[^)]+)\)\s+sent\s+(?P<msg>.+?)\s+in\s+(?P<room>\S+)", re.S)
    _sending_resp_re = re.compile(r"Sending response to\s+(?P<name>.+?)\s+in\s+(?P<room>\S+):\s+(?P<body>.*)", re.S)
    _thinking_re = re.compile(r"Model thinking for\s+(?P<who>.+?):\s+(?P<thinking>.*)", re.S)
    _sys_prompt_re = re.compile(r"System prompt for\s+(?P<who>.+?)\s+\(.*?\)\s+set to\s+'(?P<prompt>.*)'")
    _verified_re = re.compile(r"\bverified device\s+(?P<dev>\S+)")
    _persist_re = re.compile(r"\bPersisted device_id to\s+(?P<path>\S+)")
    _tool_call_re = re.compile(r"(?P<tool>Tool)\s+\((?P<origin>MCP|builtin)\):\s+(?P<name>\S+)\s+args=(?P<args>.*)")

    def __call__(self, value):
        try:
            from rich.text import Text
        except Exception:
            return value
        text = value if hasattr(value, "stylize") else Text(str(value))
        self.highlight(text)
        return text

    def highlight(self, text) -> None:
        s = text.plain
        for m in self._user_re.finditer(s):
            text.stylize("bold cyan", m.start(), m.end())
        for m in self._room_re.finditer(s):
            text.stylize("magenta", m.start(), m.end())
        for m in self._model_re.finditer(s):
            span = m.span("model")
            text.stylize("bold yellow", span[0], span[1])
        for m in self._sent_msg_re.finditer(s):
            span = m.span("msg")
            text.stylize("white", span[0], span[1])
        for m in self._sent_line_re.finditer(s):
            dspan = m.span("display")
            rsp = m.span("room")
            text.stylize("bold cyan", dspan[0], dspan[1])
            text.stylize("magenta", rsp[0], rsp[1])
        for m in self._joined_re.finditer(s):
            bspan = m.span("bot")
            rsp = m.span("room")
            text.stylize("bold cyan", bspan[0], bspan[1])
            text.stylize("magenta", rsp[0], rsp[1])
        for m in self._sending_resp_re.finditer(s):
            nspan = m.span("name")
            text.stylize("bold cyan", nspan[0], nspan[1])
            bsp = m.span("body")
            body_text = s[bsp[0]:bsp[1]]
            nl = body_text.find("\n")
            if nl >= 0:
                text.stylize("bold", bsp[0] + nl + 1, bsp[1])
            else:
                text.stylize("bold", bsp[0], bsp[1])
        for m in self._thinking_re.finditer(s):
            wsp = m.span("who")
            tsp = m.span("thinking")
            text.stylize("bold cyan", wsp[0], wsp[1])
            text.stylize("dim italic", tsp[0], tsp[1])
        for m in self._sys_prompt_re.finditer(s):
            wsp = m.span("who")
            text.stylize("bold cyan", wsp[0], wsp[1])
        for m in self._verified_re.finditer(s):
            span = m.span("dev")
            text.stylize("green", span[0], span[1])
        for m in self._persist_re.finditer(s):
            span = m.span("path")
            text.stylize("green", span[0], span[1])
        for m in self._tool_call_re.finditer(s):
            tsp = m.span("tool")
            osp = m.span("origin")
            nsp = m.span("name")
            asp = m.span("args")
            text.stylize("bold cyan", tsp[0], tsp[1])
            text.stylize("cyan", osp[0], osp[1])
            text.stylize("bold yellow", nsp[0], nsp[1])
            text.stylize("dim", asp[0], asp[1])


def setup_logging(level: str = "INFO", json: bool = False) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.config.dictConfig({"version": 1, "disable_existing_loggers": True})
    try:
        from rich.console import Console
        from rich.logging import RichHandler
        from rich.traceback import install as rich_traceback_install

        rich_traceback_install(show_locals=False)
        console = Console(highlight=False, force_terminal=True)
        highlighter = MatrixHighlighter()
        handler = RichHandler(console=console, rich_tracebacks=True, markup=True, show_level=True, show_time=True, show_path=False, highlighter=highlighter)
        datefmt = "[%X]"
        fmt = "%(message)s" if not json else "%(name)s - %(message)s"
        root = logging.getLogger(); root.handlers = []; root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("infinigpt"); pkg_logger.handlers = []; pkg_logger.setLevel(lvl)
        logging.Formatter(fmt=fmt, datefmt=datefmt)
        pkg_logger.addHandler(handler); pkg_logger.propagate = False
    except Exception:
        fmt = ("%(asctime)s %(levelname)s %(name)s %(message)s" if json else "%(asctime)s - %(levelname)s - %(message)s")
        root = logging.getLogger(); root.handlers = []; root.setLevel(logging.ERROR)
        pkg_logger = logging.getLogger("infinigpt"); pkg_logger.handlers = []; pkg_logger.setLevel(lvl)
        handler = logging.StreamHandler(); handler.setFormatter(logging.Formatter(fmt))
        pkg_logger.addHandler(handler); pkg_logger.propagate = False


def configure_logging(level: int = logging.INFO) -> None:
    setup_logging(logging.getLevelName(level))
