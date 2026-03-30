"""
Mistral IDE - Beautiful Edition
--------------------------------
A modern IDE for Mistral with syntax highlighting, line numbers, and a toolbar.
Requires compiler.py in the same directory.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
from tkinter import ttk
import subprocess
import sys
import os
import re

# Import the compiler (assumes compiler.py is in same folder)
try:
    from compiler import compile_mistral, execute_mistral
except ImportError:
    compile_mistral = None
    execute_mistral = None

# ----------------------------------------------------------------------
# Syntax Highlighting Text Widget with Line Numbers
# ----------------------------------------------------------------------


class LineNumbers(tk.Canvas):
    def __init__(self, parent, text_widget, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.text_widget = text_widget
        self.text_widget.bind('<KeyRelease>', self.on_change)
        self.text_widget.bind('<MouseWheel>', self.on_change)
        self.text_widget.bind('<Button-1>', self.on_change)
        self.text_widget.bind('<Configure>', self.on_change)
        self.redraw()

    def on_change(self, event=None):
        self.redraw()

    def redraw(self):
        self.delete('all')
        i = self.text_widget.index('@0,0')
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            line_num = str(i).split('.')[0]
            self.create_text(2, y, anchor='nw', text=line_num,
                             font=('Consolas', 10), fill='gray')
            i = self.text_widget.index(f'{i}+1line')


class SyntaxText(tk.Text):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.font = tkfont.Font(family='Consolas', size=10)
        self.configure(font=self.font, wrap='none', tabs=('4c',), undo=True,
                       background='#1e1e1e', foreground='#d4d4d4',
                       insertbackground='white', borderwidth=0,
                       highlightthickness=0, padx=5, pady=5)
        self.tag_configure('keyword', foreground='#569cd6')
        self.tag_configure('string', foreground='#ce9178')
        self.tag_configure('number', foreground='#b5cea8')
        self.tag_configure('comment', foreground='#6a9955')
        self.tag_configure('function', foreground='#dcdcaa')
        # special highlight for say
        self.tag_configure('say', foreground='#c586c0')

        self.bind('<KeyRelease>', self.highlight)
        self.bind('<Button-1>', self.highlight)
        self.highlight()

    def highlight(self, event=None):
        # Remove all tags
        for tag in self.tag_names():
            self.tag_remove(tag, '1.0', 'end')

        # Get the whole text
        content = self.get('1.0', 'end-1c')
        lines = content.split('\n')

        # Apply highlighting line by line
        for i, line in enumerate(lines):
            line_start = f'{i+1}.0'
            line_end = f'{i+1}.end'

            # Comments (//)
            comment_match = re.search(r'//.*', line)
            if comment_match:
                start = f'{i+1}.{comment_match.start()}'
                end = f'{i+1}.{comment_match.end()}'
                self.tag_add('comment', start, end)

            # Remove comment part for further highlighting
            line_without_comment = re.sub(r'//.*', '', line)

            # Keywords
            keywords = ['fun', 'if', 'else', 'while',
                        'return', 'and', 'or', 'not', 'true', 'false']
            for kw in keywords:
                for match in re.finditer(rf'\b{kw}\b', line_without_comment):
                    start = f'{i+1}.{match.start()}'
                    end = f'{i+1}.{match.end()}'
                    self.tag_add('keyword', start, end)

            # 'say' as special keyword
            for match in re.finditer(r'\bsay\b', line_without_comment):
                start = f'{i+1}.{match.start()}'
                end = f'{i+1}.{match.end()}'
                self.tag_add('say', start, end)

            # Strings (double quoted)
            for match in re.finditer(r'"[^"]*"', line_without_comment):
                start = f'{i+1}.{match.start()}'
                end = f'{i+1}.{match.end()}'
                self.tag_add('string', start, end)

            # Numbers
            for match in re.finditer(r'\b\d+\b', line_without_comment):
                start = f'{i+1}.{match.start()}'
                end = f'{i+1}.{match.end()}'
                self.tag_add('number', start, end)

            # Function names (after 'fun' keyword)
            # We can highlight the identifier following 'fun'
            fun_match = re.search(
                r'\bfun\s+([a-zA-Z_][a-zA-Z0-9_]*)\b', line_without_comment)
            if fun_match:
                start = f'{i+1}.{fun_match.start(1)}'
                end = f'{i+1}.{fun_match.end(1)}'
                self.tag_add('function', start, end)

# ----------------------------------------------------------------------
# Main IDE Application
# ----------------------------------------------------------------------


class MistralIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("Mistral IDE")
        self.root.geometry("900x700")
        self.current_file = None

        # Apply a modern theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Toolbar.TFrame', background='#2d2d2d')
        style.configure('Toolbar.TButton', background='#3c3c3c', foreground='white', borderwidth=0,
                        focuscolor='none', relief='flat')
        style.map('Toolbar.TButton',
                  background=[('active', '#505050')])
        style.configure('Status.TLabel', background='#007acc',
                        foreground='white', padding=2)

        # Main container
        main_container = ttk.Frame(root)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Toolbar
        toolbar = ttk.Frame(main_container, style='Toolbar.TFrame', height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.pack_propagate(False)

        # Toolbar buttons (using text, can be replaced with icons)
        self.new_btn = ttk.Button(
            toolbar, text="📄 New", style='Toolbar.TButton', command=self.new_file)
        self.new_btn.pack(side=tk.LEFT, padx=2, pady=5)

        self.open_btn = ttk.Button(
            toolbar, text="📂 Open", style='Toolbar.TButton', command=self.open_file)
        self.open_btn.pack(side=tk.LEFT, padx=2, pady=5)

        self.save_btn = ttk.Button(
            toolbar, text="💾 Save", style='Toolbar.TButton', command=self.save_file)
        self.save_btn.pack(side=tk.LEFT, padx=2, pady=5)

        self.saveas_btn = ttk.Button(
            toolbar, text="💾 Save As", style='Toolbar.TButton', command=self.save_as_file)
        self.saveas_btn.pack(side=tk.LEFT, padx=2, pady=5)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5)

        self.run_btn = ttk.Button(
            toolbar, text="▶ Run", style='Toolbar.TButton', command=self.run_code)
        self.run_btn.pack(side=tk.LEFT, padx=2, pady=5)

        self.clear_btn = ttk.Button(
            toolbar, text="🗑 Clear Output", style='Toolbar.TButton', command=self.clear_output)
        self.clear_btn.pack(side=tk.LEFT, padx=2, pady=5)

        # Editor area with line numbers
        editor_frame = ttk.Frame(main_container)
        editor_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.editor = SyntaxText(editor_frame, wrap=tk.NONE)
        self.editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.line_numbers = LineNumbers(
            editor_frame, self.editor, width=40, background='#252526', highlightthickness=0)
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)

        # Output area
        output_frame = ttk.Frame(main_container)
        output_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        output_label = ttk.Label(
            output_frame, text="Output:", background='#2d2d2d', foreground='white')
        output_label.pack(anchor=tk.W)

        self.output = tk.Text(output_frame, height=10, wrap=tk.WORD, font=('Consolas', 10),
                              background='#1e1e1e', foreground='#d4d4d4',
                              insertbackground='white', borderwidth=0,
                              highlightthickness=1, highlightcolor='#007acc')
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Output scrollbar
        output_scroll = ttk.Scrollbar(
            output_frame, orient=tk.VERTICAL, command=self.output.yview)
        output_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.output.configure(yscrollcommand=output_scroll.set)

        # Status bar
        self.status = ttk.Label(
            root, text="Ready", style='Status.TLabel', anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # Insert example code
        self.editor.insert('1.0', self.get_example_code())
        self.editor.highlight()

        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<F5>', lambda e: self.run_code())

    def get_example_code(self):
        return """// Mistral example with syntax highlighting
