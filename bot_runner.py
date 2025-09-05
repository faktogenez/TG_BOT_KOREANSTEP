import sys
import os

# Добавляем путь к директории проекта в sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import main

if __name__ == '__main__':
    main()