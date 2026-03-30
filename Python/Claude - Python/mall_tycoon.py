import tkinter as tk
from tkinter import ttk, messagebox
import random
import math


class MallTycoon:
    def __init__(self, root):
        self.root = root
        self.root.title("Mall Tycoon 🏬 - Retail Edition")
        self.root.geometry("1100x750")
        self.root.configure(bg="#1a1a2e")

        # Game state
        self.money = 3000
        self.reputation = 50
        self.visitors = 0
        self.total_income = 0
        self.day = 1
        self.employee_count = 0
        self.employee_salary = 50
        self.customer_satisfaction = 100
        self.complaints = 0
        self.rent = 200
        self.expansion_level = 1

        # Competitors
        self.competitors = [
            {"name": "Mega Mall", "strength": random.randint(60, 80)},
            {"name": "Shopping Paradise", "strength": random.randint(50, 70)},
            {"name": "Premium Plaza", "strength": random.randint(40, 60)}
        ]

        # Store types with expanded properties
        self.store_types = {
            "Clothing": {"cost": 800, "income": 45, "rep": 2, "visitors": 25, "employees": 1, "quality": 60},
            "Food Court": {"cost": 1200, "income": 70, "rep": 3, "visitors": 50, "employees": 2, "quality": 55},
            "Electronics": {"cost": 2000, "income": 110, "rep": 4, "visitors": 35, "employees": 2, "quality": 70},
            "Toy Store": {"cost": 600, "income": 35, "rep": 3, "visitors": 40, "employees": 1, "quality": 50},
            "Jewelry": {"cost": 3000, "income": 140, "rep": 5, "visitors": 18, "employees": 2, "quality": 80},
            "Bookstore": {"cost": 900, "income": 50, "rep": 4, "visitors": 30, "employees": 1, "quality": 65},
            "Arcade": {"cost": 1500, "income": 80, "rep": 3, "visitors": 60, "employees": 1, "quality": 55},
            "Cinema": {"cost": 3500, "income": 180, "rep": 6, "visitors": 120, "employees": 3, "quality": 75},
            "Coffee Shop": {"cost": 700, "income": 40, "rep": 2, "visitors": 45, "employees": 2, "quality": 60},
            "Gym": {"cost": 2500, "income": 130, "rep": 5, "visitors": 40, "employees": 2, "quality": 70},
            "Pet Store": {"cost": 1100, "income": 60, "rep": 3, "visitors": 35, "employees": 2, "quality": 65},
            "Salon": {"cost": 1300, "income": 75, "rep": 3, "visitors": 25, "employees": 2, "quality": 60}
        }

        self.owned_stores = []
        self.customer_events = []
        self.news_feed = []

        self.create_ui()
        self.update_stats()
        self.add_news("🎮 Welcome to Mall Tycoon! Build your retail empire!")

    def create_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#16213e", height=70)
        header.pack(fill=tk.X)

        tk.Label(header, text="🏬 MALL TYCOON", font=("Arial", 22, "bold"),
                 bg="#16213e", fg="#00d9ff").pack(side=tk.LEFT, padx=20, pady=15)

        tk.Label(header, text="RETAIL EDITION", font=("Arial", 10),
                 bg="#16213e", fg="#ff6b6b").pack(side=tk.LEFT, pady=15)

        # Stats panel
        stats_frame = tk.Frame(self.root, bg="#0f3460", relief=tk.RIDGE, bd=2)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # Row 1
        row1 = tk.Frame(stats_frame, bg="#0f3460")
        row1.pack(fill=tk.X, pady=5)

        self.money_label = tk.Label(row1, text="", font=("Arial", 11, "bold"),
                                    bg="#0f3460", fg="#00ff88")
        self.money_label.pack(side=tk.LEFT, padx=15)

        self.day_label = tk.Label(row1, text="", font=("Arial", 11),
                                  bg="#0f3460", fg="#ffdd59")
        self.day_label.pack(side=tk.LEFT, padx=15)

        self.rep_label = tk.Label(row1, text="", font=("Arial", 11),
                                  bg="#0f3460", fg="#ff6b6b")
        self.rep_label.pack(side=tk.LEFT, padx=15)

        self.visitors_label = tk.Label(row1, text="", font=("Arial", 11),
                                       bg="#0f3460", fg="#00d9ff")
        self.visitors_label.pack(side=tk.LEFT, padx=15)

        # Row 2
        row2 = tk.Frame(stats_frame, bg="#0f3460")
        row2.pack(fill=tk.X, pady=5)

        self.satisfaction_label = tk.Label(row2, text="", font=("Arial", 11),
                                           bg="#0f3460", fg="#95e1d3")
        self.satisfaction_label.pack(side=tk.LEFT, padx=15)

        self.employee_label = tk.Label(row2, text="", font=("Arial", 11),
                                       bg="#0f3460", fg="#f3a683")
        self.employee_label.pack(side=tk.LEFT, padx=15)

        self.expansion_label = tk.Label(row2, text="", font=("Arial", 11),
                                        bg="#0f3460", fg="#a29bfe")
        self.expansion_label.pack(side=tk.LEFT, padx=15)

        # Main content
        content = tk.Frame(self.root, bg="#1a1a2e")
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel - Store shop
        left_panel = tk.Frame(content, bg="#16213e", relief=tk.RIDGE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        tk.Label(left_panel, text="🛍️ Store Catalog", font=("Arial", 14, "bold"),
                 bg="#16213e", fg="#00d9ff").pack(pady=8)

        canvas = tk.Canvas(left_panel, bg="#16213e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#16213e")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for store_name, props in self.store_types.items():
            self.create_store_card(scrollable_frame, store_name, props)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Middle panel - Events & News
        middle_panel = tk.Frame(content, bg="#16213e",
                                relief=tk.RIDGE, bd=2, width=250)
        middle_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        middle_panel.pack_propagate(False)

        tk.Label(middle_panel, text="📰 News Feed", font=("Arial", 12, "bold"),
                 bg="#16213e", fg="#ffdd59").pack(pady=8)

        self.news_listbox = tk.Listbox(middle_panel, font=("Arial", 9),
                                       bg="#0f3460", fg="#ffffff", relief=tk.FLAT,
                                       highlightthickness=0)
        self.news_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right panel - Management
        right_panel = tk.Frame(content, bg="#16213e", relief=tk.RIDGE, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(right_panel, text="🏪 My Stores", font=("Arial", 14, "bold"),
                 bg="#16213e", fg="#00d9ff").pack(pady=8)

        self.stores_listbox = tk.Listbox(right_panel, font=("Arial", 10),
                                         bg="#0f3460", fg="#ffffff", relief=tk.FLAT,
                                         highlightthickness=0)
        self.stores_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Management buttons
        mgmt_frame = tk.Frame(right_panel, bg="#16213e")
        mgmt_frame.pack(pady=5)

        tk.Button(mgmt_frame, text="👥 Hire Staff", command=self.hire_employee,
                  font=("Arial", 9, "bold"), bg="#f3a683", fg="#16213e",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2").grid(row=0, column=0, padx=3, pady=3)

        tk.Button(mgmt_frame, text="🔧 Upgrade", command=self.upgrade_store,
                  font=("Arial", 9, "bold"), bg="#95e1d3", fg="#16213e",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2").grid(row=0, column=1, padx=3, pady=3)

        tk.Button(mgmt_frame, text="📢 Marketing", command=self.run_marketing,
                  font=("Arial", 9, "bold"), bg="#a29bfe", fg="#16213e",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2").grid(row=1, column=0, padx=3, pady=3)

        tk.Button(mgmt_frame, text="🏗️ Expand", command=self.expand_mall,
                  font=("Arial", 9, "bold"), bg="#ff6b6b", fg="white",
                  relief=tk.FLAT, padx=12, pady=6, cursor="hand2").grid(row=1, column=1, padx=3, pady=3)

        # Action buttons
        action_frame = tk.Frame(right_panel, bg="#16213e")
        action_frame.pack(pady=10)

        tk.Button(action_frame, text="⏭️ NEXT DAY", command=self.next_day,
                  font=("Arial", 11, "bold"), bg="#00ff88", fg="#16213e",
                  relief=tk.FLAT, padx=25, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

        tk.Button(action_frame, text="📊 Stats", command=self.show_stats,
                  font=("Arial", 11, "bold"), bg="#00d9ff", fg="#16213e",
                  relief=tk.FLAT, padx=25, pady=10, cursor="hand2").pack(side=tk.LEFT, padx=5)

    def create_store_card(self, parent, name, props):
        card = tk.Frame(parent, bg="#0f3460", relief=tk.RIDGE, bd=1)
        card.pack(fill=tk.X, padx=5, pady=4)

        tk.Label(card, text=name, font=("Arial", 11, "bold"),
                 bg="#0f3460", fg="#00d9ff").pack(anchor="w", padx=8, pady=(4, 0))

        info = f"💰 ${props['cost']} | 📈 ${props['income']}/day | ⭐ +{props['rep']}"
        tk.Label(card, text=info, font=("Arial", 8),
                 bg="#0f3460", fg="#95e1d3").pack(anchor="w", padx=8)

        info2 = f"👥 {props['visitors']} visitors | 🔧 Quality: {props['quality']}%"
        tk.Label(card, text=info2, font=("Arial", 8),
                 bg="#0f3460", fg="#f3a683").pack(anchor="w", padx=8)

        tk.Button(card, text="BUY", command=lambda: self.buy_store(name, props),
                  font=("Arial", 9, "bold"), bg="#00ff88", fg="#16213e",
                  relief=tk.FLAT, padx=12, pady=3, cursor="hand2").pack(anchor="e", padx=8, pady=4)

    def buy_store(self, name, props):
        max_stores = 5 + (self.expansion_level * 3)
        if len(self.owned_stores) >= max_stores:
            messagebox.showwarning(
                "Max Stores", f"Expand your mall to own more than {max_stores} stores!")
            return

        if self.money >= props["cost"]:
            self.money -= props["cost"]
            store_data = {
                "name": name,
                "props": props.copy(),
                "level": 1,
                "quality": props["quality"],
                "staff": props["employees"]
            }
            self.owned_stores.append(store_data)
            self.employee_count += props["employees"]
            self.reputation += props["rep"]
            self.update_stats()
            self.update_stores_list()
            self.add_news(f"✅ Purchased {name} for ${props['cost']}")
            messagebox.showinfo(
                "Success!", f"You bought a {name}! 🎉\nEmployees hired: {props['employees']}")
        else:
            messagebox.showerror("Insufficient Funds",
                                 f"You need ${props['cost']} to buy {name}.\nYou have ${self.money}.")

    def hire_employee(self):
        if len(self.owned_stores) == 0:
            messagebox.showwarning("No Stores", "Buy a store first!")
            return

        cost = 500
        if self.money >= cost:
            self.money -= cost
            self.employee_count += 1
            self.customer_satisfaction = min(
                100, self.customer_satisfaction + 5)
            self.update_stats()
            self.add_news(f"👥 Hired new employee! (+5% satisfaction)")
            messagebox.showinfo(
                "Hired!", "New employee hired!\nSalary: $50/day\n+5% Customer Satisfaction")
        else:
            messagebox.showerror("Not Enough Money",
                                 f"Need ${cost} to hire an employee.")

    def upgrade_store(self):
        if len(self.owned_stores) == 0:
            messagebox.showwarning("No Stores", "You don't own any stores!")
            return

        store = random.choice(self.owned_stores)
        cost = 800 * store["level"]

        if self.money >= cost:
            self.money -= cost
            store["level"] += 1
            store["props"]["income"] = int(store["props"]["income"] * 1.3)
            store["quality"] = min(100, store["quality"] + 10)
            self.reputation += 3
            self.update_stats()
            self.update_stores_list()
            self.add_news(
                f"🔧 Upgraded {store['name']} to level {store['level']}!")
            messagebox.showinfo(
                "Upgraded!", f"{store['name']} upgraded to level {store['level']}!\n+30% income\n+10% quality")
        else:
            messagebox.showerror("Not Enough Money",
                                 f"Need ${cost} to upgrade.")

    def run_marketing(self):
        cost = 600
        if self.money >= cost:
            self.money -= cost
            boost = random.randint(50, 150)
            self.visitors += boost
            self.reputation += 5
            self.add_news(f"📢 Marketing campaign attracted {boost} visitors!")
            self.update_stats()
            messagebox.showinfo(
                "Marketing Success!", f"Campaign attracted {boost} new visitors!\n+5 Reputation")
        else:
            messagebox.showerror("Not Enough Money",
                                 f"Need ${cost} for marketing.")

    def expand_mall(self):
        cost = 3000 * self.expansion_level
        if self.money >= cost:
            self.money -= cost
            self.expansion_level += 1
            self.add_news(f"🏗️ Mall expanded to level {self.expansion_level}!")
            messagebox.showinfo("Expansion Complete!",
                                f"Mall expanded to level {self.expansion_level}!\nCan now own {5 + (self.expansion_level * 3)} stores!")
            self.update_stats()
        else:
            messagebox.showerror("Not Enough Money",
                                 f"Need ${cost} to expand.")

    def next_day(self):
        if len(self.owned_stores) == 0:
            messagebox.showwarning(
                "No Stores", "Buy at least one store to progress!")
            return

        self.day += 1
        daily_income = 0
        daily_visitors = 0
        daily_events = []

        # Calculate income from stores
        for store in self.owned_stores:
            base_income = store["props"]["income"]
            base_visitors = store["props"]["visitors"]

            # Quality and reputation multipliers
            quality_mult = store["quality"] / 100
            rep_mult = 1 + (self.reputation / 300)
            satisfaction_mult = self.customer_satisfaction / 100

            # Random variance
            variance = random.uniform(0.7, 1.3)

            income = int(base_income * quality_mult *
                         rep_mult * satisfaction_mult * variance)
            visitors = int(base_visitors * rep_mult *
                           satisfaction_mult * variance)

            daily_income += income
            daily_visitors += visitors

            # Store quality decay
            store["quality"] = max(30, store["quality"] - random.randint(1, 3))

        # Employee salaries
        daily_expenses = self.employee_count * self.employee_salary + self.rent
        daily_income -= daily_expenses

        self.money += daily_income
        self.total_income += max(0, daily_income)
        self.visitors += daily_visitors

        # Customer events (complaints, reviews, etc.)
        self.handle_customer_events(daily_events)

        # Competitor actions
        self.handle_competitors(daily_events)

        # Random events
        if random.random() < 0.25:
            self.random_event(daily_events)

        # Customer satisfaction decay
        self.customer_satisfaction = max(
            0, self.customer_satisfaction - random.randint(2, 5))

        self.update_stats()

        events_text = "\n".join(
            daily_events) if daily_events else "No special events today."

        messagebox.showinfo("Day Complete!",
                            f"📅 Day {self.day} Results:\n\n"
                            f"💰 Net Income: ${daily_income}\n"
                            f"💸 Expenses: ${daily_expenses}\n"
                            f"👥 Visitors: {daily_visitors}\n"
                            f"😊 Satisfaction: {self.customer_satisfaction}%\n\n"
                            f"{events_text}")

    def handle_customer_events(self, events):
        # Rude customers and complaints
        if random.random() < 0.3:
            complaint_types = [
                ("😡 Angry customer complained about slow service!", -5, -2),
                ("💢 Customer left bad review online!", -8, -3),
                ("🤬 Customer demanded refund!", -100, -5),
                ("😤 Customer complained about prices!", -3, -1),
                ("👎 Customer unsatisfied with product quality!", -6, -2),
                ("🗣️ Customer caused scene in store!", -10, -4),
            ]

            complaint, money_loss, satisfaction_loss = random.choice(
                complaint_types)
            self.money += money_loss
            self.customer_satisfaction = max(
                0, self.customer_satisfaction + satisfaction_loss)
            self.complaints += 1
            events.append(complaint)
            self.add_news(complaint)

        # Happy customers
        if random.random() < 0.2 and self.customer_satisfaction > 70:
            happy_events = [
                ("⭐ Customer left 5-star review!", 3),
                ("💝 Loyal customer recommended your mall!", 5),
                ("😊 Customer praised your staff!", 4),
                ("🎉 Customer loved the shopping experience!", 3),
            ]

            event, rep_gain = random.choice(happy_events)
            self.reputation += rep_gain
            events.append(event)
            self.add_news(event)

    def handle_competitors(self, events):
        for comp in self.competitors:
            # Competitors can steal customers
            if random.random() < 0.15:
                if comp["strength"] > self.reputation:
                    visitor_loss = random.randint(20, 50)
                    self.visitors = max(0, self.visitors - visitor_loss)
                    comp["strength"] += random.randint(1, 3)
                    event = f"🏢 {comp['name']} stole {visitor_loss} visitors!"
                    events.append(event)
                    self.add_news(event)

            # Competitors grow
            if random.random() < 0.1:
                comp["strength"] += random.randint(2, 5)
                if comp["strength"] > self.reputation + 20:
                    event = f"⚠️ {comp['name']} is dominating the market!"
                    self.add_news(event)

    def random_event(self, events):
        event_list = [
            {"msg": "🎉 Holiday shopping surge! +300 visitors!",
                "visitors": 300, "money": 500},
            {"msg": "⭐ Influencer posted about your mall! +50 rep!", "rep": 15},
            {"msg": "💸 Government grant received! +$1000", "money": 1000},
            {"msg": "📰 Featured in magazine! +30 rep!", "rep": 30},
            {"msg": "🎪 Street festival nearby! +200 visitors!", "visitors": 200},
            {"msg": "💔 Competitor opened nearby. -10 rep", "rep": -10},
            {"msg": "🚧 Construction issues. -$300", "money": -300},
            {"msg": "🌧️ Bad weather. Fewer visitors.", "visitors": -100},
            {"msg": "🎁 Supplier discount! +$400", "money": 400},
            {"msg": "🏆 Won local business award! +25 rep!", "rep": 25},
        ]

        event = random.choice(event_list)

        if "money" in event:
            self.money += event["money"]
        if "rep" in event:
            self.reputation = max(0, self.reputation + event["rep"])
        if "visitors" in event:
            self.visitors = max(0, self.visitors + event["visitors"])

        events.append(event["msg"])
        self.add_news(event["msg"])

    def show_stats(self):
        comp_info = "\n".join(
            [f"  • {c['name']}: {c['strength']} strength" for c in self.competitors])

        stats_text = f"""
📊 DETAILED STATISTICS

💰 Current Money: ${self.money}
💼 Total Income: ${self.total_income}
⭐ Reputation: {self.reputation}
👥 Total Visitors: {self.visitors}
😊 Satisfaction: {self.customer_satisfaction}%
📅 Day: {self.day}

🏪 Stores Owned: {len(self.owned_stores)}
👔 Employees: {self.employee_count}
💸 Daily Salaries: ${self.employee_count * self.employee_salary}
🏗️ Expansion Level: {self.expansion_level}
😡 Total Complaints: {self.complaints}

🏢 COMPETITORS:
{comp_info}
        """
        messagebox.showinfo("Detailed Statistics", stats_text)

    def add_news(self, message):
        self.news_listbox.insert(0, f"Day {self.day}: {message}")
        if self.news_listbox.size() > 50:
            self.news_listbox.delete(50, tk.END)

    def update_stats(self):
        self.money_label.config(text=f"💰 ${self.money}")
        self.day_label.config(text=f"📅 Day {self.day}")
        self.rep_label.config(text=f"⭐ Rep: {self.reputation}")
        self.visitors_label.config(text=f"👥 Visitors: {self.visitors}")
        self.satisfaction_label.config(
            text=f"😊 Satisfaction: {self.customer_satisfaction}%")
        self.employee_label.config(
            text=f"👔 Staff: {self.employee_count} (${self.employee_count * self.employee_salary}/day)")
        self.expansion_label.config(text=f"🏗️ Level {self.expansion_level}")

        # Update satisfaction color
        if self.customer_satisfaction >= 70:
            self.satisfaction_label.config(fg="#00ff88")
        elif self.customer_satisfaction >= 40:
            self.satisfaction_label.config(fg="#ffdd59")
        else:
            self.satisfaction_label.config(fg="#ff6b6b")

    def update_stores_list(self):
        self.stores_listbox.delete(0, tk.END)
        for i, store in enumerate(self.owned_stores, 1):
            quality_indicator = "🟢" if store["quality"] >= 70 else "🟡" if store["quality"] >= 40 else "🔴"
            self.stores_listbox.insert(tk.END,
                                       f"{i}. {store['name']} L{store['level']} {quality_indicator} (${store['props']['income']}/day)")


if __name__ == "__main__":
    root = tk.Tk()
    game = MallTycoon(root)
    root.mainloop()