fun fib(n) {
    if n < 2 {
        return n;
    }
    return fib(n-1) + fib(n-2);
}

say "Fibonacci of 10 is:";
say fib(10);
"""

    def new_file(self):
        self.editor.delete('1.0', tk.END)
        self.current_file = None
        self.status.config(text="New file")

    def open_file(self):
        filename = filedialog.askopenfilename(
            defaultextension=".mistral",
            filetypes=[("Mistral files", "*.mistral"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, "r") as f:
                    content = f.read()
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', content)
                self.editor.highlight()
                self.current_file = filename
                self.status.config(text=f"Opened {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def save_file(self):
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self.save_as_file()

    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".mistral",
            filetypes=[("Mistral files", "*.mistral"), ("All files", "*.*")]
        )
        if filename:
            self._save_to_file(filename)
            self.current_file = filename
            self.status.config(text=f"Saved {os.path.basename(filename)}")

    def _save_to_file(self, filename):
        try:
            content = self.editor.get('1.0', tk.END)
            with open(filename, "w") as f:
                f.write(content)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def clear_output(self):
        self.output.delete('1.0', tk.END)

    def run_code(self):
        if compile_mistral is None:
            self.output.insert(tk.END, "Error: compiler module not found.\n")
            return

        source = self.editor.get('1.0', tk.END)
        if not source.strip():
            return

        self.output.delete('1.0', tk.END)
        self.output.insert(tk.END, "Running...\n")
        self.root.update()

        try:
            result = execute_mistral(source, capture_output=True)
            self.output.insert(tk.END, "--- stdout ---\n")
            self.output.insert(tk.END, result.stdout)
            self.output.insert(tk.END, "\n--- stderr ---\n")
            self.output.insert(tk.END, result.stderr)
            if result.returncode != 0:
                self.output.insert(
                    tk.END, f"\nProcess exited with code {result.returncode}")
            else:
                self.output.insert(tk.END, "\nExecution finished.")
        except Exception as e:
            self.output.insert(tk.END, f"Error during execution: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = MistralIDE(root)
    root.mainloop()
