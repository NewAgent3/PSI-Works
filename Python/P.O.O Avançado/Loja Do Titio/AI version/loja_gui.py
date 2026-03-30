import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import date, datetime
from dataclasses import dataclass, field
from typing import Optional
import random

# ──────────────────────────────────────────────
#  DATA CLASSES
# ──────────────────────────────────────────────

@dataclass
class Produto:
    nome: str
    preco: float
    categoria: str
    stock_min: int
    stock_max: int
    stock_atual: int = 0

    def alterar_stock_min(self, novo_stock: int):
        self.stock_min = novo_stock

    def alterar_stock_max(self, novo_stock: int):
        self.stock_max = novo_stock

    def __str__(self):
        return f"{self.nome} (€{self.preco:.2f})"


@dataclass
class Cliente:
    id_cartao: int
    nome: str
    morada: str
    telefone: str

    def __str__(self):
        return f"[{self.id_cartao}] {self.nome}"


@dataclass
class Funcionario:
    nome: str
    morada: str
    telefone: str
    data_nascimento: date
    salario_base: float

    def calcular_idade(self) -> int:
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )

    def calcular_salario_liquido(self) -> float:
        return self.salario_base * 0.75  # 25% impostos

    def comparar_salario_base(self, outro: 'Funcionario') -> str:
        diff = self.salario_base - outro.salario_base
        if diff > 0:
            return f"{self.nome} ganha mais €{diff:.2f}"
        elif diff < 0:
            return f"{outro.nome} ganha mais €{-diff:.2f}"
        return "Salários iguais"

    def tipo(self):
        return "Funcionário"

    def __str__(self):
        return f"{self.nome} ({self.tipo()})"


@dataclass
class Armazem(Funcionario):
    cartao_ativo: bool = True
    estado_entrada: bool = False

    def entrada(self):
        if self.cartao_ativo:
            self.estado_entrada = True
            return f"{self.nome} entrou no armazém."
        return "Cartão inativo!"

    def saida(self):
        self.estado_entrada = False
        return f"{self.nome} saiu do armazém."

    def alterar_acesso(self):
        self.cartao_ativo = not self.cartao_ativo
        return f"Acesso {'ativado' if self.cartao_ativo else 'desativado'}."

    def tipo(self):
        return "Armazém"


@dataclass
class Limpeza(Funcionario):
    horas_extra: int = 0

    def calcular_salario_liquido(self) -> float:
        extra = self.horas_extra * 12.5
        return (self.salario_base + extra) * 0.75

    def tipo(self):
        return "Limpeza"


@dataclass
class Caixa(Funcionario):
    subsidio_risco: float = 0.0

    def calcular_salario_liquido(self) -> float:
        return (self.salario_base + self.subsidio_risco) * 0.75

    def tipo(self):
        return "Caixa"


@dataclass
class Venda:
    id_fatura: int
    produtos: list
    vendedor: Caixa
    cliente: Cliente

    def fazer_fatura(self) -> str:
        total = sum(p.preco for p in self.produtos)
        linhas = [
            "═" * 40,
            f"  FATURA Nº {self.id_fatura}",
            "═" * 40,
            f"  Cliente : {self.cliente.nome}",
            f"  Vendedor: {self.vendedor.nome}",
            f"  Data    : {date.today().strftime('%d/%m/%Y')}",
            "─" * 40,
        ]
        for p in self.produtos:
            linhas.append(f"  {p.nome:<22} €{p.preco:>6.2f}")
        linhas += [
            "─" * 40,
            f"  TOTAL{'':>20} €{total:>6.2f}",
            "═" * 40,
        ]
        return "\n".join(linhas)

    def total(self) -> float:
        return sum(p.preco for p in self.produtos)


@dataclass
class Loja:
    lista_funcionarios: list = field(default_factory=list)
    lista_produtos: list = field(default_factory=list)
    clientes_registrados: list = field(default_factory=list)
    lista_vendas: list = field(default_factory=list)

    def adicionar_funcionario(self, f: Funcionario):
        self.lista_funcionarios.append(f)

    def adicionar_produto(self, p: Produto):
        self.lista_produtos.append(p)

    def registrar_cliente(self, c: Cliente):
        self.clientes_registrados.append(c)

    def registrar_venda(self, v: Venda):
        self.lista_vendas.append(v)


# ──────────────────────────────────────────────
#  THEME
# ──────────────────────────────────────────────

BG       = "#0f1117"
CARD     = "#1a1d27"
CARD2    = "#22263a"
ACCENT   = "#4f8ef7"
ACCENT2  = "#7c5cbf"
SUCCESS  = "#3ecf8e"
WARN     = "#f5a623"
DANGER   = "#e05260"
TEXT     = "#e2e8f0"
MUTED    = "#64748b"
BORDER   = "#2d3148"
SIDEBAR  = "#13151f"

