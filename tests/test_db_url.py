from src.db.session import fix_postgres_url


def test_postgres_scheme_gains_asyncpg_driver() -> None:
    assert fix_postgres_url("postgres://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"


def test_postgresql_scheme_gains_asyncpg_driver() -> None:
    assert fix_postgres_url("postgresql://u:p@h/db") == "postgresql+asyncpg://u:p@h/db"


def test_async_url_is_left_alone() -> None:
    url = "postgresql+asyncpg://u:p@h/db"
    assert fix_postgres_url(url) == url
