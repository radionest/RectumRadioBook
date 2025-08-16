#!/usr/bin/env python3
"""
Скрипт для переформатирования тестов из markdown файла
Изменяет формат с A), B), C), D) на 1), 2), 3), 4)
и помечает правильный ответ звездочкой
"""

import re

def reformat_tests(input_file='src/rectal-cancer-tests.md', output_file='src/rectal-cancer-tests-formatted.md'):
    """
    Переформатирует тестовые вопросы в новый формат
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разбиваем на строки для обработки
    lines = content.split('\n')
    formatted_lines = []
    correct_answer = None
    in_question = False
    question_options = []
    
    for i, line in enumerate(lines):
        # Проверяем, начинается ли вопрос
        if line.startswith('### Вопрос'):
            in_question = True
            formatted_lines.append(line)
            question_options = []
            correct_answer = None
            
        # Проверяем варианты ответов
        elif in_question and re.match(r'^[A-D]\)', line):
            # Извлекаем букву и текст ответа
            match = re.match(r'^([A-D])\)\s*(.*)', line)
            if match:
                letter = match.group(1)
                text = match.group(2)
                question_options.append((letter, text))
                
        # Проверяем правильный ответ
        elif in_question and line.startswith('**Правильный ответ:'):
            match = re.search(r':\s*([A-D])', line)
            if match:
                correct_answer = match.group(1)
                
                # Форматируем и выводим варианты с правильным ответом
                formatted_lines.append('')  # Пустая строка перед вариантами
                for idx, (letter, text) in enumerate(question_options, 1):
                    if letter == correct_answer:
                        formatted_lines.append(f'{idx}) {text} *')
                    else:
                        formatted_lines.append(f'{idx}) {text}')
                
                in_question = False
                question_options = []
                correct_answer = None
                
        # Копируем остальные строки как есть (заголовки разделов и текст вопросов)
        elif not re.match(r'^[A-D]\)', line) and not line.startswith('**Правильный ответ:'):
            # Пропускаем пустые строки между вопросом и вариантами ответов
            if in_question and line == '' and len(question_options) == 0:
                continue
            formatted_lines.append(line)
    
    # Записываем результат
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(formatted_lines))
    
    print(f"Файл успешно переформатирован и сохранен как {output_file}")
    
    # Подсчитываем количество вопросов
    question_count = len([line for line in formatted_lines if line.startswith('### Вопрос')])
    print(f"Всего вопросов: {question_count}")

if __name__ == "__main__":
    reformat_tests()