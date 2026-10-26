from pathlib import Path

from alembic import command
from alembic.config import Config

ARQUIVO_ALEMBIC = Path(__file__).resolve().parent.parent / "alembic.ini"


def test_migracoes_geram_o_mesmo_esquema_dos_models(tmp_path: Path) -> None:
    config = Config(str(ARQUIVO_ALEMBIC))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path / 'teste.db'}")
    command.upgrade(config, "head")
    # lança erro se algum model mudou sem uma migração correspondente
    command.check(config)
    command.downgrade(config, "base")
