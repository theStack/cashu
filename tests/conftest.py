import multiprocessing
import shutil
import time
from pathlib import Path

import pytest
import pytest_asyncio
import uvicorn
from uvicorn import Config, Server

from cashu.core.migrations import migrate_databases
from cashu.core.settings import settings
from cashu.wallet import migrations
from cashu.wallet.wallet import Wallet

SERVER_ENDPOINT = "http://localhost:3337"


class UvicornServer(multiprocessing.Process):
    def __init__(self, config: Config):
        super().__init__()
        self.server = Server(config=config)
        self.config = config

    def stop(self):
        self.terminate()

    def run(self, *args, **kwargs):
        settings.lightning = False
        settings.mint_lightning_backend = "FakeWallet"
        settings.mint_listen_port = 3337
        settings.mint_database = "data/test_mint"
        settings.mint_private_key = "privatekeyofthemint"

        dirpath = Path(settings.mint_database)
        if dirpath.exists() and dirpath.is_dir():
            shutil.rmtree(dirpath)

        dirpath = Path("data/test_wallet")
        if dirpath.exists() and dirpath.is_dir():
            shutil.rmtree(dirpath)

        self.server.run()


@pytest.fixture(autouse=True, scope="session")
def mint():
    settings.mint_listen_port = 3337
    settings.port = 3337
    settings.mint_url = "http://localhost:3337"
    settings.port = settings.mint_listen_port
    config = uvicorn.Config(
        "cashu.mint.app:app",
        port=settings.mint_listen_port,
        host="127.0.0.1",
    )

    server = UvicornServer(config=config)
    server.start()
    time.sleep(1)
    yield server
    server.stop()
