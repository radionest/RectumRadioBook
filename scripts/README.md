# Скрипты обработки изображений

## Установка

1. Из корневой директории проекта выполните:
```bash
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Или используйте скрипт активации:
```bash
source activate.sh
```

## Описание скриптов

### prepare_images_prerender.py
- Автоматически запускается перед сборкой Quarto
- Обрабатывает все SVG аннотации в папке `img/`
- Применяет единые стили согласно `img/layers.txt`
- Сохраняет результаты в `_book/img/`

### clean_generated_images.py
- Автоматически запускается после сборки Quarto
- Удаляет все сгенерированные файлы из исходной папки `img/`
- Оставляет только оригинальные файлы

### test_image_processing.py
- Тестовый скрипт для проверки обработки изображений
- Запускайте для тестирования без полной сборки Quarto:
```bash
.venv/bin/python scripts/test_image_processing.py
```

### prepare_images.py
- Базовый модуль с определениями стилей и функциями
- Используется другими скриптами

## Стили аннотаций

Стили определены в `prepare_images.py` согласно слоям из `img/layers.txt`:

- **Слои стенки**: mucosa, submucosa, muscularis, serosa
- **Опухолевые структуры**: tumor, tumor_core, tumor_part_1-3
- **Лимфатическая система**: lymph_node, lymph_node_necrosis
- **Сосуды**: vessels
- **Нормальные структуры**: normal, normal_fill
- **Анатомические ориентиры**: dentate_line, sphincter, peritoneum, muscle_1-4

## Требования

- Python 3.6+
- Inkscape (должен быть доступен в PATH)
- Зависимости из requirements.txt