NAV_ITEMS = [
    ("🏠", "Dashboard"),
    ("👥", "Funcionários"),
    ("📦", "Produtos"),
    ("🧑‍💼", "Clientes"),
    ("🛒", "Vendas"),
]


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def make_entry(parent, placeholder="", show=None, **kwargs):
    e = tk.Entry(parent, bg=CARD2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=0, font=("Courier New", 11),
                 highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, **kwargs)
    if show:
        e.config(show=show)
    if placeholder:
        e.insert(0, placeholder)
        e.config(fg=MUTED)
        def on_focus_in(event, p=placeholder):
            if e.get() == p:
                e.delete(0, tk.END)
                e.config(fg=TEXT)
        def on_focus_out(event, p=placeholder):
            if not e.get():
                e.insert(0, p)
                e.config(fg=MUTED)
        e.bind("<FocusIn>", on_focus_in)
        e.bind("<FocusOut>", on_focus_out)
    return e


def make_label(parent, text, size=11, color=TEXT, bold=False, **kwargs):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=parent["bg"] if hasattr(parent, "__getitem__") else BG,
                    fg=color, font=("Courier New", size, weight), **kwargs)


def make_button(parent, text, cmd, color=ACCENT, fg=BG, width=16, **kwargs):
    btn = tk.Button(parent, text=text, command=cmd,
                    bg=color, fg=fg, activebackground=color,
                    activeforeground=fg, relief="flat", bd=0,
                    font=("Courier New", 10, "bold"),
                    cursor="hand2", width=width, pady=6, **kwargs)
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _lighten(hex_color):
    r, g, b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
    r, g, b = min(r+30, 255), min(g+30, 255), min(b+30, 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def card_frame(parent, **kwargs):
    f = tk.Frame(parent, bg=CARD, bd=0, highlightthickness=1,
                 highlightbackground=BORDER, **kwargs)
    return f


def section_title(parent, text):
    tk.Label(parent, text=text, bg=parent["bg"],
             fg=ACCENT, font=("Courier New", 13, "bold")).pack(anchor="w", pady=(0, 8))


# ──────────────────────────────────────────────
#  MAIN APP
# ──────────────────────────────────────────────

class LojaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Loja Manager")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.resizable(True, True)

        # seed demo data
        self.loja = Loja()
        self._seed_data()

        self._build_ui()

    def _seed_data(self):
        self.loja.adicionar_produto(Produto("Leite Bio", 1.29, "Alimentação", 10, 200, 45))
        self.loja.adicionar_produto(Produto("Pão de Forma", 1.89, "Alimentação", 5, 100, 22))
        self.loja.adicionar_produto(Produto("Detergente Ariel", 8.49, "Limpeza", 3, 50, 18))
        self.loja.adicionar_produto(Produto("Iogurte Natural", 0.59, "Lacticínios", 20, 150, 67))
        self.loja.adicionar_produto(Produto("Sumo de Laranja", 2.19, "Bebidas", 8, 80, 30))

        c1 = Caixa("Ana Silva", "Rua das Flores 12", "912345678",
                   date(1990, 3, 15), 950.0, subsidio_risco=75.0)
        c2 = Caixa("Bruno Costa", "Av. da Liberdade 5", "934567890",
                   date(1985, 7, 22), 1000.0, subsidio_risco=75.0)
        a1 = Armazem("Carlos Maia", "Beco das Pedras 3", "961234567",
                     date(1978, 11, 5), 870.0, cartao_ativo=True)
        l1 = Limpeza("Dulce Ferreira", "Rua Nova 77", "924681357",
                     date(1995, 6, 8), 820.0, horas_extra=4)
        for f in [c1, c2, a1, l1]:
            self.loja.adicionar_funcionario(f)

        cl1 = Cliente(1001, "Maria João", "Largo do Mercado 2", "963852741")
        cl2 = Cliente(1002, "Pedro Alves", "Rua do Sol 88", "917654321")
        cl3 = Cliente(1003, "Sofia Pinto", "Alameda Central 14", "965432198")
        for c in [cl1, cl2, cl3]:
            self.loja.registrar_cliente(c)

        v1 = Venda(1001, [self.loja.lista_produtos[0], self.loja.lista_produtos[1]], c1, cl1)
        v2 = Venda(1002, [self.loja.lista_produtos[2], self.loja.lista_produtos[4]], c2, cl2)
        for v in [v1, v2]:
            self.loja.registrar_venda(v)

    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = tk.Label(self.sidebar, text="🛍  LOJA", bg=SIDEBAR,
                        fg=ACCENT, font=("Courier New", 16, "bold"), pady=24)
        logo.pack()

        tk.Frame(self.sidebar, bg=BORDER, height=1).pack(fill="x", padx=12)

        self.nav_btns = []
        self.current_page = tk.StringVar(value="Dashboard")
        for icon, label in NAV_ITEMS:
            self._nav_button(icon, label)

        tk.Frame(self.sidebar, bg=SIDEBAR).pack(fill="y", expand=True)
        ver = tk.Label(self.sidebar, text="v1.0  ·  Python/Tk", bg=SIDEBAR,
                       fg=MUTED, font=("Courier New", 8), pady=10)
        ver.pack()

        # Main area
        self.main = tk.Frame(self, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        self.pages = {}
        for _, name in NAV_ITEMS:
            frame = tk.Frame(self.main, bg=BG)
            self.pages[name] = frame
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_dashboard()
        self._build_funcionarios()
        self._build_produtos()
        self._build_clientes()
        self._build_vendas()

        self._show_page("Dashboard")

    def _nav_button(self, icon, label):
        full = f"  {icon}  {label}"
        btn = tk.Button(self.sidebar, text=full, bg=SIDEBAR, fg=MUTED,
                        activebackground=CARD, activeforeground=ACCENT,
                        relief="flat", bd=0, anchor="w",
                        font=("Courier New", 11), cursor="hand2",
                        pady=10, padx=8,
                        command=lambda l=label: self._show_page(l))
        btn.pack(fill="x", padx=8, pady=2)
        self.nav_btns.append((label, btn))

    def _show_page(self, name):
        self.current_page.set(name)
        for lbl, btn in self.nav_btns:
            if lbl == name:
                btn.config(bg=CARD, fg=ACCENT)
            else:
                btn.config(bg=SIDEBAR, fg=MUTED)
        self.pages[name].lift()
        if name == "Dashboard":
            self._refresh_dashboard()

    # ─── DASHBOARD ────────────────────────────────
    def _build_dashboard(self):
        p = self.pages["Dashboard"]
        tk.Label(p, text="Dashboard", bg=BG, fg=TEXT,
                 font=("Courier New", 20, "bold")).pack(anchor="w", padx=32, pady=(28, 4))
        tk.Label(p, text="Visão geral da loja", bg=BG, fg=MUTED,
                 font=("Courier New", 10)).pack(anchor="w", padx=32, pady=(0, 20))

        self.dash_cards_frame = tk.Frame(p, bg=BG)
        self.dash_cards_frame.pack(fill="x", padx=32)

        self.dash_cards = {}
        metrics = [
            ("Funcionários", "👥", ACCENT),
            ("Produtos",     "📦", SUCCESS),
            ("Clientes",     "🧑‍💼", WARN),
            ("Vendas",       "🛒", ACCENT2),
        ]
        for i, (lbl, icon, color) in enumerate(metrics):
            c = card_frame(self.dash_cards_frame, padx=20, pady=16)
            c.grid(row=0, column=i, padx=8, pady=4, sticky="ew")
            self.dash_cards_frame.columnconfigure(i, weight=1)
            tk.Label(c, text=icon, bg=CARD, fg=color,
                     font=("Courier New", 22)).pack(anchor="w")
            val = tk.Label(c, text="0", bg=CARD, fg=color,
                           font=("Courier New", 26, "bold"))
            val.pack(anchor="w")
            tk.Label(c, text=lbl, bg=CARD, fg=MUTED,
                     font=("Courier New", 10)).pack(anchor="w")
            self.dash_cards[lbl] = val

        # Recent sales
        bot = tk.Frame(p, bg=BG)
        bot.pack(fill="both", expand=True, padx=32, pady=20)
        bot.columnconfigure(0, weight=3)
        bot.columnconfigure(1, weight=2)
        bot.rowconfigure(0, weight=1)

        left = card_frame(bot, padx=16, pady=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tk.Label(left, text="Vendas Recentes", bg=CARD, fg=TEXT,
                 font=("Courier New", 12, "bold")).pack(anchor="w", pady=(0, 8))

        cols = ("Fatura", "Cliente", "Vendedor", "Total")
        self.dash_tree = ttk.Treeview(left, columns=cols, show="headings", height=8)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=CARD2, foreground=TEXT,
                        fieldbackground=CARD2, rowheight=28,
                        font=("Courier New", 10))
        style.configure("Treeview.Heading", background=CARD, foreground=ACCENT,
                        font=("Courier New", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ACCENT2)])

        for col in cols:
            self.dash_tree.heading(col, text=col)
            self.dash_tree.column(col, width=120, anchor="center")
        self.dash_tree.pack(fill="both", expand=True)

        right = card_frame(bot, padx=16, pady=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(right, text="Stock Baixo ⚠", bg=CARD, fg=WARN,
                 font=("Courier New", 12, "bold")).pack(anchor="w", pady=(0, 8))
        self.stock_frame = tk.Frame(right, bg=CARD)
        self.stock_frame.pack(fill="both", expand=True)

    def _refresh_dashboard(self):
        self.dash_cards["Funcionários"].config(text=str(len(self.loja.lista_funcionarios)))
        self.dash_cards["Produtos"].config(text=str(len(self.loja.lista_produtos)))
        self.dash_cards["Clientes"].config(text=str(len(self.loja.clientes_registrados)))
        self.dash_cards["Vendas"].config(text=str(len(self.loja.lista_vendas)))

        self.dash_tree.delete(*self.dash_tree.get_children())
        for v in self.loja.lista_vendas[-8:]:
            self.dash_tree.insert("", "end", values=(
                f"#{v.id_fatura}", v.cliente.nome, v.vendedor.nome, f"€{v.total():.2f}"
            ))

        for w in self.stock_frame.winfo_children():
            w.destroy()
        low = [p for p in self.loja.lista_produtos if p.stock_atual <= p.stock_min]
        if low:
            for p in low:
                row = tk.Frame(self.stock_frame, bg=CARD)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"• {p.nome}", bg=CARD, fg=WARN,
                         font=("Courier New", 10)).pack(side="left")
                tk.Label(row, text=f"  {p.stock_atual}/{p.stock_min}", bg=CARD, fg=DANGER,
                         font=("Courier New", 10, "bold")).pack(side="right")
        else:
            tk.Label(self.stock_frame, text="✓  Todos os stocks OK", bg=CARD,
                     fg=SUCCESS, font=("Courier New", 11)).pack(pady=20)

    # ─── FUNCIONÁRIOS ─────────────────────────────
    def _build_funcionarios(self):
        p = self.pages["Funcionários"]
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 4))
        tk.Label(hdr, text="Funcionários", bg=BG, fg=TEXT,
                 font=("Courier New", 20, "bold")).pack(side="left")
        make_button(hdr, "+ Novo Funcionário", self._open_add_func,
                    color=ACCENT).pack(side="right", pady=4)

        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=8)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # List
        lst = card_frame(body, padx=12, pady=12)
        lst.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        cols = ("Nome", "Tipo", "Salário Base", "Salário Líquido", "Idade")
        self.func_tree = ttk.Treeview(lst, columns=cols, show="headings", height=18)
        for col in cols:
            self.func_tree.heading(col, text=col)
            self.func_tree.column(col, width=110, anchor="center")
        self.func_tree.pack(fill="both", expand=True)
        self.func_tree.bind("<<TreeviewSelect>>", self._on_func_select)

        # Detail panel
        self.func_detail = card_frame(body, padx=16, pady=16)
        self.func_detail.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.func_detail_lbl = tk.Label(self.func_detail, text="Selecione um\nfuncionário",
                                         bg=CARD, fg=MUTED, font=("Courier New", 11),
                                         justify="center")
        self.func_detail_lbl.pack(expand=True)

        self._refresh_func_tree()

    def _refresh_func_tree(self):
        self.func_tree.delete(*self.func_tree.get_children())
        for f in self.loja.lista_funcionarios:
            self.func_tree.insert("", "end", values=(
                f.nome, f.tipo(),
                f"€{f.salario_base:.2f}",
                f"€{f.calcular_salario_liquido():.2f}",
                f.calcular_idade()
            ))

    def _on_func_select(self, event):
        sel = self.func_tree.selection()
        if not sel:
            return
        idx = self.func_tree.index(sel[0])
        f = self.loja.lista_funcionarios[idx]
        for w in self.func_detail.winfo_children():
            w.destroy()

        tk.Label(self.func_detail, text=f.nome, bg=CARD, fg=ACCENT,
                 font=("Courier New", 14, "bold")).pack(anchor="w", pady=(0, 4))
        tag_colors = {"Caixa": ACCENT, "Armazém": SUCCESS, "Limpeza": WARN}
        color = tag_colors.get(f.tipo(), MUTED)
        tk.Label(self.func_detail, text=f"[ {f.tipo()} ]", bg=CARD,
                 fg=color, font=("Courier New", 10, "bold")).pack(anchor="w", pady=(0, 12))

        details = [
            ("📍 Morada",       f.morada),
            ("📞 Telefone",     f.telefone),
            ("🎂 Nascimento",   f.data_nascimento.strftime("%d/%m/%Y")),
            ("📅 Idade",        f"{f.calcular_idade()} anos"),
            ("💰 Sal. Base",    f"€{f.salario_base:.2f}"),
            ("💵 Sal. Líquido", f"€{f.calcular_salario_liquido():.2f}"),
        ]
        if isinstance(f, Armazem):
            details.append(("🔑 Cartão",  "Ativo" if f.cartao_ativo else "Inativo"))
            details.append(("🚪 Entrada", "Dentro" if f.estado_entrada else "Fora"))
        elif isinstance(f, Limpeza):
            details.append(("⏱ Horas Extra", str(f.horas_extra)))
        elif isinstance(f, Caixa):
            details.append(("⚠ Subsídio Risco", f"€{f.subsidio_risco:.2f}"))

        for lbl, val in details:
            row = tk.Frame(self.func_detail, bg=CARD)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, bg=CARD, fg=MUTED,
                     font=("Courier New", 9), width=16, anchor="w").pack(side="left")
            tk.Label(row, text=val, bg=CARD, fg=TEXT,
                     font=("Courier New", 9, "bold")).pack(side="left")

        tk.Frame(self.func_detail, bg=BORDER, height=1).pack(fill="x", pady=10)
        if isinstance(f, Armazem):
            make_button(self.func_detail, "📥 Entrada", lambda fi=f: self._armazem_action(fi, "entrada"),
                        color=SUCCESS, width=14).pack(pady=2)
            make_button(self.func_detail, "📤 Saída",   lambda fi=f: self._armazem_action(fi, "saida"),
                        color=WARN, width=14).pack(pady=2)
            make_button(self.func_detail, "🔑 Alterar Acesso", lambda fi=f: self._armazem_action(fi, "acesso"),
                        color=ACCENT2, width=14).pack(pady=2)
        make_button(self.func_detail, "🗑  Remover", lambda: self._remove_func(idx),
                    color=DANGER, width=14).pack(pady=(8, 0))

    def _armazem_action(self, f, action):
        if action == "entrada":
            msg = f.entrada()
        elif action == "saida":
            msg = f.saida()
        else:
            msg = f.alterar_acesso()
        messagebox.showinfo("Armazém", msg)
        self._refresh_func_tree()

    def _remove_func(self, idx):
        if messagebox.askyesno("Confirmar", "Remover este funcionário?"):
            self.loja.lista_funcionarios.pop(idx)
            self._refresh_func_tree()
            for w in self.func_detail.winfo_children():
                w.destroy()
            tk.Label(self.func_detail, text="Selecione um\nfuncionário",
                     bg=CARD, fg=MUTED, font=("Courier New", 11),
                     justify="center").pack(expand=True)

    def _open_add_func(self):
        win = tk.Toplevel(self)
        win.title("Novo Funcionário")
        win.geometry("440x560")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="Novo Funcionário", bg=BG, fg=TEXT,
                 font=("Courier New", 15, "bold")).pack(pady=(20, 4))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=6)

        form = tk.Frame(win, bg=BG)
        form.pack(fill="both", expand=True, padx=24, pady=8)

        def lbl(text): tk.Label(form, text=text, bg=BG, fg=MUTED, font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
        def ent(ph=""): e = make_entry(form, ph, width=36); e.pack(fill="x", ipady=5); return e

        lbl("Tipo de Funcionário")
        tipo_var = tk.StringVar(value="Caixa")
        tipos = tk.Frame(form, bg=BG)
        tipos.pack(anchor="w")
        for t in ["Caixa", "Armazém", "Limpeza"]:
            tk.Radiobutton(tipos, text=t, variable=tipo_var, value=t,
                           bg=BG, fg=TEXT, selectcolor=CARD2,
                           activebackground=BG, activeforeground=ACCENT,
                           font=("Courier New", 10)).pack(side="left", padx=4)

        lbl("Nome"); e_nome = ent("Nome completo")
        lbl("Morada"); e_morada = ent("Rua, número, cidade")
        lbl("Telefone"); e_tel = ent("9XXXXXXXX")
        lbl("Data Nascimento (AAAA-MM-DD)"); e_nasc = ent("1990-01-01")
        lbl("Salário Base (€)"); e_sal = ent("900.00")

        extra_frame = tk.Frame(form, bg=BG)
        extra_frame.pack(fill="x")
        e_extra = None

        def update_extra(*_):
            nonlocal e_extra
            for w in extra_frame.winfo_children(): w.destroy()
            t = tipo_var.get()
            if t == "Caixa":
                tk.Label(extra_frame, text="Subsídio de Risco (€)", bg=BG, fg=MUTED,
                         font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
                e_extra = make_entry(extra_frame, "75.00", width=36)
                e_extra.pack(fill="x", ipady=5)
            elif t == "Limpeza":
                tk.Label(extra_frame, text="Horas Extra", bg=BG, fg=MUTED,
                         font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
                e_extra = make_entry(extra_frame, "0", width=36)
                e_extra.pack(fill="x", ipady=5)

        tipo_var.trace_add("write", update_extra)
        update_extra()

        def submit():
            nonlocal e_extra
            try:
                nome = e_nome.get().strip()
                morada = e_morada.get().strip()
                tel = e_tel.get().strip()
                nasc = datetime.strptime(e_nasc.get().strip(), "%Y-%m-%d").date()
                sal = float(e_sal.get().strip())
                if not nome or nome == "Nome completo":
                    raise ValueError("Nome obrigatório")
                t = tipo_var.get()
                if t == "Caixa":
                    sub = float(e_extra.get().strip()) if e_extra else 0.0
                    f = Caixa(nome, morada, tel, nasc, sal, subsidio_risco=sub)
                elif t == "Armazém":
                    f = Armazem(nome, morada, tel, nasc, sal)
                else:
                    he = int(e_extra.get().strip()) if e_extra else 0
                    f = Limpeza(nome, morada, tel, nasc, sal, horas_extra=he)
                self.loja.adicionar_funcionario(f)
                self._refresh_func_tree()
                messagebox.showinfo("Sucesso", f"{nome} adicionado(a)!", parent=win)
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Erro", str(ex), parent=win)

        make_button(win, "✔  Adicionar", submit, color=SUCCESS, width=20).pack(pady=14)

    # ─── PRODUTOS ─────────────────────────────────
    def _build_produtos(self):
        p = self.pages["Produtos"]
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 4))
        tk.Label(hdr, text="Produtos", bg=BG, fg=TEXT,
                 font=("Courier New", 20, "bold")).pack(side="left")
        make_button(hdr, "+ Novo Produto", self._open_add_prod, color=SUCCESS).pack(side="right", pady=4)

        card = card_frame(p, padx=14, pady=14)
        card.pack(fill="both", expand=True, padx=32, pady=8)

        cols = ("Nome", "Categoria", "Preço", "Stock Atual", "Mín", "Máx", "Estado")
        self.prod_tree = ttk.Treeview(card, columns=cols, show="headings", height=20)
        for col in cols:
            self.prod_tree.heading(col, text=col)
            self.prod_tree.column(col, width=100, anchor="center")
        vsb = ttk.Scrollbar(card, orient="vertical", command=self.prod_tree.yview)
        self.prod_tree.configure(yscrollcommand=vsb.set)
        self.prod_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        btn_row = tk.Frame(p, bg=BG)
        btn_row.pack(pady=6)
        make_button(btn_row, "✏ Editar Stock", self._edit_stock, color=WARN, width=14).pack(side="left", padx=6)
        make_button(btn_row, "🗑 Remover",      self._remove_prod, color=DANGER, width=14).pack(side="left", padx=6)

        self._refresh_prod_tree()

    def _refresh_prod_tree(self):
        self.prod_tree.delete(*self.prod_tree.get_children())
        for pr in self.loja.lista_produtos:
            estado = "✓ OK" if pr.stock_atual > pr.stock_min else "⚠ Baixo"
            self.prod_tree.insert("", "end", values=(
                pr.nome, pr.categoria, f"€{pr.preco:.2f}",
                pr.stock_atual, pr.stock_min, pr.stock_max, estado
            ))

    def _open_add_prod(self):
        win = tk.Toplevel(self)
        win.title("Novo Produto")
        win.geometry("400x460")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="Novo Produto", bg=BG, fg=TEXT,
                 font=("Courier New", 15, "bold")).pack(pady=(20, 4))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=6)

        form = tk.Frame(win, bg=BG)
        form.pack(fill="both", expand=True, padx=24)

        def lbl(text): tk.Label(form, text=text, bg=BG, fg=MUTED, font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
        def ent(ph=""): e = make_entry(form, ph, width=36); e.pack(fill="x", ipady=5); return e

        lbl("Nome"); e_nome = ent("Nome do produto")
        lbl("Categoria"); e_cat = ent("Alimentação / Limpeza / ...")
        lbl("Preço (€)"); e_preco = ent("0.00")
        lbl("Stock Actual"); e_stock = ent("0")
        lbl("Stock Mínimo"); e_min = ent("5")
        lbl("Stock Máximo"); e_max = ent("100")

        def submit():
            try:
                pr = Produto(
                    nome=e_nome.get().strip(),
                    preco=float(e_preco.get()),
                    categoria=e_cat.get().strip(),
                    stock_min=int(e_min.get()),
                    stock_max=int(e_max.get()),
                    stock_atual=int(e_stock.get())
                )
                self.loja.adicionar_produto(pr)
                self._refresh_prod_tree()
                messagebox.showinfo("Sucesso", "Produto adicionado!", parent=win)
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Erro", str(ex), parent=win)

        make_button(win, "✔  Adicionar", submit, color=SUCCESS, width=20).pack(pady=14)

    def _edit_stock(self):
        sel = self.prod_tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um produto.")
            return
        idx = self.prod_tree.index(sel[0])
        pr = self.loja.lista_produtos[idx]

        win = tk.Toplevel(self)
        win.title("Editar Stock")
        win.geometry("340x260")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text=f"Stock: {pr.nome}", bg=BG, fg=ACCENT,
                 font=("Courier New", 13, "bold")).pack(pady=(20, 10))

        form = tk.Frame(win, bg=BG)
        form.pack(padx=30, fill="x")

        def row(lbl_text, default):
            tk.Label(form, text=lbl_text, bg=BG, fg=MUTED, font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
            e = make_entry(form, str(default), width=30)
            e.delete(0, tk.END); e.insert(0, str(default)); e.config(fg=TEXT)
            e.pack(fill="x", ipady=4)
            return e

        e_atual = row("Stock Actual", pr.stock_atual)
        e_min   = row("Stock Mínimo", pr.stock_min)
        e_max   = row("Stock Máximo", pr.stock_max)

        def save():
            try:
                pr.stock_atual = int(e_atual.get())
                pr.alterar_stock_min(int(e_min.get()))
                pr.alterar_stock_max(int(e_max.get()))
                self._refresh_prod_tree()
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Erro", str(ex), parent=win)

        make_button(win, "💾  Guardar", save, color=ACCENT, width=18).pack(pady=14)

    def _remove_prod(self):
        sel = self.prod_tree.selection()
        if not sel: return
        idx = self.prod_tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "Remover produto?"):
            self.loja.lista_produtos.pop(idx)
            self._refresh_prod_tree()

    # ─── CLIENTES ─────────────────────────────────
    def _build_clientes(self):
        p = self.pages["Clientes"]
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 4))
        tk.Label(hdr, text="Clientes", bg=BG, fg=TEXT,
                 font=("Courier New", 20, "bold")).pack(side="left")
        make_button(hdr, "+ Novo Cliente", self._open_add_client, color=WARN).pack(side="right", pady=4)

        card = card_frame(p, padx=14, pady=14)
        card.pack(fill="both", expand=True, padx=32, pady=8)

        cols = ("ID Cartão", "Nome", "Morada", "Telefone")
        self.cli_tree = ttk.Treeview(card, columns=cols, show="headings", height=20)
        for col in cols:
            self.cli_tree.heading(col, text=col)
            self.cli_tree.column(col, width=150, anchor="center")
        self.cli_tree.pack(fill="both", expand=True)

        make_button(p, "🗑 Remover Cliente", self._remove_client,
                    color=DANGER, width=18).pack(pady=6)

        self._refresh_cli_tree()

    def _refresh_cli_tree(self):
        self.cli_tree.delete(*self.cli_tree.get_children())
        for c in self.loja.clientes_registrados:
            self.cli_tree.insert("", "end", values=(c.id_cartao, c.nome, c.morada, c.telefone))

    def _open_add_client(self):
        win = tk.Toplevel(self)
        win.title("Novo Cliente")
        win.geometry("380x360")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="Novo Cliente", bg=BG, fg=TEXT,
                 font=("Courier New", 15, "bold")).pack(pady=(20, 6))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=4)

        form = tk.Frame(win, bg=BG)
        form.pack(fill="both", expand=True, padx=24)

        def lbl(t): tk.Label(form, text=t, bg=BG, fg=MUTED, font=("Courier New", 9)).pack(anchor="w", pady=(6,1))
        def ent(ph=""): e = make_entry(form, ph, width=36); e.pack(fill="x", ipady=5); return e

        new_id = max((c.id_cartao for c in self.loja.clientes_registrados), default=1000) + 1
        lbl("ID Cartão (auto)"); e_id = ent(str(new_id)); e_id.config(state="disabled")
        lbl("Nome"); e_nome = ent("Nome completo")
        lbl("Morada"); e_mor = ent("Rua, número, cidade")
        lbl("Telefone"); e_tel = ent("9XXXXXXXX")

        def submit():
            try:
                c = Cliente(new_id, e_nome.get().strip(), e_mor.get().strip(), e_tel.get().strip())
                self.loja.registrar_cliente(c)
                self._refresh_cli_tree()
                messagebox.showinfo("Sucesso", "Cliente registado!", parent=win)
                win.destroy()
            except Exception as ex:
                messagebox.showerror("Erro", str(ex), parent=win)

        make_button(win, "✔  Registar", submit, color=WARN, width=20).pack(pady=14)

    def _remove_client(self):
        sel = self.cli_tree.selection()
        if not sel: return
        idx = self.cli_tree.index(sel[0])
        if messagebox.askyesno("Confirmar", "Remover cliente?"):
            self.loja.clientes_registrados.pop(idx)
            self._refresh_cli_tree()

    # ─── VENDAS ───────────────────────────────────
    def _build_vendas(self):
        p = self.pages["Vendas"]
        hdr = tk.Frame(p, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 4))
        tk.Label(hdr, text="Vendas", bg=BG, fg=TEXT,
                 font=("Courier New", 20, "bold")).pack(side="left")
        make_button(hdr, "+ Nova Venda", self._open_add_venda, color=ACCENT2).pack(side="right", pady=4)

        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=32, pady=8)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = card_frame(body, padx=12, pady=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        cols = ("Fatura", "Cliente", "Vendedor", "Produtos", "Total")
        self.venda_tree = ttk.Treeview(left, columns=cols, show="headings", height=18)
        for col in cols:
            self.venda_tree.heading(col, text=col)
            self.venda_tree.column(col, width=100, anchor="center")
        self.venda_tree.pack(fill="both", expand=True)
        self.venda_tree.bind("<<TreeviewSelect>>", self._on_venda_select)

        self.fatura_frame = card_frame(body, padx=16, pady=16)
        self.fatura_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        tk.Label(self.fatura_frame, text="Selecione uma\nvenda", bg=CARD,
                 fg=MUTED, font=("Courier New", 11), justify="center").pack(expand=True)

        self._refresh_venda_tree()

    def _refresh_venda_tree(self):
        self.venda_tree.delete(*self.venda_tree.get_children())
        for v in self.loja.lista_vendas:
            self.venda_tree.insert("", "end", values=(
                f"#{v.id_fatura}", v.cliente.nome, v.vendedor.nome,
                len(v.produtos), f"€{v.total():.2f}"
            ))

    def _on_venda_select(self, event):
        sel = self.venda_tree.selection()
        if not sel: return
        idx = self.venda_tree.index(sel[0])
        v = self.loja.lista_vendas[idx]
        for w in self.fatura_frame.winfo_children():
            w.destroy()

        tk.Label(self.fatura_frame, text="FATURA", bg=CARD, fg=ACCENT,
                 font=("Courier New", 13, "bold")).pack(anchor="w")
        tk.Frame(self.fatura_frame, bg=BORDER, height=1).pack(fill="x", pady=4)

        txt = tk.Text(self.fatura_frame, bg=CARD2, fg=SUCCESS,
                      font=("Courier New", 9), relief="flat",
                      highlightthickness=0, bd=0, wrap="none")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", v.fazer_fatura())
        txt.config(state="disabled")

    def _open_add_venda(self):
        caixas = [f for f in self.loja.lista_funcionarios if isinstance(f, Caixa)]
        if not caixas:
            messagebox.showerror("Erro", "Não há caixas registados.")
            return
        if not self.loja.clientes_registrados:
            messagebox.showerror("Erro", "Não há clientes registados.")
            return
        if not self.loja.lista_produtos:
            messagebox.showerror("Erro", "Não há produtos registados.")
            return

        win = tk.Toplevel(self)
        win.title("Nova Venda")
        win.geometry("500x580")
        win.configure(bg=BG)
        win.grab_set()

        tk.Label(win, text="Nova Venda", bg=BG, fg=TEXT,
                 font=("Courier New", 15, "bold")).pack(pady=(20, 4))
        tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=24, pady=4)

        form = tk.Frame(win, bg=BG)
        form.pack(fill="both", expand=True, padx=24)

        def lbl(t): tk.Label(form, text=t, bg=BG, fg=MUTED, font=("Courier New", 9)).pack(anchor="w", pady=(8,1))

        lbl("Vendedor (Caixa)")
        caixa_var = tk.StringVar()
        caixa_cb = ttk.Combobox(form, textvariable=caixa_var, state="readonly",
                                 values=[str(c) for c in caixas], font=("Courier New", 10))
        caixa_cb.pack(fill="x", ipady=4)
        if caixas: caixa_cb.current(0)

        lbl("Cliente")
        cli_var = tk.StringVar()
        cli_cb = ttk.Combobox(form, textvariable=cli_var, state="readonly",
                               values=[str(c) for c in self.loja.clientes_registrados],
                               font=("Courier New", 10))
        cli_cb.pack(fill="x", ipady=4)
        if self.loja.clientes_registrados: cli_cb.current(0)

        lbl("Produtos (Ctrl+click para selecionar múltiplos)")
        prod_lb = tk.Listbox(form, selectmode="multiple", bg=CARD2, fg=TEXT,
                             font=("Courier New", 10), relief="flat",
                             highlightthickness=1, highlightbackground=BORDER,
                             selectbackground=ACCENT2, height=8)
        for pr in self.loja.lista_produtos:
            prod_lb.insert(tk.END, f"{pr.nome}  –  €{pr.preco:.2f}")
        prod_lb.pack(fill="x", pady=2)

        total_lbl = tk.Label(form, text="Total: €0.00", bg=BG, fg=SUCCESS,
                             font=("Courier New", 12, "bold"))
        total_lbl.pack(anchor="e", pady=4)

        def update_total(event=None):
            sel = prod_lb.curselection()
            total = sum(self.loja.lista_produtos[i].preco for i in sel)
            total_lbl.config(text=f"Total: €{total:.2f}")

        prod_lb.bind("<<ListboxSelect>>", update_total)

        def submit():
            sel = prod_lb.curselection()
            if not sel:
                messagebox.showwarning("Aviso", "Selecione pelo menos um produto.", parent=win)
                return
            caixa = caixas[caixa_cb.current()]
            cliente = self.loja.clientes_registrados[cli_cb.current()]
            produtos = [self.loja.lista_produtos[i] for i in sel]
            new_id = max((v.id_fatura for v in self.loja.lista_vendas), default=1000) + 1
            venda = Venda(new_id, produtos, caixa, cliente)
            self.loja.registrar_venda(venda)
            self._refresh_venda_tree()
            messagebox.showinfo("Sucesso", f"Venda #{new_id} registada!", parent=win)
            win.destroy()

        make_button(win, "✔  Registar Venda", submit, color=ACCENT2, width=22).pack(pady=14)


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────

if __name__ == "__main__":
    app = LojaApp()
    app.mainloop()
