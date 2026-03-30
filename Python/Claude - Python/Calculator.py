import tkinter as tk
from tkinter import font


class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculator")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.expression = ""
        self.result_var = tk.StringVar()
        self.result_var.set("0")

        self.create_widgets()

    def create_widgets(self):
        # Display frame
        display_frame = tk.Frame(self.root, bg="#1e1e1e")
        display_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Result display
        result_font = font.Font(family="Segoe UI", size=48, weight="normal")
        result_label = tk.Label(
            display_frame,
            textvariable=self.result_var,
            font=result_font,
            bg="#1e1e1e",
            fg="#ffffff",
            anchor="e",
            padx=10
        )
        result_label.pack(expand=True, fill="both")

        # Button frame
        button_frame = tk.Frame(self.root, bg="#1e1e1e")
        button_frame.pack(padx=20, pady=(0, 20))

        # Button layout
        buttons = [
            ['C', '⌫', '%', '/'],
            ['7', '8', '9', '×'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['±', '0', '.', '=']
        ]

        button_font = font.Font(family="Segoe UI", size=20, weight="normal")

        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                # Color scheme
                if btn_text in ['C', '⌫', '±', '%']:
                    bg_color = "#505050"
                    fg_color = "#ffffff"
                    active_bg = "#606060"
                elif btn_text in ['/', '×', '-', '+', '=']:
                    bg_color = "#ff9500"
                    fg_color = "#ffffff"
                    active_bg = "#ffb143"
                else:
                    bg_color = "#333333"
                    fg_color = "#ffffff"
                    active_bg = "#404040"

                btn = tk.Button(
                    button_frame,
                    text=btn_text,
                    font=button_font,
                    bg=bg_color,
                    fg=fg_color,
                    activebackground=active_bg,
                    activeforeground=fg_color,
                    bd=0,
                    highlightthickness=0,
                    command=lambda x=btn_text: self.on_button_click(x)
                )

                btn.grid(row=i, column=j, sticky="nsew", padx=5, pady=5)

        # Configure grid weights for responsive sizing
        for i in range(5):
            button_frame.grid_rowconfigure(i, weight=1, minsize=70)
        for j in range(4):
            button_frame.grid_columnconfigure(j, weight=1, minsize=70)

    def on_button_click(self, char):
        if char == 'C':
            self.expression = ""
            self.result_var.set("0")
        elif char == '⌫':
            self.expression = self.expression[:-1]
            self.result_var.set(self.expression if self.expression else "0")
        elif char == '=':
            try:
                # Replace display symbols with Python operators
                calc_expr = self.expression.replace('×', '*').replace('÷', '/')
                result = eval(calc_expr)
                # Format result
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 10)
                self.result_var.set(str(result))
                self.expression = str(result)
            except:
                self.result_var.set("Error")
                self.expression = ""
        elif char == '±':
            if self.expression and self.expression != "0":
                if self.expression[0] == '-':
                    self.expression = self.expression[1:]
                else:
                    self.expression = '-' + self.expression
                self.result_var.set(self.expression)
        else:
            if self.result_var.get() == "Error":
                self.expression = ""

            # Prevent multiple decimal points
            if char == '.':
                parts = self.expression.split()
                if parts and '.' in parts[-1]:
                    return

            self.expression += char
            self.result_var.set(self.expression)


if __name__ == "__main__":
    root = tk.Tk()
    calculator = Calculator(root)
    root.mainloop()
