#!/usr/bin/env python3
"""Extract comments from markdown files processed by pandoc with track-changes option."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode


@dataclass
class Comment:
    """Represents a single comment with metadata."""
    
    id: str
    author: str
    date: str
    text: str
    commented_text: str  # Text between comment-start and comment-end
    section: str
    line_number: int
    context: str = ""
    
    def __str__(self) -> str:
        """Format comment for display."""
        return (
            f"**Comment {self.id}** by {self.author} ({self.date})\n"
            f"Line {self.line_number}: {self.text}\n"
            f"Context: {self.context[:100]}..." if len(self.context) > 100 else f"Context: {self.context}"
        )


@dataclass
class CommentExtractor:
    """Extracts comments from markdown with track-changes format."""
    
    comments: list[Comment] = field(default_factory=list)
    current_section: str = "Document Start"
    section_stack: list[str] = field(default_factory=list)
    
    def extract_comments(self, markdown_text: str) -> list[Comment]:
        """Extract all comments from markdown text."""
        self.comments = []
        self.current_section = "Document Start"
        self.section_stack = []
        
        # Parse markdown to AST
        md = MarkdownIt()
        tokens = md.parse(markdown_text)
        root = SyntaxTreeNode(tokens)
        
        # Process AST
        self._process_node(root, markdown_text)
        
        return self.comments
    
    def _process_node(self, node: SyntaxTreeNode, source_text: str) -> None:
        """Process a node and its children recursively."""
        match node:
            case SyntaxTreeNode(type="heading"):
                self._update_section(node)
            case SyntaxTreeNode(type="paragraph" | "list_item" | "blockquote"):
                self._extract_from_container(node, source_text)
            case SyntaxTreeNode(type="inline"):
                self._extract_from_inline(node, source_text)
            case _:
                # Process children for other node types
                for child in node.children:
                    self._process_node(child, source_text)
    
    def _update_section(self, node: SyntaxTreeNode) -> None:
        """Update current section from heading node."""
        heading_level = int(node.tag[1]) if node.tag else 1
        
        # Extract heading text
        heading_text = ""
        for child in node.children:
            if child.type == "inline":
                heading_text = self._extract_text(child)
                break
        
        # Update section stack
        while len(self.section_stack) >= heading_level:
            self.section_stack.pop()
        
        self.section_stack.append(heading_text)
        self.current_section = " > ".join(self.section_stack) if self.section_stack else "Document Start"
    
    def _extract_text(self, node: SyntaxTreeNode) -> str:
        """Extract plain text from inline node."""
        text_parts = []
        
        def collect_text(n: SyntaxTreeNode) -> None:
            match n:
                case SyntaxTreeNode(type="text"):
                    text_parts.append(n.content)
                case SyntaxTreeNode(type="code_inline"):
                    text_parts.append(f"`{n.content}`")
                case SyntaxTreeNode(type="strong"):
                    inner = "".join(child.content for child in n.children if child.type == "text")
                    text_parts.append(f"**{inner}**")
                case SyntaxTreeNode(type="em"):
                    inner = "".join(child.content for child in n.children if child.type == "text")
                    text_parts.append(f"*{inner}*")
                case SyntaxTreeNode(type="link"):
                    link_text = "".join(child.content for child in n.children if child.type == "text")
                    url = n.token.attrGet('href') if hasattr(n, 'token') and n.token else ""
                    text_parts.append(f"[{link_text}]({url})")
                case SyntaxTreeNode(type="softbreak"):
                    text_parts.append(" ")
                case SyntaxTreeNode(type="hardbreak"):
                    text_parts.append("  \n")
                case _:
                    for child in n.children:
                        collect_text(child)
        
        for child in node.children:
            collect_text(child)
        
        return "".join(text_parts)
    
    def _extract_from_container(self, node: SyntaxTreeNode, source_text: str) -> None:
        """Extract comments from container nodes."""
        for child in node.children:
            match child:
                case SyntaxTreeNode(type="inline"):
                    self._extract_from_inline(child, source_text)
                case _:
                    self._process_node(child, source_text)
    
    def _extract_from_inline(self, node: SyntaxTreeNode, source_text: str) -> None:
        """Extract comments from inline content."""
        if not hasattr(node, 'token') or not node.token:
            return
        
        # Get line number
        line_number = node.token.map[0] + 1 if node.token.map else 0
        
        # Get the raw content from source - need broader context for multiline
        if node.token.map:
            start_line = max(0, node.token.map[0] - 5)  # Get more context
            end_line = min(len(source_text.split('\n')), node.token.map[1] + 5)
            lines = source_text.split('\n')
            raw_content = '\n'.join(lines[start_line:end_line])
        else:
            raw_content = self._extract_text(node)
        
        # Find comment patterns including multiline comments
        # Pattern now handles multiline content within brackets
        comment_pattern = r'\[([^\]]*?)\]\{\.comment-start\s+id="(\d+)"\s+author="([^"]+)"\s+date="([^"]+)"\}'
        
        for match in re.finditer(comment_pattern, raw_content, re.DOTALL):
            text = match.group(1)
            comment_id = match.group(2)
            author = match.group(3)
            date = match.group(4)
            
            # Find the end marker for this comment and extract commented text
            end_pattern = rf'\[.*?\]\{{\.comment-end\s+id="{comment_id}"\}}'
            end_match = re.search(end_pattern, raw_content[match.end():], re.DOTALL)
            
            # Extract the text between comment-start and comment-end
            commented_text = ""
            if end_match:
                # Text between start and end markers
                commented_text = raw_content[match.end():match.end() + end_match.start()]
                # Clean up the text inside the brackets before comment-end
                commented_text = re.sub(r'\[.*?\]\{', '[', commented_text)
                commented_text = ' '.join(commented_text.split())
                comment_end_pos = match.end() + end_match.end()
            else:
                comment_end_pos = match.end()
            
            # Now find the complete sentence containing the entire comment
            comment_start_pos = match.start()
            
            # Look for sentence boundaries before the comment
            # Search backwards for sentence start (. ! ? or beginning of text)
            sentence_start = 0
            for i in range(comment_start_pos - 1, -1, -1):
                if i == 0:
                    sentence_start = 0
                    break
                if raw_content[i] in '.!?':
                    # Check if followed by space and capital letter (new sentence)
                    if i + 1 < len(raw_content):
                        remaining = raw_content[i+1:min(i+10, len(raw_content))]
                        if re.match(r'^\s+[А-ЯA-Z]', remaining):
                            sentence_start = i + 1
                            break
            
            # Look for sentence boundaries after the comment
            # Search forward for sentence end (. ! ? followed by space and capital or end)
            sentence_end = len(raw_content)
            for i in range(comment_end_pos, len(raw_content)):
                if raw_content[i] in '.!?':
                    # Check if this is end of sentence
                    if i + 1 >= len(raw_content):
                        sentence_end = i + 1
                        break
                    remaining = raw_content[i+1:min(i+10, len(raw_content))]
                    if re.match(r'^\s+[А-ЯA-Z]', remaining) or re.match(r'^\s*$', remaining):
                        sentence_end = i + 1
                        break
            
            # Extract the full sentence
            full_sentence = raw_content[sentence_start:sentence_end].strip()
            
            # Clean up the sentence from comment markers but keep the original text
            context = re.sub(r'\[.*?\]\{\.comment-start[^}]+\}', '', full_sentence, flags=re.DOTALL)
            context = re.sub(r'\[.*?\]\{\.comment-end[^}]+\}', '', context, flags=re.DOTALL)
            context = ' '.join(context.split())
            
            comment = Comment(
                id=comment_id,
                author=author,
                date=date,
                text=text,
                commented_text=commented_text,
                section=self.current_section,
                line_number=line_number,
                context=context
            )
            
            self.comments.append(comment)


def generate_report(comments: list[Comment]) -> str:
    """Generate a markdown report of extracted comments."""
    if not comments:
        return "# No Comments Found\n\nNo track-changes comments were found in the document."
    
    # Group comments by section
    sections: dict[str, list[Comment]] = {}
    for comment in comments:
        if comment.section not in sections:
            sections[comment.section] = []
        sections[comment.section].append(comment)
    
    # Generate report
    report_lines = [
        "# Comments Report",
        f"\nTotal comments found: {len(comments)}",
        f"Authors: {', '.join(set(c.author for c in comments))}",
        "\n---\n"
    ]
    
    for section, section_comments in sections.items():
        report_lines.append(f"\n## {section}")
        report_lines.append(f"\n*{len(section_comments)} comment(s)*\n")
        
        for comment in sorted(section_comments, key=lambda c: c.line_number):
            report_lines.append(f"\n### {comment.id}. Line {comment.line_number}")
            report_lines.append(f"**Comment:** {comment.text}")
            if comment.commented_text:
                report_lines.append(f"**Commented text:** {comment.commented_text}")
            report_lines.append(f"**Full sentence:** {comment.context}")
            report_lines.append("")
    
    return "\n".join(report_lines)


def main() -> None:
    """Main entry point."""
    # Default input file
    input_file = Path("/home/nest/Documents/RectumRadioBook/corrections/burovik2.md")
    
    # Allow command line override
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File {input_file} not found", file=sys.stderr)
        sys.exit(1)
    
    # Read markdown content
    markdown_text = input_file.read_text(encoding='utf-8')
    
    # Extract comments
    extractor = CommentExtractor()
    comments = extractor.extract_comments(markdown_text)
    
    # Generate report
    report = generate_report(comments)
    
    # Output report
    output_file = input_file.parent / f"{input_file.stem}_comments.md"
    output_file.write_text(report, encoding='utf-8')
    
    print(f"Extracted {len(comments)} comments")
    print(f"Report saved to: {output_file}")
    
    # Also print to stdout for review
    print("\n" + "=" * 60)
    print(report)


if __name__ == "__main__":
    main()