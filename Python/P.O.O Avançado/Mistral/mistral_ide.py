#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║           MISTRAL IDE  v1.0.0                            ║
║   A VS Code-style IDE for the Mistral Language           ║
║   Includes: Syntax Highlighting · mistral-fmt · Runner   ║
╚══════════════════════════════════════════════════════════╝

MISTRAL LANGUAGE QUICK REFERENCE:
  fn       → def          (function definition)
  when     → if           (conditional)
  orwhen   → elif         (else-if)
  otherwise→ else         (fallback)
  repeat   → while        (while loop)
  loop     → for          (for loop)
  true     → True
  false    → False
  null     → None
  echo     → print        (print alias)
  let      → (optional variable declaration keyword)
  catch    → except
  ::       → :            (type annotation separator)

Example:
  fn greet(name :: str) -> str:
      let msg = "Hello, " + name
      return msg

  loop i in range(5):
      when i % 2 == 0:
          echo(i)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re
import sys
import io
import os
import threading
import traceback
from pathlib import Path


# ══════════════════════════════════════════════════════════════════
#  MISTRAL LANGUAGE — KEYWORD DEFINITIONS
# ══════════════════════════════════════════════════════════════════

MISTRAL_KEYWORDS = [
    'fn', 'when', 'orwhen', 'otherwise', 'repeat', 'loop',
    'true', 'false', 'null', 'echo', 'let', 'pass', 'return',
    'break', 'continue', 'import', 'from', 'as', 'class',
    'try', 'catch', 'finally', 'raise', 'with', 'yield',
    'lambda', 'global', 'nonlocal', 'del', 'and', 'or', 'not',
    'in', 'is', 'assert', 'async', 'await',
]

MISTRAL_BUILTINS = [
    'print', 'len', 'range', 'type', 'int', 'str', 'float',
    'list', 'dict', 'set', 'tuple', 'bool', 'input', 'open',
    'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
    'sum', 'min', 'max', 'abs', 'round', 'super', 'isinstance',
    'hasattr', 'getattr', 'setattr', 'repr', 'hash', 'id',
    'callable', 'iter', 'next', 'any', 'all', 'dir', 'vars',
    'format', 'chr', 'ord', 'hex', 'oct', 'bin', 'pow',
]


# ══════════════════════════════════════════════════════════════════
#  MISTRAL TRANSPILER  (Mistral → Python)
# ══════════════════════════════════════════════════════════════════

class MistralTranspiler:
    """Converts Mistral source code into executable Python."""

    KEYWORD_MAP = {
        'fn':        'def',
        'when':      'if',
        'orwhen':    'elif',
        'otherwise': 'else',
        'repeat':    'while',
        'loop':      'for',
        'true':      'True',
        'false':     'False',
        'null':      'None',
        'echo':      'print',
        'catch':     'except',
    }

    def transpile(self, source: str) -> str:
        lines = source.splitlines(keepends=False)
        output = []
        for line in lines:
            output.append(self._transpile_line(line))
        return '\n'.join(output)

    def _transpile_line(self, line: str) -> str:
        # Preserve blank lines
        if not line.strip():
            return line

        # Preserve comments as-is
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        if stripped.startswith('#'):
            return line

        # --- Split off inline comment so we don't transform it ---
        # Simple approach: find unquoted '#'
        code_part, comment_part = self._split_comment(stripped)

        # 1. Remove optional 'let' keyword at line start
        code_part = re.sub(r'^let\s+', '', code_part)

        # 2. Replace type annotation :: with just removing it for exec
        #    e.g. fn add(a :: int, b :: int):
        code_part = re.sub(r'\s*::\s*\w+', '', code_part)

        # 3. Remove return type arrows  -> Type  before colon
        code_part = re.sub(r'\s*->\s*\w+\s*(?=:)', '', code_part)

        # 4. Replace Mistral keywords with Python equivalents
        #    Use word boundaries to avoid partial replacements
        for mst_kw, py_kw in self.KEYWORD_MAP.items():
            code_part = re.sub(r'\b' + re.escape(mst_kw) + r'\b', py_kw, code_part)

        result = indent + code_part
        if comment_part:
            result += '  ' + comment_part
        return result

    @staticmethod
    def _split_comment(code: str):
        """Split 'code  # comment' into (code, '# comment') respecting strings."""
        in_single = False
        in_double = False
        i = 0
        while i < len(code):
            c = code[i]
            if c == "'" and not in_double:
                in_single = not in_single
            elif c == '"' and not in_single:
                in_double = not in_double
            elif c == '#' and not in_single and not in_double:
                return code[:i].rstrip(), code[i:]
            i += 1
        return code, ''


# ══════════════════════════════════════════════════════════════════
#  MISTRAL-FMT  (Auto-formatter, like autopep8)
# ══════════════════════════════════════════════════════════════════

