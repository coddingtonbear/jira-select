try:
    import debugpy
except ImportError:
    debugpy = None


def pytest_addoption(parser):
    parser.addoption("--debugger", action="store_true")
    parser.addoption("--debugger-port", type=int, default=5678)


def pytest_sessionstart(session):
    if not debugpy:
        return

    if session.config.getoption("debugger"):
        port = session.config.getoption("debugger_port")
        debugpy.listen(port)
        debugpy.wait_for_client()
