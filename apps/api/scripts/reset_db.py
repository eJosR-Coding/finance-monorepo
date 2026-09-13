"""Wipe the database and rebuild the empty schema.

Run it with:  uv run python scripts/reset_db.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base, create_all, engine  # noqa: E402


def main() -> None:
    Base.metadata.drop_all(bind=engine)
    create_all()
    print("Base de datos reiniciada. Ejecuta 'uv run python scripts/seed.py' para cargar datos.")


if __name__ == "__main__":
    main()
