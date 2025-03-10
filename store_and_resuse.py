import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime, timedelta
import matplotlib.patches as patches
import csv
import os
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

class BudgetTracker:
    def __init__(self):
        # user specific directory for CSV file
        home_dir = Path.home()
        data_dir = home_dir / "Documents" / "BudgetTracker"
        data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file = data_dir / "budget_data.csv"            

        # self.data_file = "budget_data.csv"
        self.categories = [
            "Housing", "Transportation", "Food", "Entertainment", "Activities", "Groceries",
            "Utilities", "Healthcare", "Shopping", "Savings", "Charitable", "Other"
        ]
        
        self.root = tk.Tk()
        self.root.title("Budget Master Beta")
        self.root.geometry("1000x850")
        self.root.configure(bg="#1a1a1a")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", 
                            font=("Arial", 12, "bold"),
                            background="#4CAF50",
                            foreground="white",
                            borderwidth=0,
                            padding=10)
        self.style.map("TButton",
                      background=[('active', '#45a049')])
        
        # Modernize Combobox styling
        self.style.configure("TCombobox",
                            fieldbackground="#2d2d2d",
                            background="#4CAF50",
                            foreground="white",
                            arrowcolor="white",
                            borderwidth=0,
                            font=("Arial", 12),
                            padding=5)
        self.style.map("TCombobox",
                    fieldbackground=[('readonly', '#2d2d2d')],
                    background=[('readonly', '#3c3f41'), ('active', '#45a049')],
                    foreground=[('readonly', 'white')])
        
        self.style.configure("Treeview",
                            background="#2d2d2d",
                            foreground="white",
                            fieldbackground="#2d2d2d",
                            font=("Arial", 12),
                            rowheight=25,
                            borderwidth=0,
                            relief="flat",
                            highlightthickness=0)
        self.style.configure("Treeview.Heading",
                            font=("Arial", 12, "bold"),
                            background="#3c3f41",
                            foreground="white",
                            borderwidth=1,
                            relief="solid")
        self.style.map("Treeview",
                      background=[('selected', '#4CAF50')])
        self.style.layout("Treeview", [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])

        self.showing_list = False
        self.current_month = datetime.now().strftime("%Y-%m")
        self.budget_canvas = None
        self.all_income = []  # Store all income across months
        self.all_expenses = []  # Store all expenses across months
        
        self.load_data()
        self.setup_gui()

    def load_data(self):
        self.all_income = []
        self.all_expenses = []
        if os.path.exists(self.data_file):
            with open(self.data_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["type"] == "income":
                        self.all_income.append({
                            "source": row["source"],
                            "amount": float(row["amount"]),
                            "date": row["date"],
                            "month": row["date"][:7]  # Extract YYYY-MM
                        })
                    elif row["type"] == "expense":
                        self.all_expenses.append({
                            "where": row["where"],
                            "amount": float(row["amount"]),
                            "date": row["date"],
                            "category": row["category"],
                            "month": row["date"][:7]  # Extract YYYY-MM
                        })

    def save_data(self):
        with open(self.data_file, mode='w', newline='') as file:
            fieldnames = ["type", "source", "where", "amount", "date", "category"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            for inc in self.all_income:
                writer.writerow({
                    "type": "income",
                    "source": inc["source"],
                    "where": "",
                    "amount": inc["amount"],
                    "date": inc["date"],
                    "category": ""
                })
            for exp in self.all_expenses:
                writer.writerow({
                    "type": "expense",
                    "source": "",
                    "where": exp["where"],
                    "amount": exp["amount"],
                    "date": exp["date"],
                    "category": exp["category"]
                })

    def get_month_data(self, month):
        """Filter income and expenses for the given month."""
        income = [i for i in self.all_income if i["month"] == month]
        expenses = [e for e in self.all_expenses if e["month"] == month]
        return income, expenses

    def setup_gui(self):
        header_frame = tk.Frame(self.root, bg="#252526", pady=10)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, 
                            text="Budget Master Beta",
                            font=("Arial", 24, "bold"),
                            fg="#ffffff",
                            bg="#252526")
        title_label.pack()

        self.month_var = tk.StringVar(value=self.current_month)
        self.month_dropdown = ttk.Combobox(header_frame, textvariable=self.month_var, 
                                        values=self.get_month_options(), state="readonly")
        self.month_dropdown.pack(side="right", padx=10)
        self.month_dropdown.bind("<<ComboboxSelected>>", self.update_month_view)
        
        button_frame = tk.Frame(self.root, bg="#1a1a1a", pady=10)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="Add Income", 
                command=self.open_income_window, style="TButton").pack(side="left", padx=20)
        ttk.Button(button_frame, text="Add Expense", 
                command=self.open_expense_window, style="TButton").pack(side="left", padx=20)
        ttk.Button(button_frame, text="Analyze", 
                command=self.analyze_months, style="TButton").pack(side="left", padx=20)
        
        self.chart_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.chart_frame.grid_columnconfigure((0, 1), weight=1)
        
        # Income Pie Chart
        self.income_fig, self.income_ax = plt.subplots(figsize=(5, 5))
        self.income_fig.patch.set_facecolor('#1a1a1a')
        self.income_ax.set_facecolor('#2d2d2d')
        self.income_canvas = tkagg.FigureCanvasTkAgg(self.income_fig, master=self.chart_frame)
        self.income_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10)
        self.income_fig.canvas.mpl_connect('motion_notify_event', self.on_income_hover)
        self.income_fig.canvas.mpl_connect('button_press_event', self.on_income_click)
        
        # Expense Pie Chart
        self.expense_fig, self.expense_ax = plt.subplots(figsize=(5, 5))
        self.expense_fig.patch.set_facecolor('#1a1a1a')
        self.expense_ax.set_facecolor('#2d2d2d')
        self.expense_canvas = tkagg.FigureCanvasTkAgg(self.expense_fig, master=self.chart_frame)
        self.expense_canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=10)
        self.expense_fig.canvas.mpl_connect('motion_notify_event', self.on_expense_hover)
        self.expense_fig.canvas.mpl_connect('button_press_event', self.on_expense_click)
        
        # View Buttons
        self.view_income_button = ttk.Button(self.chart_frame, text="View Income List", 
                                            command=self.toggle_income_view, style="TButton")
        self.view_income_button.grid(row=1, column=0, pady=5)
        
        self.view_expense_button = ttk.Button(self.chart_frame, text="View Expense List", 
                                            command=self.toggle_expense_view, style="TButton")
        self.view_expense_button.grid(row=1, column=1, pady=5)
        
        # Income Table Frame
        income_table_frame = tk.Frame(self.chart_frame, bg="#1a1a1a")
        income_table_frame.grid(row=0, column=0, sticky="nsew", padx=10)
        income_table_frame.grid_remove()
        
        self.income_tree = ttk.Treeview(income_table_frame, 
                                    columns=("Date", "Source", "Amount"), 
                                    show="headings", height=20)
        self.income_tree.heading("Date", text="Date")
        self.income_tree.heading("Source", text="Source")
        self.income_tree.heading("Amount", text="Amount")
        uniform_width = 100
        self.income_tree.column("Date", width=uniform_width, anchor="center")
        self.income_tree.column("Source", width=uniform_width, anchor="w")
        self.income_tree.column("Amount", width=uniform_width, anchor="e")
        self.income_tree.pack(side="top", fill="both", expand=True)
        
        income_scrollbar = ttk.Scrollbar(income_table_frame, orient="vertical", command=self.income_tree.yview)
        income_scrollbar.pack(side="right", fill="y")
        self.income_tree.configure(yscrollcommand=income_scrollbar.set)
        
        income_button_frame = tk.Frame(income_table_frame, bg="#1a1a1a")
        income_button_frame.pack(side="bottom", pady=5)
        ttk.Button(income_button_frame, text="Edit", command=self.edit_income, style="TButton").pack(side="left", padx=5)
        ttk.Button(income_button_frame, text="Delete", command=self.delete_income, style="TButton").pack(side="left", padx=5)
        
        self.income_table_frame = income_table_frame

        # Expense Table Frame
        expense_table_frame = tk.Frame(self.chart_frame, bg="#1a1a1a")
        expense_table_frame.grid(row=0, column=1, sticky="nsew", padx=10)
        expense_table_frame.grid_remove()
        
        self.expense_tree = ttk.Treeview(expense_table_frame, 
                                        columns=("Date", "Recipient", "Amount", "Category"), 
                                        show="headings", height=20)
        self.expense_tree.heading("Date", text="Date")
        self.expense_tree.heading("Recipient", text="Recipient")
        self.expense_tree.heading("Amount", text="Amount")
        self.expense_tree.heading("Category", text="Category")
        uniform_width = 75
        self.expense_tree.column("Date", width=uniform_width, anchor="center")
        self.expense_tree.column("Recipient", width=uniform_width, anchor="w")
        self.expense_tree.column("Amount", width=uniform_width, anchor="e")
        self.expense_tree.column("Category", width=uniform_width, anchor="w")
        self.expense_tree.pack(side="top", fill="both", expand=True)
        
        expense_scrollbar = ttk.Scrollbar(expense_table_frame, orient="vertical", command=self.expense_tree.yview)
        expense_scrollbar.pack(side="right", fill="y")
        self.expense_tree.configure(yscrollcommand=expense_scrollbar.set)
        
        expense_button_frame = tk.Frame(expense_table_frame, bg="#1a1a1a")
        expense_button_frame.pack(side="bottom", pady=5)
        ttk.Button(expense_button_frame, text="Edit", command=self.edit_expense, style="TButton").pack(side="left", padx=5)
        ttk.Button(expense_button_frame, text="Delete", command=self.delete_expense, style="TButton").pack(side="left", padx=5)
        
        self.expense_table_frame = expense_table_frame

        self.budget_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.budget_frame.pack(fill="x", pady=5)

        self.net_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.net_frame.pack(fill="x", pady=5)
        self.net_label = tk.Label(self.net_frame, text="Net Income: $0.00", 
                                font=("Arial", 16, "bold"), bg="#1a1a1a")
        self.net_label.pack()
        
        self.detail_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.detail_frame.pack(fill="x", padx=20, pady=10)
        self.detail_listbox = tk.Listbox(self.detail_frame, height=10, bg="#2d2d2d", 
                                        fg="white", font=("Arial", 12))
        self.detail_listbox.pack(fill="x")
        
        self.update_charts()

    def get_month_options(self):
        # Include all months from data plus current month
        months = set(i["month"] for i in self.all_income) | set(e["month"] for e in self.all_expenses)
        current_date = datetime.now()
        for i in range(-12, 7):
            month_date = current_date + timedelta(days=30 * i)
            months.add(month_date.strftime("%Y-%m"))
        return sorted(months, reverse=True)

    def update_month_view(self, event):
        self.current_month = self.month_var.get()
        self.update_charts()

    def open_income_window(self):
        window = tk.Toplevel(self.root)
        window.title("Add Income")
        window.geometry("400x350")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="New Income", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        tk.Label(frame, text="Source:", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        source_entry = ttk.Entry(frame)
        source_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Amount:", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        amount_entry = ttk.Entry(frame)
        amount_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Date:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        def update_date():
            top = tk.Toplevel(window)
            cal = Calendar(top, selectmode="day", date_pattern="y-mm-dd")
            cal.pack(pady=10)
            def set_date():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, cal.get_date())
                top.destroy()
            ttk.Button(top, text="Select", command=set_date).pack(pady=5)
        
        ttk.Button(frame, text="📅", command=update_date, width=2).grid(row=2, column=2, padx=5)
        
        def add_income():
            try:
                amount = amount_entry.get()
                if not amount:
                    raise ValueError("Amount cannot be empty")
                date = date_entry.get()
                income = {
                    "source": source_entry.get(),
                    "amount": float(amount),
                    "date": date,
                    "month": date[:7]  # Extract YYYY-MM
                }
                self.all_income.append(income)
                self.update_charts()
                self.save_data()
                self.month_dropdown['values'] = self.get_month_options()  # Update dropdown
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numerical amount (e.g., 50.00)")
                
        ttk.Button(window, text="Add Income", command=add_income).pack(pady=20)

    def open_expense_window(self):
        window = tk.Toplevel(self.root)
        window.title("Add Expense")
        window.geometry("400x400")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="New Expense", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        tk.Label(frame, text="Where:", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        where_entry = ttk.Entry(frame)
        where_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Amount:", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        amount_entry = ttk.Entry(frame)
        amount_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Date:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        def update_date():
            top = tk.Toplevel(window)
            cal = Calendar(top, selectmode="day", date_pattern="y-mm-dd")
            cal.pack(pady=10)
            def set_date():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, cal.get_date())
                top.destroy()
            ttk.Button(top, text="Select", command=set_date).pack(pady=5)
        
        ttk.Button(frame, text="📅", command=update_date, width=2).grid(row=2, column=2, padx=5)
        
        tk.Label(frame, text="Category:", fg="white", bg="#2d2d2d").grid(row=3, column=0, padx=5, pady=5)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=self.categories)
        category_combo.grid(row=3, column=1, padx=5, pady=5)
        category_combo.set("Other")
        
        def add_expense():
            try:
                amount = amount_entry.get()
                if not amount:
                    raise ValueError("Amount cannot be empty")
                date = date_entry.get()
                expense = {
                    "where": where_entry.get(),
                    "amount": float(amount),
                    "date": date,
                    "category": category_var.get(),
                    "month": date[:7]  # Extract YYYY-MM
                }
                self.all_expenses.append(expense)
                self.update_charts()
                self.save_data()
                self.month_dropdown['values'] = self.get_month_options()  # Update dropdown
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numerical amount (e.g., 50.00)")
                
        ttk.Button(window, text="Add Expense", command=add_expense).pack(pady=20)

    def update_charts(self):
        income, expenses = self.get_month_data(self.current_month)
        
        if self.showing_list:
            self.update_expense_table()
            return
        
        self.income_ax.clear()
        total_income = sum(i["amount"] for i in income)
        if not income:
            self.income_ax.text(0.5, 0.5, "No Income", ha='center', va='center', 
                              color="white", fontsize=12)
            self.income_center_text = self.income_ax.text(0, 0, "$0.00", 
                                                        ha='center', va='center', 
                                                        color="white", fontsize=16, fontweight='bold')
        else:
            sources = [i["source"] for i in income]
            amounts = [i["amount"] for i in income]
            explode = [0] * len(amounts)
            wedges, texts, autotexts = self.income_ax.pie(
                amounts, labels=sources, autopct='', startangle=90, 
                textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Paired.colors,
                explode=explode, labeldistance=1.1
            )
            self.income_wedges = wedges
            self.income_autotexts = autotexts
            self.income_amounts = amounts
            self.income_center_text = self.income_ax.text(0, 0, f"${total_income:.2f}", 
                                                        ha='center', va='center', 
                                                        color="white", fontsize=16, fontweight='bold')
        
        self.income_ax.set_title(f"Income Breakdown ({self.current_month})", color="white", pad=20)
        self.income_canvas.draw()
        
        self.expense_ax.clear()
        total_expense = sum(e["amount"] for e in expenses)
        if not expenses:
            self.expense_ax.text(0.5, 0.5, "No Expenses", ha='center', va='center', 
                               color="white", fontsize=12)
            self.expense_center_text = self.expense_ax.text(0, 0, "$0.00", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        else:
            category_totals = {}
            for exp in expenses:
                cat = exp["category"]
                category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
            amounts = list(category_totals.values())
            labels = list(category_totals.keys())
            explode = [0] * len(amounts)
            wedges, texts, autotexts = self.expense_ax.pie(
                amounts, labels=labels, autopct='', startangle=90, 
                textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Paired.colors,
                explode=explode, labeldistance=1.1
            )
            self.expense_wedges = wedges
            self.expense_autotexts = autotexts
            self.expense_amounts = amounts
            self.expense_categories = labels
            self.expense_center_text = self.expense_ax.text(0, 0, f"${total_expense:.2f}", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        
        self.expense_ax.set_title(f"Expense Breakdown ({self.current_month})", color="white", pad=20)
        self.expense_canvas.draw()
        
        needs_categories = ["Housing", "Transportation", "Groceries", "Utilities", "Healthcare"]
        wants_categories = ["Food", "Entertainment", "Activities", "Shopping"]
        savings_categories = ["Savings", "Charitable"]
        needs_spent = sum(e["amount"] for e in expenses if e["category"] in needs_categories)
        wants_spent = sum(e["amount"] for e in expenses if e["category"] in wants_categories)
        savings_spent = sum(e["amount"] for e in expenses if e["category"] in savings_categories)
        needs_budget = total_income * 0.50
        wants_budget = total_income * 0.30
        savings_budget = total_income * 0.20

        for widget in self.budget_frame.winfo_children():
            widget.destroy()
        
        if total_income > 0:
            budget_fig, budget_ax = plt.subplots(figsize=(8, 0.6))
            bar_height = 0.4
            needs_cmap = LinearSegmentedColormap.from_list("", ["#2E7D32", "#4CAF50"])
            wants_cmap = LinearSegmentedColormap.from_list("", ["#1565C0", "#2196F3"])
            savings_cmap = LinearSegmentedColormap.from_list("", ["#F9A825", "#FFC107"])
            needs_width = min(needs_spent, needs_budget)
            needs_bar = budget_ax.barh(0, needs_budget, height=bar_height, left=0, color="#4CAF50", alpha=0.3)
            if needs_width > 0:
                needs_fill = budget_ax.barh(0, needs_width, height=bar_height, left=0, color=needs_cmap(0.5), edgecolor="white", linewidth=1)
                needs_fill[0].set_hatch('..')
                budget_ax.text(needs_budget / 2, bar_height / 2, "Needs: 50%", ha='center', va='center', color="white", 
                              fontsize=10, fontweight='bold', bbox=dict(facecolor='black', alpha=0.4, edgecolor='none'))
            wants_width = min(wants_spent, wants_budget)
            wants_bar = budget_ax.barh(0, wants_budget, height=bar_height, left=needs_budget, color="#2196F3", alpha=0.3)
            if wants_width > 0:
                wants_fill = budget_ax.barh(0, wants_width, height=bar_height, left=needs_budget, color=wants_cmap(0.5), edgecolor="white", linewidth=1)
                wants_fill[0].set_hatch('//')
                budget_ax.text(needs_budget + wants_budget / 2, bar_height / 2, "Wants: 30%", ha='center', va='center', color="white", 
                              fontsize=10, fontweight='bold', bbox=dict(facecolor='black', alpha=0.4, edgecolor='none'))
            savings_width = min(savings_spent, savings_budget)
            savings_bar = budget_ax.barh(0, savings_budget, height=bar_height, left=needs_budget + wants_budget, color="#FFC107", alpha=0.3)
            if savings_width > 0:
                savings_fill = budget_ax.barh(0, savings_width, height=bar_height, left=needs_budget + wants_budget, color=savings_cmap(0.5), edgecolor="white", linewidth=1)
                savings_fill[0].set_hatch('xx')
                budget_ax.text(needs_budget + wants_budget + savings_budget / 2, bar_height / 2, "Savings: 20%", ha='center', va='center', color="white", 
                              fontsize=10, fontweight='bold', bbox=dict(facecolor='black', alpha=0.4, edgecolor='none'))
            budget_ax.set_xlim(0, total_income)
            budget_ax.set_ylim(0, bar_height)
            budget_ax.set_yticks([])
            budget_ax.set_xticks([])
            budget_ax.set_facecolor('#2d2d2d')
            budget_fig.patch.set_facecolor('#1a1a1a')
            for spine in budget_ax.spines.values():
                spine.set_visible(False)
            budget_ax.add_patch(patches.Rectangle((0, -0.05), total_income, bar_height + 0.1, facecolor="gray", alpha=0.2, zorder=-1))
            self.budget_canvas = tkagg.FigureCanvasTkAgg(budget_fig, master=self.budget_frame)
            self.budget_canvas.get_tk_widget().pack(fill="x")
            self.budget_canvas.draw()
        else:
            self.budget_canvas = None

        net_income = total_income - total_expense
        color = "green" if net_income >= 0 else "red"
        self.net_label.config(text=f"Net Income ({self.current_month}): ${net_income:.2f}", fg=color)

    def update_expense_table(self):
        _, expenses = self.get_month_data(self.current_month)
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        sorted_expenses = sorted(expenses, key=lambda x: x["date"], reverse=True)
        for i, exp in enumerate(sorted_expenses):
            self.expense_tree.insert("", "end", values=(
                exp["date"],
                exp["where"],
                f"${exp['amount']:.2f}",
                exp["category"]
            ), tags=('row',))
            self.expense_tree.tag_configure('row', background="#2d2d2d")
            if i < len(sorted_expenses) - 1:
                self.expense_tree.insert("", "end", values=("", "", "", ""), tags=('separator',))
                self.expense_tree.tag_configure('separator', background="#3c3f41", font=("Arial", 1))
        
        self.expense_ax.clear()
        total_expense = sum(e["amount"] for e in expenses)
        if not expenses:
            self.expense_ax.text(0.5, 0.5, "No Expenses", ha='center', va='center', 
                               color="white", fontsize=12)
            self.expense_center_text = self.expense_ax.text(0, 0, "$0.00", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        else:
            category_totals = {}
            for exp in expenses:
                cat = exp["category"]
                category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
            amounts = list(category_totals.values())
            labels = list(category_totals.keys())
            explode = [0] * len(amounts)
            wedges, texts, autotexts = self.expense_ax.pie(
                amounts, labels=labels, autopct='', startangle=90,
                textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Paired.colors,
                explode=explode, labeldistance=1.1
            )
            self.expense_wedges = wedges
            self.expense_amounts = amounts
            self.expense_categories = labels
            self.expense_center_text = self.expense_ax.text(0, 0, f"${total_expense:.2f}", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        
        self.expense_ax.set_title(f"Expense Breakdown ({self.current_month})", color="white", pad=20)
        self.expense_canvas.draw()

    def toggle_income_view(self):
        if not hasattr(self, 'showing_income_list'):
            self.showing_income_list = False
        
        if not self.showing_income_list:
            self.income_canvas.get_tk_widget().grid_remove()
            self.income_table_frame.grid()
            self.view_income_button.config(text="See Pie Chart")
            self.showing_income_list = True
            self.update_income_table()
        else:
            self.income_table_frame.grid_remove()
            self.income_canvas.get_tk_widget().grid()
            self.view_income_button.config(text="View Income List")
            self.showing_income_list = False
            self.update_charts()

    def toggle_expense_view(self):
        if not hasattr(self, 'showing_expense_list'):
            self.showing_expense_list = False
        
        if not self.showing_expense_list:
            self.expense_canvas.get_tk_widget().grid_remove()
            self.expense_table_frame.grid()
            self.view_expense_button.config(text="See Pie Chart")
            self.showing_expense_list = True
            self.update_expense_table()
        else:
            self.expense_table_frame.grid_remove()
            self.expense_canvas.get_tk_widget().grid()
            self.view_expense_button.config(text="View Expense List")
            self.showing_expense_list = False
            self.update_charts()

    def update_income_table(self):
        income, _ = self.get_month_data(self.current_month)
        for item in self.income_tree.get_children():
            self.income_tree.delete(item)
        sorted_income = sorted(income, key=lambda x: x["date"], reverse=True)
        for i, inc in enumerate(sorted_income):
            self.income_tree.insert("", "end", values=(
                inc["date"],
                inc["source"],
                f"${inc['amount']:.2f}"
            ), tags=('row',))
            self.income_tree.tag_configure('row', background="#2d2d2d")
            if i < len(sorted_income) - 1:
                self.income_tree.insert("", "end", values=("", "", ""), tags=('separator',))
                self.income_tree.tag_configure('separator', background="#3c3f41", font=("Arial", 1))

    def update_expense_table(self):
        _, expenses = self.get_month_data(self.current_month)
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
        sorted_expenses = sorted(expenses, key=lambda x: x["date"], reverse=True)
        for i, exp in enumerate(sorted_expenses):
            self.expense_tree.insert("", "end", values=(
                exp["date"],
                exp["where"],
                f"${exp['amount']:.2f}",
                exp["category"]
            ), tags=('row',))
            self.expense_tree.tag_configure('row', background="#2d2d2d")
            if i < len(sorted_expenses) - 1:
                self.expense_tree.insert("", "end", values=("", "", "", ""), tags=('separator',))
                self.expense_tree.tag_configure('separator', background="#3c3f41", font=("Arial", 1))

    def hide_analysis_view(self):
        self.analysis_frame.grid_remove()
        self.table_frame.grid_remove()  # Ensure expense table stays hidden
        self.income_canvas.get_tk_widget().grid()
        self.view_list_button.config(text="View List", command=self.toggle_expense_view)
        self.showing_list = False
        self.update_charts()

    def on_income_hover(self, event):
        income, _ = self.get_month_data(self.current_month)
        if not income or self.showing_list:
            return
        
        amounts = [i["amount"] for i in income]
        sources = [i["source"] for i in income]
        explode = [0] * len(amounts)
        hovered = False
        
        for i, wedge in enumerate(self.income_wedges):
            if event.inaxes == self.income_ax and wedge.contains_point([event.x, event.y]):
                explode[i] = 0.1
                hovered_text = f"${self.income_amounts[i]:.2f}"
                hovered = True
                break
        
        self.income_ax.clear()
        wedges, texts, autotexts = self.income_ax.pie(
            amounts, labels=sources, autopct='', startangle=90,
            textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Paired.colors,
            explode=explode, labeldistance=1.1
        )
        self.income_wedges = wedges
        total_income = sum(i["amount"] for i in income)
        center_text = hovered_text if hovered else f"${total_income:.2f}"
        self.income_center_text = self.income_ax.text(
            0, 0, center_text, ha='center', va='center', fontsize=16, fontweight='bold', color="white"
        )
        self.income_ax.set_title(f"Income Breakdown ({self.current_month})", color="white", pad=20)
        self.income_canvas.draw()

    def on_expense_hover(self, event):
        income, expenses = self.get_month_data(self.current_month)
        if not expenses:
            return
        
        total_income = sum(i["amount"] for i in income)  # Get total income for percentage calculation
        
        category_totals = {}
        for exp in expenses:
            cat = exp["category"]
            category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
        amounts = list(category_totals.values())
        labels = list(category_totals.keys())
        explode = [0] * len(amounts)
        hovered_text = None
        hovered = False

        for i, wedge in enumerate(self.expense_wedges):
            if event.inaxes == self.expense_ax and wedge.contains_point([event.x, event.y]):
                explode[i] = 0.1
                percentage = (amounts[i] / total_income) * 100 if total_income > 0 else 0
                hovered_text = f"${amounts[i]:.2f}\n{percentage:.1f}% of Income"
                hovered = True
                break
        
        self.expense_ax.clear()
        wedges, texts, autotexts = self.expense_ax.pie(
            amounts, labels=labels, autopct='', startangle=90,
            textprops={'color': 'white'}, colors=plt.cm.Paired.colors,
            explode=explode, labeldistance=1.1
        )
        self.expense_wedges = wedges
        self.expense_autotexts = autotexts
        total_expense = sum(amounts)
        center_text = hovered_text if hovered else f"${total_expense:.2f}"
        self.expense_center_text = self.expense_ax.text(
            0, 0, center_text, ha='center', va='center', fontsize=16, fontweight='bold', color="white"
        )
        self.expense_ax.set_title(f"Expense Breakdown ({self.current_month})", color="white", pad=20)
        self.expense_canvas.draw()

    def on_income_click(self, event):
        income, _ = self.get_month_data(self.current_month)
        if event.inaxes != self.income_ax or not income:
            return
        self.detail_listbox.delete(0, tk.END)
        for i, wedge in enumerate(self.income_wedges):
            if wedge.contains_point([event.x, event.y]):
                inc = income[i]
                self.detail_listbox.insert(tk.END, f"Income: {inc['source']}")
                self.detail_listbox.insert(tk.END, f"Amount: ${inc['amount']:.2f}")
                self.detail_listbox.insert(tk.END, f"Date: {inc['date']}")
                self.detail_listbox.insert(tk.END, "-" * 30)
                break

    def on_expense_click(self, event):
        _, expenses = self.get_month_data(self.current_month)
        if event.inaxes != self.expense_ax or not expenses:
            return
        self.detail_listbox.delete(0, tk.END)
        for i, wedge in enumerate(self.expense_wedges):
            if wedge.contains_point([event.x, event.y]):
                category = self.expense_categories[i]
                self.detail_listbox.insert(tk.END, f"Category: {category}")
                total = 0
                for exp in expenses:
                    if exp["category"] == category:
                        self.detail_listbox.insert(tk.END, f"{exp['where']} - ${exp['amount']:.2f} ({exp['date']})")
                        total += exp["amount"]
                self.detail_listbox.insert(tk.END, f"Total: ${total:.2f}")
                self.detail_listbox.insert(tk.END, "-" * 30)
                break
    
    def edit_income(self):
        selected = self.income_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an income to edit.")
            return
        
        item = self.income_tree.item(selected[0])
        values = item['values']
        if not values or values[0] == "":
            messagebox.showwarning("Warning", "Please select a valid income entry.")
            return
        
        date, source, amount_str = values
        amount = float(amount_str.replace("$", ""))
        
        for i, inc in enumerate(self.all_income):
            if inc["date"] == date and inc["source"] == source and inc["amount"] == amount:
                income_index = i
                break
        else:
            messagebox.showerror("Error", "Income not found.")
            return

        window = tk.Toplevel(self.root)
        window.title("Edit Income")
        window.geometry("400x350")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="Edit Income", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        tk.Label(frame, text="Source:", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        source_entry = ttk.Entry(frame)
        source_entry.grid(row=0, column=1, padx=5, pady=5)
        source_entry.insert(0, source)
        
        tk.Label(frame, text="Amount:", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        amount_entry = ttk.Entry(frame)
        amount_entry.grid(row=1, column=1, padx=5, pady=5)
        amount_entry.insert(0, amount)
        
        tk.Label(frame, text="Date:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, date)
        
        def update_date():
            top = tk.Toplevel(window)
            cal = Calendar(top, selectmode="day", date_pattern="y-mm-dd")
            cal.pack(pady=10)
            def set_date():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, cal.get_date())
                top.destroy()
            ttk.Button(top, text="Select", command=set_date).pack(pady=5)
        
        ttk.Button(frame, text="📅", command=update_date, width=2).grid(row=2, column=2, padx=5)
        
        def save_edit():
            try:
                new_amount = float(amount_entry.get())
                new_date = date_entry.get()
                self.all_income[income_index] = {
                    "source": source_entry.get(),
                    "amount": new_amount,
                    "date": new_date,
                    "month": new_date[:7]
                }
                self.save_data()
                self.update_income_table()
                self.update_charts()
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numerical amount (e.g., 50.00)")
        
        ttk.Button(window, text="Save Changes", command=save_edit).pack(pady=20)

    def edit_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to edit.")
            return
        
        item = self.expense_tree.item(selected[0])
        values = item['values']
        if not values or values[0] == "":
            messagebox.showwarning("Warning", "Please select a valid expense entry.")
            return
        
        date, where, amount_str, category = values
        amount = float(amount_str.replace("$", ""))
        
        for i, exp in enumerate(self.all_expenses):
            if (exp["date"] == date and exp["where"] == where and 
                exp["amount"] == amount and exp["category"] == category):
                expense_index = i
                break
        else:
            messagebox.showerror("Error", "Expense not found.")
            return

        window = tk.Toplevel(self.root)
        window.title("Edit Expense")
        window.geometry("400x400")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="Edit Expense", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        tk.Label(frame, text="Where:", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        where_entry = ttk.Entry(frame)
        where_entry.grid(row=0, column=1, padx=5, pady=5)
        where_entry.insert(0, where)
        
        tk.Label(frame, text="Amount:", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        amount_entry = ttk.Entry(frame)
        amount_entry.grid(row=1, column=1, padx=5, pady=5)
        amount_entry.insert(0, amount)
        
        tk.Label(frame, text="Date:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.grid(row=2, column=1, padx=5, pady=5)
        date_entry.insert(0, date)
        
        def update_date():
            top = tk.Toplevel(window)
            cal = Calendar(top, selectmode="day", date_pattern="y-mm-dd")
            cal.pack(pady=10)
            def set_date():
                date_entry.delete(0, tk.END)
                date_entry.insert(0, cal.get_date())
                top.destroy()
            ttk.Button(top, text="Select", command=set_date).pack(pady=5)
        
        ttk.Button(frame, text="📅", command=update_date, width=2).grid(row=2, column=2, padx=5)
        
        tk.Label(frame, text="Category:", fg="white", bg="#2d2d2d").grid(row=3, column=0, padx=5, pady=5)
        category_var = tk.StringVar(value=category)
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=self.categories, state="readonly")
        category_combo.grid(row=3, column=1, padx=5, pady=5)
        
        def save_edit():
            try:
                new_amount = float(amount_entry.get())
                new_date = date_entry.get()
                self.all_expenses[expense_index] = {
                    "where": where_entry.get(),
                    "amount": new_amount,
                    "date": new_date,
                    "category": category_var.get(),
                    "month": new_date[:7]
                }
                self.save_data()
                self.update_expense_table()
                self.update_charts()
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numerical amount (e.g., 50.00)")
        
        ttk.Button(window, text="Save Changes", command=save_edit).pack(pady=20)

    def delete_income(self):
        selected = self.income_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an income to delete.")
            return
        
        item = self.income_tree.item(selected[0])
        values = item['values']
        if not values or values[0] == "":
            messagebox.showwarning("Warning", "Please select a valid income entry.")
            return
        
        date, source, amount_str = values
        amount = float(amount_str.replace("$", ""))
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this income?"):
            return
        
        for i, inc in enumerate(self.all_income):
            if inc["date"] == date and inc["source"] == source and inc["amount"] == amount:
                del self.all_income[i]
                break
        
        self.save_data()
        self.update_income_table()
        self.update_charts()

    def delete_expense(self):
        selected = self.expense_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an expense to delete.")
            return
        
        item = self.expense_tree.item(selected[0])
        values = item['values']
        if not values or values[0] == "":
            messagebox.showwarning("Warning", "Please select a valid expense entry.")
            return
        
        date, where, amount_str, category = values
        amount = float(amount_str.replace("$", ""))
        
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            return
        
        for i, exp in enumerate(self.all_expenses):
            if (exp["date"] == date and exp["where"] == where and 
                exp["amount"] == amount and exp["category"] == category):
                del self.all_expenses[i]
                break
        
        self.save_data()
        self.update_expense_table()
        self.update_charts()

    def analyze_months(self):
        window = tk.Toplevel(self.root)
        window.title("Analyze Months")
        window.geometry("400x400")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="Analyze Spending", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        # Month 1 Dropdown
        tk.Label(frame, text="Month 1:", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        month1_var = tk.StringVar(value=self.current_month)  # Default to current month
        month1_combo = ttk.Combobox(frame, textvariable=month1_var, values=self.get_month_options(), state="readonly")
        month1_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Month 2 Dropdown
        tk.Label(frame, text="Month 2:", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        month2_var = tk.StringVar(value=self.get_month_options()[1] if len(self.get_month_options()) > 1 else self.current_month)  # Default to previous month if available
        month2_combo = ttk.Combobox(frame, textvariable=month2_var, values=self.get_month_options(), state="readonly")
        month2_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Category Dropdown (already a Combobox, now styled by TCombobox)
        tk.Label(frame, text="Category:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        category_var = tk.StringVar()
        category_options = ["All Categories"] + self.categories
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=category_options, state="readonly")
        category_combo.grid(row=2, column=1, padx=5, pady=5)
        category_combo.set("All Categories")
        
        def compare_months():
            try:
                month1 = month1_var.get()
                month2 = month2_var.get()
                category = category_var.get()
                _, expenses1 = self.get_month_data(month1)
                _, expenses2 = self.get_month_data(month2)
                
                # Show analysis frame and hide income chart
                self.income_canvas.get_tk_widget().grid_remove()
                self.table_frame.grid_remove()  # Hide expense table if visible
                self.analysis_frame.grid()
                self.view_list_button.config(text="Back to Charts", command=self.hide_analysis_view)
                self.showing_list = True  # Reuse flag to track state
                
                self.analysis_listbox.delete(0, tk.END)
                
                if category == "All Categories":
                    month1_total = sum(exp["amount"] for exp in expenses1)
                    month2_total = sum(exp["amount"] for exp in expenses2)
                    self.analysis_listbox.insert(tk.END, "✨ MONTHLY SPENDING ANALYSIS ✨")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    self.analysis_listbox.insert(tk.END, f"📅 {month1}: 💰 ${month1_total:.2f}")
                    self.analysis_listbox.insert(tk.END, f"📅 {month2}: 💰 ${month2_total:.2f}")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    if month1_total > month2_total:
                        self.analysis_listbox.insert(tk.END, f"📈 {month1} outspent {month2} by ${month1_total - month2_total:.2f}")
                    elif month2_total > month1_total:
                        self.analysis_listbox.insert(tk.END, f"📈 {month2} outspent {month1} by ${month2_total - month1_total:.2f}")
                    else:
                        self.analysis_listbox.insert(tk.END, "⚖️ Total spending is equal!")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    
                    self.analysis_listbox.insert(tk.END, "🔍 Category Breakdown")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    for cat in self.categories:
                        month1_cat_total = sum(exp["amount"] for exp in expenses1 if exp["category"] == cat)
                        month2_cat_total = sum(exp["amount"] for exp in expenses2 if exp["category"] == cat)
                        if month1_cat_total > 0 or month2_cat_total > 0:
                            self.analysis_listbox.insert(tk.END, f"🏷️ {cat.upper()}")
                            self.analysis_listbox.insert(tk.END, f"  📅 {month1}: 💵 ${month1_cat_total:.2f}")
                            self.analysis_listbox.insert(tk.END, f"  📅 {month2}: 💵 ${month2_cat_total:.2f}")
                            if month1_cat_total > month2_cat_total:
                                diff = month1_cat_total - month2_cat_total
                                self.analysis_listbox.insert(tk.END, f"  📈 {month1} outspent {month2} by ${diff:.2f}")
                            elif month2_cat_total > month1_cat_total:
                                diff = month2_cat_total - month1_cat_total
                                self.analysis_listbox.insert(tk.END, f"  📈 {month2} outspent {month1} by ${diff:.2f}")
                            else:
                                self.analysis_listbox.insert(tk.END, "  ⚖️ Even spending")
                            self.analysis_listbox.insert(tk.END, "─" * 30)
                else:
                    month1_total = sum(exp["amount"] for exp in expenses1 if exp["category"] == category)
                    month2_total = sum(exp["amount"] for exp in expenses2 if exp["category"] == category)
                    self.analysis_listbox.insert(tk.END, f"✨ ANALYSIS FOR {category.upper()} ✨")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    self.analysis_listbox.insert(tk.END, f"📅 {month1}: 💰 ${month1_total:.2f}")
                    self.analysis_listbox.insert(tk.END, f"📅 {month2}: 💰 ${month2_total:.2f}")
                    self.analysis_listbox.insert(tk.END, "═════════════════════════════")
                    if month1_total > month2_total:
                        self.analysis_listbox.insert(tk.END, f"📈 {month1} outspent {month2} by ${month1_total - month2_total:.2f}")
                    elif month2_total > month1_total:
                        self.analysis_listbox.insert(tk.END, f"📈 {month2} outspent {month1} by ${month2_total - month1_total:.2f}")
                    else:
                        self.analysis_listbox.insert(tk.END, "⚖️ Even Spending")
                
                window.destroy()
            except Exception as e:
                print(f"Error: {e}")
                messagebox.showerror("Error", "An error occurred. Please ensure valid months are selected.")
        
        ttk.Button(window, text="Compare", command=compare_months).pack(pady=20)
    
    
    def on_closing(self):
        self.save_data()
        plt.close('all')
        self.root.destroy()
        self.root.quit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tracker = BudgetTracker()
    tracker.run()