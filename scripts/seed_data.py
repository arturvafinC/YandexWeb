import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.utils import seed_reference_data


def main():
    app = create_app()
    with app.app_context():
        seed_reference_data()
        print("Стартовые предметы, типы ошибок и теги добавлены или уже существуют.")


if __name__ == "__main__":
    main()