class MistralFormatter:
    """
    mistral-fmt: Automatic code formatter for the Mistral language.
    Applies PEP-8-style rules adapted for Mistral syntax.
    """

    CONTROL_KEYWORDS = ('when', 'orwhen', 'repeat', 'loop', 'fn',
                        'class', 'with', 'try', 'catch', 'finally',
                        'otherwise', 'return', 'yield', 'assert')

    def format(self, source: str) -> str:
        lines = source.splitlines()
        lines = [self._fix_trailing_whitespace(l) for l in lines]
        lines = [self._fix_spaces_after_keywords(l) for l in lines]
        lines = [self._fix_operator_spacing(l) for l in lines]
        lines = [self._fix_comma_spacing(l) for l in lines]
        lines = [self._fix_colon_spacing(l) for l in lines]

        source = '\n'.join(lines)
        source = self._fix_blank_lines_around_fn(source)
        source = self._fix_blank_lines_around_class(source)
        source = self._remove_excess_blank_lines(source)
        source = self._ensure_final_newline(source)
        return source

    # ── Individual fixers ──────────────────────────────────────

    @staticmethod
    def _fix_trailing_whitespace(line: str) -> str:
        return line.rstrip()

    def _fix_spaces_after_keywords(self, line: str) -> str:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        for kw in self.CONTROL_KEYWORDS:
            # keyword immediately followed by ( or letter without space
            pattern = r'\b(' + kw + r')(?=\S)'
            stripped = re.sub(pattern, r'\1 ', stripped)
        return indent + stripped

    @staticmethod
    def _fix_operator_spacing(line: str) -> str:
        # Skip comment lines
        if line.lstrip().startswith('#'):
            return line
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        # Augmented assignments: +=, -=, *=, /=, **=, //=, %=
        stripped = re.sub(r'\s*(\+=|-=|\*\*=|//=|\*=|/=|%=|&=|\|=|\^=)\s*',
                          r' \1 ', stripped)
        # Comparison operators (must come before single =)
        stripped = re.sub(r'\s*(==|!=|<=|>=)\s*', r' \1 ', stripped)
        # Single assignment = (not ==, !=, <=, >=)
        stripped = re.sub(r'(?<![=!<>+\-*/%&|^])=(?!=)', r' = ', stripped)
        # Normalise multiple spaces (but not in indentation)
        stripped = re.sub(r'  +', ' ', stripped)
        # Arrow operator
        stripped = re.sub(r'\s*->\s*', r' -> ', stripped)
        return indent + stripped

    @staticmethod
    def _fix_comma_spacing(line: str) -> str:
        if line.lstrip().startswith('#'):
            return line
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        # Remove space before comma, ensure space after
        stripped = re.sub(r'\s*,\s*', ', ', stripped)
        # But no trailing comma-space at end of paren
        stripped = re.sub(r',\s*\)', ')', stripped)
        return indent + stripped

    @staticmethod
    def _fix_colon_spacing(line: str) -> str:
        """Ensure colons in slices/dicts have no extra spaces; block colons are fine."""
        if line.lstrip().startswith('#'):
            return line
        return line  # conservative – avoid breaking string literals

    def _fix_blank_lines_around_fn(self, source: str) -> str:
        return self._ensure_blank_lines_before(source, r'^(\s*)fn\s+\w+', n=2)

    def _fix_blank_lines_around_class(self, source: str) -> str:
        return self._ensure_blank_lines_before(source, r'^class\s+\w+', n=2)

    @staticmethod
    def _ensure_blank_lines_before(source: str, pattern: str, n: int) -> str:
        lines = source.splitlines()
        result = []
        for i, line in enumerate(lines):
            if re.match(pattern, line) and i > 0:
                # Strip trailing blank lines from result
                while result and result[-1].strip() == '':
                    result.pop()
                # Add exactly n blank lines
                result.extend([''] * n)
            result.append(line)
        return '\n'.join(result)

    @staticmethod
    def _remove_excess_blank_lines(source: str) -> str:
        """Collapse 3+ consecutive blank lines into 2."""
        return re.sub(r'\n{4,}', '\n\n\n', source)

    @staticmethod
    def _ensure_final_newline(source: str) -> str:
        return source.rstrip('\n') + '\n'

    def format_report(self, original: str, formatted: str) -> str:
        """Return a human-readable diff summary."""
        orig_lines = original.splitlines()
        fmt_lines = formatted.splitlines()
        changes = sum(1 for a, b in zip(orig_lines, fmt_lines) if a != b)
        added = max(0, len(fmt_lines) - len(orig_lines))
        removed = max(0, len(orig_lines) - len(fmt_lines))
        return (f"mistral-fmt: {changes} line(s) modified, "
                f"+{added}/-{removed} lines")


# ══════════════════════════════════════════════════════════════════
#  VS CODE COLOUR PALETTE
# ══════════════════════════════════════════════════════════════════

class VSColors:
    BG            = '#1e1e1e'
    SIDEBAR_BG    = '#252526'
    TAB_INACTIVE  = '#2d2d30'
    TAB_ACTIVE    = '#1e1e1e'
    ACTIVITY_BAR  = '#333333'
    STATUS_BAR    = '#007acc'
    PANEL_BG      = '#1e1e1e'
    PANEL_HEADER  = '#252526'
    MENU_BG       = '#3c3c3c'
    BORDER        = '#454545'
    SASH          = '#3e3e42'
    SELECTION     = '#264f78'
    HOVER         = '#2a2d2e'
    SCROLLBAR     = '#424242'

    # Text
    TEXT          = '#d4d4d4'
    TEXT_DIM      = '#858585'
    TEXT_BRIGHT   = '#ffffff'
    TEXT_MUTED    = '#cccccc'
    LINE_NUMS     = '#5a5a5a'

    # Syntax
    SYN_KEYWORD   = '#569cd6'  # blue
    SYN_BUILTIN   = '#dcdcaa'  # yellow
    SYN_STRING    = '#ce9178'  # orange
    SYN_COMMENT   = '#6a9955'  # green
    SYN_NUMBER    = '#b5cea8'  # light green
    SYN_CLASS     = '#4ec9b0'  # teal
    SYN_FUNC      = '#dcdcaa'  # yellow
    SYN_DECORATOR = '#c586c0'  # purple
    SYN_SELF      = '#9cdcfe'  # light blue
    SYN_OPERATOR  = '#d4d4d4'

    # Terminal
    TERM_OUTPUT   = '#d4d4d4'
    TERM_ERROR    = '#f44747'
    TERM_SUCCESS  = '#4ec9b0'
    TERM_INFO     = '#569cd6'
    TERM_PROMPT   = '#4ec9b0'
    TERM_WARN     = '#ce9178'

    # Accent
    ACCENT        = '#0e639c'
    ACCENT_HOVER  = '#1177bb'


# ══════════════════════════════════════════════════════════════════
#  MAIN IDE APPLICATION
# ══════════════════════════════════════════════════════════════════

