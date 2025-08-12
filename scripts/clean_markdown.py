from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
from typing import List


def fix_markdown_line_breaks(text: str) -> str:
    """
    Убирает разрывы строк посреди предложений в markdown тексте.
    Сохраняет структуру документа (заголовки, списки, блоки кода и т.д.)
    """
    md = MarkdownIt()
    tokens = md.parse(text)
    root = SyntaxTreeNode(tokens)
    
    output_lines: List[str] = []
    
    def extract_text_content(node: SyntaxTreeNode) -> str:
        """Извлекает текстовое содержимое из inline узла"""
        text_parts = []
        
        def collect_text(n: SyntaxTreeNode):
            if n.type == "text":
                # Заменяем переносы строк на пробелы
                normalized = " ".join(n.content.split())
                text_parts.append(normalized)
            elif n.type == "code_inline":
                text_parts.append(f"`{n.content}`")
            elif n.type == "strong":
                inner_text = ""
                for child in n.children:
                    if child.type == "text":
                        inner_text += child.content
                text_parts.append(f"**{inner_text}**")
            elif n.type == "em":
                inner_text = ""
                for child in n.children:
                    if child.type == "text":
                        inner_text += child.content
                text_parts.append(f"*{inner_text}*")
            elif n.type == "link":
                link_text = ""
                for child in n.children:
                    if child.type == "text":
                        link_text += child.content
                # Получаем URL из атрибутов токена
                url = ""
                if hasattr(n, 'token') and n.token and hasattr(n.token, 'attrGet'):
                    url = n.token.attrGet('href') or ""
                text_parts.append(f"[{link_text}]({url})")
            elif n.type == "softbreak":
                # Мягкий перенос строки заменяем на пробел
                text_parts.append(" ")
            elif n.type == "hardbreak":
                # Жесткий перенос строки (два пробела + \n) сохраняем
                text_parts.append("  \n")
            else:
                # Рекурсивно обрабатываем дочерние узлы
                for child in n.children:
                    collect_text(child)
        
        for child in node.children:
            collect_text(child)
        
        return "".join(text_parts)
    
    def process_node(node: SyntaxTreeNode, level: int = 0):
        """Обрабатывает узел дерева markdown"""
        
        if node.type == "heading":
            # Обработка заголовков
            heading_level = int(node.tag[1]) if node.tag else 1
            for child in node.children:
                if child.type == "inline":
                    content = extract_text_content(child)
                    output_lines.append(f"{'#' * heading_level} {content}")
            output_lines.append("")
            
        elif node.type == "paragraph":
            # Обработка параграфов
            for child in node.children:
                if child.type == "inline":
                    content = extract_text_content(child)
                    if content.strip():  # Только если есть содержимое
                        output_lines.append(content)
            output_lines.append("")
            
        elif node.type == "fence":
            # Блоки кода
            output_lines.append(f"```{node.info or ''}")
            if node.content:
                # Убираем лишний перенос строки в конце, если есть
                code_content = node.content.rstrip('\n')
                output_lines.append(code_content)
            output_lines.append("```")
            output_lines.append("")
            
        elif node.type == "code_block":
            # Обычные блоки кода (с отступом)
            if node.content:
                for line in node.content.splitlines():
                    output_lines.append(f"    {line}")
            output_lines.append("")
            
        elif node.type == "blockquote":
            # Цитаты
            quote_lines = []
            for child in node.children:
                if child.type == "paragraph":
                    for inline_child in child.children:
                        if inline_child.type == "inline":
                            content = extract_text_content(inline_child)
                            if content.strip():
                                quote_lines.append(f"> {content}")
            output_lines.extend(quote_lines)
            output_lines.append("")
            
        elif node.type == "bullet_list":
            # Маркированные списки
            for child in node.children:
                if child.type == "list_item":
                    process_list_item(child, "- ")
            output_lines.append("")
            
        elif node.type == "ordered_list":
            # Нумерованные списки
            item_number = 1
            for child in node.children:
                if child.type == "list_item":
                    process_list_item(child, f"{item_number}. ")
                    item_number += 1
            output_lines.append("")
            
        elif node.type == "hr":
            # Горизонтальная линия
            output_lines.append("---")
            output_lines.append("")
            
        elif node.type == "html_block":
            # HTML блоки сохраняем как есть
            if node.content:
                output_lines.append(node.content.rstrip('\n'))
            output_lines.append("")
            
        elif node.type == "html_inline":
            # Inline HTML
            if node.content:
                output_lines.append(node.content)
                
        else:
            # Рекурсивно обрабатываем дочерние узлы
            for child in node.children:
                process_node(child, level + 1)
    
    def process_list_item(item_node: SyntaxTreeNode, prefix: str):
        """Обрабатывает элемент списка"""
        for child in item_node.children:
            if child.type == "paragraph":
                for inline_child in child.children:
                    if inline_child.type == "inline":
                        content = extract_text_content(inline_child)
                        if content.strip():
                            output_lines.append(f"{prefix}{content}")
            elif child.type == "bullet_list" or child.type == "ordered_list":
                # Вложенные списки
                for nested_item in child.children:
                    if nested_item.type == "list_item":
                        nested_prefix = "  " + prefix  # Добавляем отступ
                        process_list_item(nested_item, nested_prefix)
    
    # Обрабатываем все узлы верхнего уровня
    for child in root.children:
        process_node(child)
    
    # Убираем лишние пустые строки в конце
    while output_lines and output_lines[-1] == "":
        output_lines.pop()
    
    # Добавляем одну пустую строку в конце файла
    output_lines.append("")
    
    return "\n".join(output_lines)


# Пример использования
if __name__ == "__main__":
    import sys
    
    # Если передан аргумент - используем его как путь к файлу
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else "output.qmd"
    else:
        input_file = "./src/Rectal-Cancer-Staging/T-Staging.qmd"
        output_file = "T-Staging_cleaned.qmd"
    
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            markdown_text = f.read()
        
        fixed_markdown = fix_markdown_line_breaks(markdown_text)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(fixed_markdown)
        
        print(f"Файл успешно обработан и сохранен как {output_file}")
        
    except FileNotFoundError:
        print(f"Ошибка: файл {input_file} не найден")
    except Exception as e:
        print(f"Ошибка при обработке файла: {e}")