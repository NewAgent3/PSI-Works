# Mistral IDE

A VS Code-style IDE for the **Mistral programming language**, built entirely in Python using Tkinter.

## 🚀 How to Run

```bash
python3 mistral_ide.py
```

**Requires:** Python 3.10+ (uses Tkinter, which ships with standard Python)

---

## ⌨️ Keyboard Shortcuts

| Shortcut       | Action                        |
|----------------|-------------------------------|
| `F5`           | Run current file              |
| `F6`           | Format & Run                  |
| `Alt+Shift+F`  | Format with mistral-fmt       |
| `Ctrl+N`       | New file                      |
| `Ctrl+O`       | Open file                     |
| `Ctrl+S`       | Save                          |
| `Ctrl+Shift+S` | Save As                       |
| `Ctrl+F`       | Find                          |
| `Ctrl+H`       | Find & Replace                |
| `Ctrl+B`       | Toggle sidebar                |
| `Ctrl+\``      | Toggle terminal               |

---

## 🌀 Mistral Language Reference

Mistral is a Python-like language with cleaner keywords:

| Mistral       | Python     | Meaning              |
|---------------|------------|----------------------|
| `fn`          | `def`      | Function definition  |
| `when`        | `if`       | Conditional          |
| `orwhen`      | `elif`     | Else-if              |
| `otherwise`   | `else`     | Fallback             |
| `repeat`      | `while`    | While loop           |
| `loop`        | `for`      | For loop             |
| `true`        | `True`     | Boolean true         |
| `false`       | `False`    | Boolean false        |
| `null`        | `None`     | Null value           |
| `echo`        | `print`    | Print output         |
| `let`         | *(none)*   | Optional var keyword |
| `catch`       | `except`   | Exception catch      |
| `x :: int`    | `x: int`   | Type annotation      |

### Example

```mistral
fn greet(name :: str) -> str:
    let msg = f"Hello, {name}!"
    return msg


fn main():
    loop i in range(3):
        when i % 2 == 0:
            echo(greet("World"))
        otherwise:
            echo("odd:", i)

    repeat false:
        pass  # never runs


main()
```

---

## 🛠 mistral-fmt

The built-in formatter (like `autopep8`) automatically:

- Removes trailing whitespace
- Ensures 2 blank lines before `fn` and `class` definitions
- Adds spaces around operators (`=`, `==`, `+=`, etc.)
- Fixes comma spacing (`a,b` → `a, b`)
- Normalises keyword spacing
- Collapses excessive blank lines

Trigger with **Alt+Shift+F** or click **mistral-fmt** in the status bar.

---

## 📁 File Structure

```
mistral_ide.py          ← Main IDE application
examples/
  hello_mistral.mst     ← Example Mistral program
README.md
```

---

## Features

- ✅ Full Mistral syntax (transpiles to Python at runtime)
- ✅ Syntax highlighting (keywords, strings, comments, functions, classes…)
- ✅ Auto-indent on Enter
- ✅ 4-space Tab handling
- ✅ Line numbers
- ✅ Multi-file tabs
- ✅ File explorer sidebar
- ✅ Integrated terminal / output panel
- ✅ **mistral-fmt** auto-formatter
- ✅ Find & Replace
- ✅ VS Code dark theme