class MistralIDE:

    DEFAULT_SAMPLE = '''\
# ╔══════════════════════════════╗
# ║  Welcome to Mistral!         ║
# ╚══════════════════════════════╝
# Mistral is a clean, readable language inspired by Python.
# Press F5 to run  •  Alt+Shift+F to format with mistral-fmt

fn factorial(n :: int) -> int:
    """Return n! recursively."""
    when n <= 1:
        return 1
    otherwise:
        return n * factorial(n - 1)


fn fizzbuzz(limit :: int):
    loop i in range(1, limit + 1):
        when i % 15 == 0:
            echo("FizzBuzz")
        orwhen i % 3 == 0:
            echo("Fizz")
        orwhen i % 5 == 0:
            echo("Buzz")
        otherwise:
            echo(i)


fn main():
    echo("── Factorial ──────────────────")
    loop n in range(1, 8):
        echo(f"{n}! = {factorial(n)}")

    echo("")
    echo("── FizzBuzz (1-20) ────────────")
    fizzbuzz(20)

    echo("")
    echo("── List comprehension ─────────")
    let squares = [x * x loop x in range(1, 6)]
    echo("Squares:", squares)

    echo("")
    echo("── Repeat (while) loop ────────")
    let count = 0
    repeat count < 5:
        echo(f"  count = {count}")
        count += 1


main()
'''

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('Mistral IDE')
        self.root.geometry('1440x900')
        self.root.configure(bg=VSColors.BG)
        self.root.minsize(900, 600)

        self.transpiler  = MistralTranspiler()
        self.formatter   = MistralFormatter()

        # tab_widget_name → dict(editor, line_nums, path, modified)
        self.tab_data: dict = {}
        self.sidebar_visible  = True
        self.terminal_visible = True
        self._highlight_after_id = None

        self._build_styles()
        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()

        # Open a welcome file
        self._new_tab('welcome.mst', self.DEFAULT_SAMPLE)
        self._terminal_write('Mistral IDE v1.0.0  —  ready.\n', 'info')
        self._terminal_write('F5 = run  •  Alt+Shift+F = mistral-fmt  •  Ctrl+S = save\n\n',
                             'dim')

    # ── TTK Styles ─────────────────────────────────────────────

    def _build_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')

        style.configure('TNotebook',
                        background=VSColors.SIDEBAR_BG,
                        borderwidth=0,
                        tabmargins=[0, 0, 0, 0])
        style.configure('TNotebook.Tab',
                        background=VSColors.TAB_INACTIVE,
                        foreground=VSColors.TEXT_DIM,
                        padding=[16, 7],
                        borderwidth=0,
                        focuscolor=VSColors.TAB_INACTIVE)
        style.map('TNotebook.Tab',
                  background=[('selected', VSColors.TAB_ACTIVE),
                               ('active',   VSColors.HOVER)],
                  foreground=[('selected', VSColors.TEXT_BRIGHT),
                               ('active',   VSColors.TEXT)])

        style.configure('Treeview',
                        background=VSColors.SIDEBAR_BG,
                        foreground=VSColors.TEXT_MUTED,
                        fieldbackground=VSColors.SIDEBAR_BG,
                        borderwidth=0,
                        rowheight=22)
        style.configure('Treeview.Heading',
                        background=VSColors.SIDEBAR_BG,
                        foreground=VSColors.TEXT_DIM,
                        relief='flat')
        style.map('Treeview',
                  background=[('selected', '#094771')],
                  foreground=[('selected', VSColors.TEXT_BRIGHT)])

        style.configure('Vertical.TScrollbar',
                        background=VSColors.SCROLLBAR,
                        troughcolor=VSColors.BG,
                        borderwidth=0,
                        arrowcolor=VSColors.TEXT_DIM,
                        width=10)
        style.configure('Horizontal.TScrollbar',
                        background=VSColors.SCROLLBAR,
                        troughcolor=VSColors.BG,
                        borderwidth=0,
                        arrowcolor=VSColors.TEXT_DIM,
                        width=10)

        style.configure('TPanedwindow', background=VSColors.BORDER)

    # ── Menu Bar ───────────────────────────────────────────────

    def _build_menu(self):
        mb = tk.Menu(self.root,
                     bg=VSColors.MENU_BG, fg=VSColors.TEXT_MUTED,
                     activebackground='#094771',
                     activeforeground=VSColors.TEXT_BRIGHT,
                     borderwidth=0, relief='flat')

        def menu(label, items):
            m = tk.Menu(mb, tearoff=0,
                        bg=VSColors.SIDEBAR_BG, fg=VSColors.TEXT_MUTED,
                        activebackground='#094771',
                        activeforeground=VSColors.TEXT_BRIGHT,
                        borderwidth=1, relief='solid',
                        bd=1)
            for item in items:
                if item == '---':
                    m.add_separator(background=VSColors.BORDER)
                else:
                    lbl, acc, cmd = item
                    m.add_command(label=lbl, accelerator=acc, command=cmd)
            mb.add_cascade(label=label, menu=m)

        menu('File', [
            ('New File',       'Ctrl+N',       self._new_file),
            ('Open File…',     'Ctrl+O',       self._open_file),
            ('Open Folder…',   '',             self._open_folder),
            '---',
            ('Save',           'Ctrl+S',       self._save_file),
            ('Save As…',       'Ctrl+Shift+S', self._save_file_as),
            '---',
            ('Exit',           'Alt+F4',       self.root.quit),
        ])
        menu('Edit', [
            ('Undo',                    'Ctrl+Z',       lambda: self._editor_cmd('edit_undo')),
            ('Redo',                    'Ctrl+Y',       lambda: self._editor_cmd('edit_redo')),
            '---',
            ('Find…',                   'Ctrl+F',       self._find_dialog),
            ('Replace…',               'Ctrl+H',       self._replace_dialog),
            '---',
            ('Format Document (mistral-fmt)', 'Alt+Shift+F', self._format_code),
        ])
        menu('Run', [
            ('▶  Run File',             'F5',           self._run_code),
            ('⚡  Format & Run',        'F6',           self._format_and_run),
            '---',
            ('Clear Terminal',          '',             self._clear_terminal),
        ])
        menu('View', [
            ('Toggle Sidebar',          'Ctrl+B',       self._toggle_sidebar),
            ('Toggle Terminal',         'Ctrl+`',       self._toggle_terminal),
        ])
        menu('Language', [
            ('Mistral Syntax Reference', '', self._show_reference),
            ('About Mistral',            '', self._show_about),
        ])

        self.root.config(menu=mb)

    # ── Main UI ────────────────────────────────────────────────

    def _build_ui(self):
        # ── Status bar (pack first so it's at the very bottom)
        self._build_status_bar()

        # ── Root horizontal layout: [activity | sidebar | editor]
        self.root_frame = tk.Frame(self.root, bg=VSColors.BG)
        self.root_frame.pack(fill=tk.BOTH, expand=True)

        self._build_activity_bar()

        # Horizontal paned window (sidebar + editor)
        self.h_pane = tk.PanedWindow(self.root_frame,
                                     orient=tk.HORIZONTAL,
                                     bg=VSColors.BORDER,
                                     sashwidth=3,
                                     sashrelief='flat',
                                     bd=0)
        self.h_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar()
        self._build_editor_panel()

    # ── Activity Bar ───────────────────────────────────────────

    def _build_activity_bar(self):
        bar = tk.Frame(self.root_frame,
                       bg=VSColors.ACTIVITY_BAR, width=48)
        bar.pack(side=tk.LEFT, fill=tk.Y)
        bar.pack_propagate(False)

        # Logo
        logo = tk.Label(bar, text='🌀', bg=VSColors.ACTIVITY_BAR,
                        fg='#4fc3f7', font=('Segoe UI Emoji', 18),
                        pady=12, cursor='hand2')
        logo.pack(fill=tk.X)

        icons = [
            ('📁', 'Explorer',  self._toggle_sidebar),
            ('🔍', 'Search',    self._find_dialog),
            ('▶',  'Run',       self._run_code),
            ('⚡',  'Format',   self._format_code),
        ]
        for icon, tip, cmd in icons:
            lbl = tk.Label(bar, text=icon,
                           bg=VSColors.ACTIVITY_BAR, fg=VSColors.TEXT_DIM,
                           font=('Segoe UI Emoji', 14),
                           pady=10, cursor='hand2')
            lbl.pack(fill=tk.X)
            lbl.bind('<Button-1>', lambda e, c=cmd: c())
            lbl.bind('<Enter>',   lambda e, w=lbl: w.configure(fg=VSColors.TEXT_BRIGHT))
            lbl.bind('<Leave>',   lambda e, w=lbl: w.configure(fg=VSColors.TEXT_DIM))

        # Bottom: settings
        bottom = tk.Label(bar, text='⚙️',
                          bg=VSColors.ACTIVITY_BAR, fg=VSColors.TEXT_DIM,
                          font=('Segoe UI Emoji', 14), cursor='hand2')
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=8)

    # ── Sidebar (File Explorer) ────────────────────────────────

    def _build_sidebar(self):
        self.sidebar_frame = tk.Frame(self.h_pane,
                                      bg=VSColors.SIDEBAR_BG, width=220)
        self.h_pane.add(self.sidebar_frame, minsize=120, width=220)

        # Header
        hdr = tk.Frame(self.sidebar_frame, bg=VSColors.SIDEBAR_BG)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text='EXPLORER',
                 bg=VSColors.SIDEBAR_BG, fg=VSColors.TEXT_DIM,
                 font=('Segoe UI', 9, 'bold'),
                 anchor='w', padx=12, pady=8).pack(side=tk.LEFT)

        # Empty state
        self.sidebar_empty = tk.Frame(self.sidebar_frame,
                                       bg=VSColors.SIDEBAR_BG)
        self.sidebar_empty.pack(fill=tk.X, pady=30)
        tk.Label(self.sidebar_empty, text='No folder opened',
                 bg=VSColors.SIDEBAR_BG, fg=VSColors.TEXT_DIM,
                 font=('Segoe UI', 10), wraplength=190).pack()
        tk.Button(self.sidebar_empty, text='Open Folder…',
                  bg=VSColors.ACCENT, fg=VSColors.TEXT_BRIGHT,
                  font=('Segoe UI', 10), relief='flat', bd=0,
                  padx=10, pady=5, cursor='hand2',
                  command=self._open_folder).pack(pady=10)

        # File tree (shown after folder opened)
        tree_frame = tk.Frame(self.sidebar_frame, bg=VSColors.SIDEBAR_BG)
        self.file_tree = ttk.Treeview(tree_frame, show='tree',
                                       selectmode='browse')
        vsb = ttk.Scrollbar(tree_frame, orient='vertical',
                            command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.pack(fill=tk.BOTH, expand=True)
        self.file_tree.bind('<Double-Button-1>', self._on_tree_dblclick)
        self.tree_frame_widget = tree_frame   # store ref

    # ── Editor Panel ───────────────────────────────────────────

    def _build_editor_panel(self):
        editor_outer = tk.Frame(self.h_pane, bg=VSColors.BG)
        self.h_pane.add(editor_outer, minsize=400)

        # Vertical pane: [notebook] / [terminal]
        self.v_pane = tk.PanedWindow(editor_outer,
                                     orient=tk.VERTICAL,
                                     bg=VSColors.BORDER,
                                     sashwidth=3,
                                     sashrelief='flat',
                                     bd=0)
        self.v_pane.pack(fill=tk.BOTH, expand=True)

        # Top: tab notebook
        nb_frame = tk.Frame(self.v_pane, bg=VSColors.BG)
        self.v_pane.add(nb_frame, minsize=150)

        self.notebook = ttk.Notebook(nb_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

        # Bottom: terminal
        self.terminal_panel = self._build_terminal_panel(self.v_pane)
        self.v_pane.add(self.terminal_panel, minsize=80, height=200)

    # ── Terminal Panel ─────────────────────────────────────────

    def _build_terminal_panel(self, parent) -> tk.Frame:
        panel = tk.Frame(parent, bg=VSColors.PANEL_BG)

        # Header bar
        hdr = tk.Frame(panel, bg=VSColors.PANEL_HEADER, height=30)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text='TERMINAL',
                 bg=VSColors.PANEL_HEADER, fg=VSColors.TEXT_DIM,
                 font=('Segoe UI', 9, 'bold'), padx=12).pack(side=tk.LEFT)

        # Tab buttons
        for label, cmd in [('🗑 Clear', self._clear_terminal),
                            ('✕',       self._toggle_terminal)]:
            b = tk.Button(hdr, text=label,
                          bg=VSColors.PANEL_HEADER, fg=VSColors.TEXT_DIM,
                          font=('Segoe UI', 9), relief='flat', bd=0,
                          padx=8, pady=0, cursor='hand2', command=cmd)
            b.pack(side=tk.RIGHT, padx=2)
            b.bind('<Enter>', lambda e, w=b: w.configure(fg=VSColors.TEXT_BRIGHT))
            b.bind('<Leave>', lambda e, w=b: w.configure(fg=VSColors.TEXT_DIM))

        # Thin separator
        tk.Frame(panel, bg=VSColors.BORDER, height=1).pack(fill=tk.X)

        # Text area
        t_frame = tk.Frame(panel, bg=VSColors.PANEL_BG)
        t_frame.pack(fill=tk.BOTH, expand=True)

        self.terminal = tk.Text(t_frame,
                                bg='#0d1117', fg=VSColors.TERM_OUTPUT,
                                font=('Consolas', 11),
                                relief='flat', bd=0,
                                padx=10, pady=6,
                                insertbackground=VSColors.TEXT_BRIGHT,
                                selectbackground=VSColors.SELECTION,
                                state='disabled',
                                wrap='word')
        vsb = ttk.Scrollbar(t_frame, orient='vertical',
                            command=self.terminal.yview)
        self.terminal.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.terminal.pack(fill=tk.BOTH, expand=True)

        # Terminal colour tags
        for tag, color in [
            ('output',  VSColors.TERM_OUTPUT),
            ('error',   VSColors.TERM_ERROR),
            ('success', VSColors.TERM_SUCCESS),
            ('info',    VSColors.TERM_INFO),
            ('prompt',  VSColors.TERM_PROMPT),
            ('warn',    VSColors.TERM_WARN),
            ('dim',     VSColors.TEXT_DIM),
        ]:
            self.terminal.tag_configure(tag, foreground=color)
        self.terminal.tag_configure('bold', font=('Consolas', 11, 'bold'))

        return panel

    # ── Status Bar ─────────────────────────────────────────────

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=VSColors.STATUS_BAR, height=24)
        bar.pack(side=tk.BOTTOM, fill=tk.X)
        bar.pack_propagate(False)

        # Left items
        self.status_branch = tk.Label(
            bar, text=' ⚡ Mistral  ',
            bg=VSColors.STATUS_BAR, fg=VSColors.TEXT_BRIGHT,
            font=('Segoe UI', 9))
        self.status_branch.pack(side=tk.LEFT)

        # Right items
        for text, cmd in [
            ('mistral-fmt', self._format_code),
            ('UTF-8',       None),
        ]:
            lbl = tk.Label(bar, text=f'  {text}  ',
                           bg=VSColors.STATUS_BAR, fg=VSColors.TEXT_BRIGHT,
                           font=('Segoe UI', 9),
                           cursor='hand2' if cmd else 'arrow')
            lbl.pack(side=tk.RIGHT)
            if cmd:
                lbl.bind('<Button-1>', lambda e, c=cmd: c())
                lbl.bind('<Enter>', lambda e, w=lbl:
                         w.configure(bg='#005f9e'))
                lbl.bind('<Leave>', lambda e, w=lbl:
                         w.configure(bg=VSColors.STATUS_BAR))

        self.status_cursor = tk.Label(
            bar, text='  Ln 1, Col 1  ',
            bg=VSColors.STATUS_BAR, fg=VSColors.TEXT_BRIGHT,
            font=('Segoe UI', 9))
        self.status_cursor.pack(side=tk.RIGHT)

    # ── Tab / Editor creation ──────────────────────────────────

    def _new_tab(self, title: str = 'untitled.mst',
                 content: str = '', path: str = None):
        """Create a new editor tab and return its data dict."""
        outer = tk.Frame(self.notebook, bg=VSColors.BG)

        # ── Row 1: editor + line numbers ──
        editor_row = tk.Frame(outer, bg=VSColors.BG)
        editor_row.pack(fill=tk.BOTH, expand=True)

        # Line numbers
        line_nums = tk.Text(editor_row,
                            width=5,
                            bg='#1a1a1a', fg=VSColors.LINE_NUMS,
                            font=('Consolas', 13),
                            state='disabled',
                            relief='flat', bd=0,
                            padx=4, pady=4,
                            selectbackground='#1a1a1a',
                            cursor='arrow')
        line_nums.pack(side=tk.LEFT, fill=tk.Y)

        # Separator line
        tk.Frame(editor_row, bg='#2d2d30', width=1).pack(
            side=tk.LEFT, fill=tk.Y)

        # Editor
        editor = tk.Text(editor_row,
                         bg=VSColors.BG, fg=VSColors.TEXT,
                         font=('Consolas', 13),
                         insertbackground='#aeafad',
                         selectbackground=VSColors.SELECTION,
                         relief='flat', bd=0,
                         padx=12, pady=4,
                         undo=True, autoseparators=True,
                         maxundo=-1,
                         wrap='none',
                         spacing1=1, spacing3=1)

        vsb = ttk.Scrollbar(editor_row, orient='vertical',
                            command=lambda *a: (editor.yview(*a),
                                               self._sync_line_scroll(
                                                   editor, line_nums)))
        hsb = ttk.Scrollbar(outer, orient='horizontal',
                            command=editor.xview)

        editor.configure(yscrollcommand=lambda *a: (
                             vsb.set(*a),
                             self._sync_line_scroll(editor, line_nums)),
                         xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hsb.pack(fill=tk.X)

        # Syntax highlighting colour tags
        self._configure_syntax_tags(editor)

        # Insert content
        if content:
            editor.insert('1.0', content)
            editor.edit_reset()
            self._highlight_syntax(editor)
            self._update_line_numbers(editor, line_nums)

        # Events
        editor.bind('<KeyRelease>',
                    lambda e: self._on_key_release(e, editor, line_nums))
        editor.bind('<ButtonRelease-1>',
                    lambda e: self._on_cursor_move(editor))
        editor.bind('<Tab>',
                    lambda e: self._handle_tab(e, editor))
        editor.bind('<Return>',
                    lambda e: self._handle_return(e, editor))

        # Add tab
        display = f'  {title}  '
        self.notebook.add(outer, text=display)
        self.notebook.select(outer)

        data = {
            'editor':    editor,
            'line_nums': line_nums,
            'path':      path,
            'modified':  False,
            'title':     title,
        }
        self.tab_data[str(outer)] = data
        return data

    def _configure_syntax_tags(self, editor: tk.Text):
        editor.tag_configure('keyword',   foreground=VSColors.SYN_KEYWORD)
        editor.tag_configure('builtin',   foreground=VSColors.SYN_BUILTIN)
        editor.tag_configure('string',    foreground=VSColors.SYN_STRING)
        editor.tag_configure('comment',   foreground=VSColors.SYN_COMMENT)
        editor.tag_configure('number',    foreground=VSColors.SYN_NUMBER)
        editor.tag_configure('class_nm',  foreground=VSColors.SYN_CLASS)
        editor.tag_configure('fn_name',   foreground=VSColors.SYN_FUNC)
        editor.tag_configure('decorator', foreground=VSColors.SYN_DECORATOR)
        editor.tag_configure('self_kw',   foreground=VSColors.SYN_SELF)
        editor.tag_configure('search_hi', background='#515c6a')
        editor.tag_configure('error_ln',  background='#3a1515')

    # ── Syntax Highlighting ────────────────────────────────────

    def _highlight_syntax(self, editor: tk.Text):
        """Full document syntax highlight (debounced)."""
        content = editor.get('1.0', 'end-1c')

        all_tags = ('keyword', 'builtin', 'string', 'comment',
                    'number', 'class_nm', 'fn_name', 'decorator', 'self_kw')
        for t in all_tags:
            editor.tag_remove(t, '1.0', tk.END)

        def apply(tag, pat, content, group=0):
            for m in re.finditer(pat, content, re.MULTILINE):
                s = m.start(group)
                e = m.end(group)
                editor.tag_add(tag, f'1.0+{s}c', f'1.0+{e}c')

        # Comments (must come first so strings inside don't override)
        apply('comment', r'#[^\n]*', content)

        # Multi-line and single-line strings
        apply('string', r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'', content)
        apply('string', r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'', content)

        # Numbers
        apply('number', r'\b\d+\.?\d*(?:[eE][+-]?\d+)?\b', content)

        # Keywords
        kw_pat = r'\b(' + '|'.join(re.escape(k) for k in MISTRAL_KEYWORDS) + r')\b'
        apply('keyword', kw_pat, content)

        # Builtins
        bi_pat = r'\b(' + '|'.join(re.escape(b) for b in MISTRAL_BUILTINS) + r')\b'
        apply('builtin', bi_pat, content)

        # fn <name>
        apply('fn_name', r'\bfn\s+(\w+)', content, group=1)

        # class <Name>
        apply('class_nm', r'\bclass\s+(\w+)', content, group=1)

        # self
        apply('self_kw', r'\bself\b', content)

        # decorators
        apply('decorator', r'@\w+', content)

    def _schedule_highlight(self, editor: tk.Text):
        """Debounce highlighting so typing feels responsive."""
        if self._highlight_after_id:
            self.root.after_cancel(self._highlight_after_id)
        self._highlight_after_id = self.root.after(
            120, lambda: self._highlight_syntax(editor))

    # ── Line Numbers ──────────────────────────────────────────

    def _update_line_numbers(self, editor: tk.Text, line_nums: tk.Text):
        content = editor.get('1.0', tk.END)
        n = content.count('\n')
        width = max(3, len(str(n))) + 1

        line_nums.configure(state='normal', width=width)
        line_nums.delete('1.0', tk.END)
        line_nums.insert(tk.END, '\n'.join(str(i) for i in range(1, n + 1)))
        line_nums.configure(state='disabled')

    def _sync_line_scroll(self, editor: tk.Text, line_nums: tk.Text):
        line_nums.yview_moveto(editor.yview()[0])

    # ── Editor Events ─────────────────────────────────────────

    def _on_key_release(self, event, editor: tk.Text, line_nums: tk.Text):
        self._schedule_highlight(editor)
        self._update_line_numbers(editor, line_nums)
        self._on_cursor_move(editor)

    def _on_cursor_move(self, editor: tk.Text):
        try:
            ln, col = editor.index(tk.INSERT).split('.')
            self.status_cursor.configure(
                text=f'  Ln {ln}, Col {int(col) + 1}  ')
        except Exception:
            pass

    def _handle_tab(self, event, editor: tk.Text):
        # Check if text is selected — indent block
        try:
            sel_start = editor.index('sel.first')
            sel_end   = editor.index('sel.last')
            start_ln  = int(sel_start.split('.')[0])
            end_ln    = int(sel_end.split('.')[0])
            for ln in range(start_ln, end_ln + 1):
                editor.insert(f'{ln}.0', '    ')
            return 'break'
        except tk.TclError:
            pass
        editor.insert(tk.INSERT, '    ')
        return 'break'

    def _handle_return(self, event, editor: tk.Text):
        """Auto-indent on Enter."""
        cur = editor.index(tk.INSERT)
        ln = int(cur.split('.')[0])
        line = editor.get(f'{ln}.0', f'{ln}.end')
        indent = re.match(r'^(\s*)', line).group(1)
        # Extra indent after colon
        if line.rstrip().endswith(':'):
            indent += '    '
        editor.insert(tk.INSERT, '\n' + indent)
        return 'break'

    def _editor_cmd(self, cmd):
        data = self._current_tab()
        if data:
            try:
                data['editor'].event_generate(f'<<{cmd.replace("_", "-").title()}>>')
            except Exception:
                pass

    # ── Tab helpers ───────────────────────────────────────────

    def _current_tab(self) -> dict | None:
        try:
            tab_id = self.notebook.select()
            if not tab_id:
                return None
            frame = self.notebook.nametowidget(tab_id)
            return self.tab_data.get(str(frame))
        except Exception:
            return None

    def _on_tab_changed(self, event):
        data = self._current_tab()
        if data:
            name = data['title']
            self.root.title(f"{name} — Mistral IDE")

    # ── File Operations ───────────────────────────────────────

    def _new_file(self):
        self._new_tab('untitled.mst')
        self._terminal_write('> new file\n', 'dim')

    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[('Mistral', '*.mst'), ('All', '*.*')])
        if not path:
            return
        try:
            content = Path(path).read_text(encoding='utf-8')
            self._new_tab(os.path.basename(path), content, path)
            self._terminal_write(f'> opened: {path}\n', 'info')
        except Exception as ex:
            self._terminal_write(f'> open error: {ex}\n', 'error')

    def _open_folder(self):
        folder = filedialog.askdirectory()
        if not folder:
            return
        self.sidebar_empty.pack_forget()
        self.tree_frame_widget.pack(fill=tk.BOTH, expand=True)
        self._populate_tree(folder)

    def _populate_tree(self, folder: str):
        self.file_tree.delete(*self.file_tree.get_children())
        name = os.path.basename(folder)
        root_node = self.file_tree.insert(
            '', 'end', text=f'📂 {name}', open=True, values=[folder])
        self._tree_recurse(root_node, folder, depth=0)

    def _tree_recurse(self, parent, folder: str, depth: int):
        if depth > 4:
            return
        try:
            entries = sorted(os.listdir(folder))
        except PermissionError:
            return
        dirs  = [e for e in entries
                 if os.path.isdir(os.path.join(folder, e))
                 and not e.startswith('.')]
        files = [e for e in entries
                 if os.path.isfile(os.path.join(folder, e))]
        for d in dirs:
            p = os.path.join(folder, d)
            node = self.file_tree.insert(parent, 'end',
                                         text=f'📁 {d}', values=[p])
            self._tree_recurse(node, p, depth + 1)
        for f in files:
            p = os.path.join(folder, f)
            icon = '🔷' if f.endswith('.mst') else '📄'
            self.file_tree.insert(parent, 'end',
                                  text=f'{icon} {f}', values=[p])

    def _on_tree_dblclick(self, event):
        item = self.file_tree.focus()
        vals = self.file_tree.item(item, 'values')
        if vals and os.path.isfile(vals[0]):
            path = vals[0]
            try:
                content = Path(path).read_text(encoding='utf-8')
                self._new_tab(os.path.basename(path), content, path)
            except Exception as ex:
                self._terminal_write(f'> {ex}\n', 'error')

    def _save_file(self):
        data = self._current_tab()
        if not data:
            return
        if data['path']:
            self._write_file(data['path'], data['editor'].get('1.0', tk.END))
        else:
            self._save_file_as()

    def _save_file_as(self):
        data = self._current_tab()
        if not data:
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.mst',
            filetypes=[('Mistral', '*.mst'), ('All', '*.*')])
        if not path:
            return
        data['path']  = path
        data['title'] = os.path.basename(path)
        self._write_file(path, data['editor'].get('1.0', tk.END))
        tab_id = self.notebook.select()
        self.notebook.tab(tab_id, text=f"  {data['title']}  ")

    def _write_file(self, path: str, content: str):
        try:
            Path(path).write_text(content, encoding='utf-8')
            self._terminal_write(f'> saved: {path}\n', 'success')
        except Exception as ex:
            self._terminal_write(f'> save error: {ex}\n', 'error')

    # ── Formatter ─────────────────────────────────────────────

    def _format_code(self):
        data = self._current_tab()
        if not data:
            return
        editor = data['editor']
        original = editor.get('1.0', tk.END)
        try:
            formatted = self.formatter.format(original)
            report    = self.formatter.format_report(original, formatted)
            cursor    = editor.index(tk.INSERT)
            editor.delete('1.0', tk.END)
            editor.insert('1.0', formatted)
            try:
                editor.mark_set(tk.INSERT, cursor)
            except Exception:
                pass
            self._highlight_syntax(editor)
            self._update_line_numbers(editor, data['line_nums'])
            self._terminal_write(f'> {report}\n', 'success')
        except Exception as ex:
            self._terminal_write(f'> mistral-fmt error: {ex}\n', 'error')

    # ── Runner ────────────────────────────────────────────────

    def _run_code(self):
        data = self._current_tab()
        if not data:
            return
        source = data['editor'].get('1.0', tk.END)
        self._terminal_write('\n', 'output')
        self._terminal_write('━' * 56 + '\n', 'dim')
        self._terminal_write('▶  Running Mistral program\n', 'prompt')
        self._terminal_write('━' * 56 + '\n', 'dim')

        def worker():
            try:
                python_src = self.transpiler.transpile(source)
            except Exception as ex:
                self.root.after(0, self._terminal_write,
                                f'Transpile error: {ex}\n', 'error')
                return

            captured_out = io.StringIO()
            captured_err = io.StringIO()
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout = captured_out
            sys.stderr = captured_err
            exec_error = None
            try:
                globs = {
                    '__name__': '__main__',
                    '__builtins__': __builtins__,
                }
                exec(compile(python_src, '<mistral>', 'exec'), globs)
            except SystemExit:
                pass
            except Exception:
                exec_error = traceback.format_exc()
            finally:
                sys.stdout = old_out
                sys.stderr = old_err

            out = captured_out.getvalue()
            err = captured_err.getvalue()

            def update():
                if out:
                    self._terminal_write(out, 'output')
                if err:
                    self._terminal_write(err, 'warn')
                if exec_error:
                    self._terminal_write(exec_error, 'error')
                tag = 'success' if not exec_error else 'error'
                msg = 'Program finished.' if not exec_error else 'Program exited with error.'
                self._terminal_write('━' * 56 + '\n', 'dim')
                self._terminal_write(f'{msg}\n', tag)

            self.root.after(0, update)

        threading.Thread(target=worker, daemon=True).start()

    def _format_and_run(self):
        self._format_code()
        self.root.after(300, self._run_code)

    # ── Terminal helpers ──────────────────────────────────────

    def _terminal_write(self, text: str, tag: str = 'output'):
        self.terminal.configure(state='normal')
        self.terminal.insert(tk.END, text, tag)
        self.terminal.see(tk.END)
        self.terminal.configure(state='disabled')

    def _clear_terminal(self):
        self.terminal.configure(state='normal')
        self.terminal.delete('1.0', tk.END)
        self.terminal.configure(state='disabled')

    def _toggle_terminal(self):
        if self.terminal_visible:
            self.v_pane.forget(self.terminal_panel)
            self.terminal_visible = False
        else:
            self.v_pane.add(self.terminal_panel, minsize=80, height=200)
            self.terminal_visible = True

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.h_pane.forget(self.sidebar_frame)
            self.sidebar_visible = False
        else:
            self.h_pane.insert(0, self.sidebar_frame, minsize=120, width=220)
            self.sidebar_visible = True

    # ── Find / Replace ────────────────────────────────────────

    def _find_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('Find')
        dlg.geometry('400x120')
        dlg.configure(bg=VSColors.SIDEBAR_BG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        def row(label, var, r):
            tk.Label(dlg, text=label,
                     bg=VSColors.SIDEBAR_BG, fg=VSColors.TEXT_MUTED,
                     font=('Segoe UI', 10), width=8, anchor='e').grid(
                row=r, column=0, padx=(10, 4), pady=6)
            e = tk.Entry(dlg, textvariable=var,
                         bg='#3c3c3c', fg=VSColors.TEXT_BRIGHT,
                         insertbackground=VSColors.TEXT_BRIGHT,
                         font=('Consolas', 11), relief='flat', bd=4, width=28)
            e.grid(row=r, column=1, padx=4, pady=6)
            return e

        find_var = tk.StringVar()
        fe = row('Find:', find_var, 0)
        fe.focus()

        def do_find():
            data = self._current_tab()
            if not data:
                return
            editor = data['editor']
            editor.tag_remove('search_hi', '1.0', tk.END)
            q = find_var.get()
            if not q:
                return
            pos = '1.0'
            count = 0
            first = None
            while True:
                idx = editor.search(q, pos, tk.END)
                if not idx:
                    break
                end = f'{idx}+{len(q)}c'
                editor.tag_add('search_hi', idx, end)
                if first is None:
                    first = idx
                pos = end
                count += 1
            if first:
                editor.see(first)
            self._terminal_write(
                f'> find "{q}": {count} match(es)\n', 'info')

        btn_frame = tk.Frame(dlg, bg=VSColors.SIDEBAR_BG)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=6)
        tk.Button(btn_frame, text='Find All',
                  bg=VSColors.ACCENT, fg=VSColors.TEXT_BRIGHT,
                  font=('Segoe UI', 10), relief='flat', bd=0,
                  padx=14, pady=4, cursor='hand2',
                  command=do_find).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text='Close',
                  bg='#3c3c3c', fg=VSColors.TEXT_MUTED,
                  font=('Segoe UI', 10), relief='flat', bd=0,
                  padx=14, pady=4, cursor='hand2',
                  command=dlg.destroy).pack(side=tk.LEFT, padx=4)
        fe.bind('<Return>', lambda e: do_find())

    def _replace_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('Find & Replace')
        dlg.geometry('420x160')
        dlg.configure(bg=VSColors.SIDEBAR_BG)
        dlg.transient(self.root)
        dlg.resizable(False, False)

        find_var    = tk.StringVar()
        replace_var = tk.StringVar()

        def row(label, var, r):
            tk.Label(dlg, text=label,
                     bg=VSColors.SIDEBAR_BG, fg=VSColors.TEXT_MUTED,
                     font=('Segoe UI', 10), width=9, anchor='e').grid(
                row=r, column=0, padx=(10, 4), pady=6)
            e = tk.Entry(dlg, textvariable=var,
                         bg='#3c3c3c', fg=VSColors.TEXT_BRIGHT,
                         insertbackground=VSColors.TEXT_BRIGHT,
                         font=('Consolas', 11), relief='flat', bd=4, width=26)
            e.grid(row=r, column=1, padx=4, pady=6)
            return e

        fe = row('Find:',    find_var,    0)
        re_ = row('Replace:', replace_var, 1)
        fe.focus()

        def do_replace_all():
            data = self._current_tab()
            if not data:
                return
            editor = data['editor']
            content = editor.get('1.0', tk.END)
            q = find_var.get()
            r = replace_var.get()
            if not q:
                return
            new_content = content.replace(q, r)
            count = content.count(q)
            editor.delete('1.0', tk.END)
            editor.insert('1.0', new_content)
            self._highlight_syntax(editor)
            self._terminal_write(
                f'> replaced {count} occurrence(s) of "{q}"\n', 'success')

        btn_frame = tk.Frame(dlg, bg=VSColors.SIDEBAR_BG)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=8)
        tk.Button(btn_frame, text='Replace All',
                  bg=VSColors.ACCENT, fg=VSColors.TEXT_BRIGHT,
                  font=('Segoe UI', 10), relief='flat', bd=0,
                  padx=14, pady=4, cursor='hand2',
                  command=do_replace_all).pack(side=tk.LEFT, padx=4)
        tk.Button(btn_frame, text='Close',
                  bg='#3c3c3c', fg=VSColors.TEXT_MUTED,
                  font=('Segoe UI', 10), relief='flat', bd=0,
                  padx=14, pady=4, cursor='hand2',
                  command=dlg.destroy).pack(side=tk.LEFT, padx=4)

    # ── Keyboard shortcuts ─────────────────────────────────────

    def _bind_shortcuts(self):
        bind = self.root.bind
        bind('<Control-n>',       lambda e: self._new_file())
        bind('<Control-o>',       lambda e: self._open_file())
        bind('<Control-s>',       lambda e: self._save_file())
        bind('<Control-S>',       lambda e: self._save_file_as())
        bind('<Control-f>',       lambda e: self._find_dialog())
        bind('<Control-h>',       lambda e: self._replace_dialog())
        bind('<Control-b>',       lambda e: self._toggle_sidebar())
        bind('<Control-grave>',   lambda e: self._toggle_terminal())
        bind('<F5>',              lambda e: self._run_code())
        bind('<F6>',              lambda e: self._format_and_run())
        bind('<Alt-F>',           lambda e: self._format_code())

    # ── Info dialogs ──────────────────────────────────────────

    def _show_reference(self):
        dlg = tk.Toplevel(self.root)
        dlg.title('Mistral Syntax Reference')
        dlg.geometry('680x560')
        dlg.configure(bg=VSColors.BG)
        dlg.transient(self.root)

        txt = tk.Text(dlg, bg=VSColors.BG, fg=VSColors.TEXT,
                      font=('Consolas', 12),
                      relief='flat', bd=0, padx=20, pady=16,
                      wrap='word', state='normal')
        vsb = ttk.Scrollbar(dlg, orient='vertical', command=txt.yview)
        txt.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        txt.pack(fill=tk.BOTH, expand=True)

        self._configure_syntax_tags(txt)

        ref = '''MISTRAL LANGUAGE — SYNTAX REFERENCE
══════════════════════════════════════

FUNCTIONS
─────────
  fn greet(name :: str) -> str:
      return "Hello, " + name

VARIABLES
─────────
  let x = 42          # let is optional
  count = 0           # also valid

CONDITIONALS
────────────
  when x > 10:
      echo("big")
  orwhen x == 10:
      echo("exactly 10")
  otherwise:
      echo("small")

LOOPS
─────
  loop item in collection:
      echo(item)

  repeat condition:
      do_something()

CLASSES
───────
  class Animal:
      fn __init__(self, name :: str):
          self.name = name

      fn speak(self) -> str:
          return f"{self.name} speaks"

EXCEPTIONS
──────────
  try:
      risky_operation()
  catch ValueError as e:
      echo(f"Caught: {e}")
  finally:
      cleanup()

LITERALS
────────
  true   →  True
  false  →  False
  null   →  None
  echo   →  print

TYPE ANNOTATIONS  (optional, stripped at runtime)
────────────────
  fn add(a :: int, b :: int) -> int:
      return a + b

COMMENTS
────────
  # Single-line comment

F-STRINGS & STRING FEATURES
────────────────────────────
  fn introduce(name :: str, age :: int):
      echo(f"I am {name}, age {age}")
'''

        txt.insert('1.0', ref)
        self._highlight_syntax(txt)
        txt.configure(state='disabled')

    def _show_about(self):
        messagebox.showinfo(
            'About Mistral',
            'Mistral IDE  v1.0.0\n\n'
            'Mistral is a clean, readable programming language\n'
            'inspired by Python with simplified syntax.\n\n'
            'Includes:\n'
            '  • Full Mistral language interpreter\n'
            '  • mistral-fmt auto-formatter\n'
            '  • VS Code-style editor\n'
            '  • Syntax highlighting\n'
            '  • Multi-file tabs\n\n'
            'Keyboard shortcuts:\n'
            '  F5           Run file\n'
            '  F6           Format & Run\n'
            '  Alt+Shift+F  Format (mistral-fmt)\n'
            '  Ctrl+N/O/S   New / Open / Save\n'
            '  Ctrl+F/H     Find / Replace\n'
            '  Ctrl+B       Toggle sidebar\n'
            '  Ctrl+`       Toggle terminal'
        )


# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.title('Mistral IDE')

    # DPI awareness (Windows)
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = MistralIDE(root)
    root.mainloop()


if __name__ == '__main__':
    main()
