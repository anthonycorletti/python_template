import pytest_asyncio


@pytest_asyncio.fixture(scope="session", autouse=True)
def _session() -> None:
    pass


@pytest_asyncio.fixture(scope="module", autouse=True)
def _module() -> None:
    pass
