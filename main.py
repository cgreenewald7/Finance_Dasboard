import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
import tkinter as tk
from tkinter import ttk, messagebox  # Added messagebox for better error handling
from tkcalendar import Calendar
from datetime import datetime, timedelta
import matplotlib.patches as patches

class BudgetTracker:
    def __init__(self):
        self.expenses = []
        self.income = []
        
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
        
        self.showing_list = False
        self.current_month = datetime.now().strftime("%Y-%m")
        self.setup_gui()
        
    def setup_gui(self):
        header_frame = tk.Frame(self.root, bg="#252526", pady=10)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, 
                              text="Budget Master Beta",
                              font=("Arial", 24, "bold"),
                              fg="#ffffff",
                              bg="#252526")
        title_label.pack()

        # Month selection dropdown in top right
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
        
        self.income_fig, self.income_ax = plt.subplots(figsize=(5, 5))
        self.income_fig.patch.set_facecolor('#1a1a1a')
        self.income_ax.set_facecolor('#2d2d2d')
        self.income_canvas = tkagg.FigureCanvasTkAgg(self.income_fig, master=self.chart_frame)
        self.income_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10)
        self.income_fig.canvas.mpl_connect('motion_notify_event', self.on_income_hover)
        self.income_fig.canvas.mpl_connect('button_press_event', self.on_income_click)
        
        self.expense_fig, self.expense_ax = plt.subplots(figsize=(5, 5))
        self.expense_fig.patch.set_facecolor('#1a1a1a')
        self.expense_ax.set_facecolor('#2d2d2d')
        self.expense_canvas = tkagg.FigureCanvasTkAgg(self.expense_fig, master=self.chart_frame)
        self.expense_canvas.get_tk_widget().grid(row=0, column=1, sticky="nsew", padx=10)
        self.expense_fig.canvas.mpl_connect('motion_notify_event', self.on_expense_hover)
        self.expense_fig.canvas.mpl_connect('button_press_event', self.on_expense_click)
        
        self.view_list_button = ttk.Button(self.chart_frame, text="View List", 
                                          command=self.toggle_expense_view, style="TButton")
        self.view_list_button.grid(row=1, column=1, pady=5)
        
        # Expense Listbox (initially hidden)
        self.expense_listbox = tk.Listbox(self.chart_frame, bg="#2d2d2d", fg="white", 
                                         font=("Arial", 12), width=50, height=20)
        self.expense_listbox.grid(row=0, column=0, sticky="nsew", padx=10)
        self.expense_listbox.grid_remove()  # Hide initially

        # Budget bar frame (new, placed above net income)
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
        """Generate a list of month options (e.g., '2025-01', '2025-02') for the last 12 months and next 6 months."""
        current_date = datetime.now()
        options = []
        for i in range(-12, 7):  # Last 12 months and next 6 months
            month_date = current_date + timedelta(days=30 * i)
            options.append(month_date.strftime("%Y-%m"))
        return sorted(options, reverse=True)  # Newest first
    
    def update_month_view(self, event):
        """Update the view when a new month is selected from the dropdown."""
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
                income = {
                    "source": source_entry.get(),
                    "amount": float(amount),
                    "date": date_entry.get()
                }
                self.income.append(income)
                self.update_charts()
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
                expense = {
                    "where": where_entry.get(),
                    "amount": float(amount),
                    "date": date_entry.get(),
                    "category": category_var.get()
                }
                self.expenses.append(expense)
                self.update_charts()
                window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid numerical amount (e.g., 50.00)")
                
        ttk.Button(window, text="Add Expense", command=add_expense).pack(pady=20)
        
    def update_charts(self):
        if self.showing_list:
            self.update_expense_list()
            return
        
        # Income Chart
        self.income_ax.clear()
        total_income = sum(i["amount"] for i in self.income)
        if not self.income:
            self.income_ax.text(0.5, 0.5, "No Income", ha='center', va='center', 
                              color="white", fontsize=12)
            self.income_center_text = self.income_ax.text(0, 0, "$0.00", 
                                                        ha='center', va='center', 
                                                        color="white", fontsize=16, fontweight='bold')
        else:
            month_income = [i for i in self.income if i["date"].startswith(self.current_month)]
            sources = [i["source"] for i in self.income]
            amounts = [i["amount"] for i in self.income]
            explode = [0] * len(amounts)

            wedges, texts, autotexts = self.income_ax.pie(
                amounts, labels=sources, autopct='', startangle=90, 
                textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Set3.colors,
                explode=explode, labeldistance=1.1
            )

            self.income_wedges = wedges
            self.income_autotexts = autotexts
            self.income_amounts = amounts
            self.income_center_text = self.income_ax.text(0, 0, f"${total_income:.2f}", 
                                                        ha='center', va='center', 
                                                        color="white", fontsize=16, fontweight='bold')
        
        self.income_ax.set_title("Income Breakdown", color="white", pad=20)
        self.income_canvas.draw()
        
        # Expense Chart
        self.expense_ax.clear()
        total_expense = sum(e["amount"] for e in self.expenses)
        if not self.expenses:
            self.expense_ax.text(0.5, 0.5, "No Expenses", ha='center', va='center', 
                               color="white", fontsize=12)
            self.expense_center_text = self.expense_ax.text(0, 0, "$0.00", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        else:
            category_totals = {}
            for exp in self.expenses:
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
        
        self.expense_ax.set_title("Expense Breakdown", color="white", pad=20)
        self.expense_canvas.draw()
        
        # 50/30/20 Budget Bar 
        needs_categories = ["Housing", "Transportation", "Groceries", "Utilities", "Healthcare"]
        wants_categories = ["Food", "Entertainment", "Activities", "Shopping"]
        savings_categories = ["Savings", "Charitable"]

        needs_spent = sum(e["amount"] for e in self.expenses if e["date"].startswith(self.current_month) and e["category"] in needs_categories)
        wants_spent = sum(e["amount"] for e in self.expenses if e["date"].startswith(self.current_month) and e["category"] in wants_categories)
        savings_spent = sum(e["amount"] for e in self.expenses if e["date"].startswith(self.current_month) and e["category"] in savings_categories)

        needs_budget = total_income * 0.50
        wants_budget = total_income * 0.30
        savings_budget = total_income * 0.20

        # Create sleek budget bar with soft gray color and rounded edges
        budget_fig, budget_ax = plt.subplots(figsize=(7, 0.4))
        bar_height = 0.2
        # Needs section with left rounded edge
        needs_width = min(needs_spent, needs_budget)
        if total_income > 0:
            needs_rect = patches.FancyBboxPatch((0, 0), needs_width, bar_height, 
                                            boxstyle="round,pad=0.5,rounding_size=0.1", 
                                            facecolor='#4CAF50', edgecolor='white', linewidth=1, alpha=0.9)
            budget_ax.add_patch(needs_rect)

        # Wants section (middle, no curved edges)
        wants_width = min(wants_spent, wants_budget)
        if total_income > 0:
            wants_rect = patches.FancyBboxPatch((needs_budget + 0.05 * total_income, 0), wants_width, bar_height, 
                                            boxstyle="round,pad=0.05,rounding_size=1", 
                                            facecolor='#2196F3', edgecolor='white', linewidth=1, alpha=0.9)
            budget_ax.add_patch(wants_rect)

        # Savings section with right rounded edge
        savings_width = min(savings_spent, savings_budget)
        if total_income > 0:
            savings_rect = patches.FancyBboxPatch((needs_budget + wants_budget + 0.1 * total_income, 0), savings_width, bar_height, 
                                                boxstyle="round,pad=0.05,rounding_size=1", 
                                                facecolor='#FFC107', edgecolor='white', linewidth=1, alpha=0.9)
            budget_ax.add_patch(savings_rect)

        # # Add labels
        # if total_income > 0:
        #     budget_ax.text(needs_budget / 2, bar_height + 0.05, f"Needs\n${needs_spent:.2f}/{needs_budget:.2f}", 
        #                 ha='center', va='bottom', color="white", fontsize=8, fontweight='bold', 
        #                 bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=2))
        #     budget_ax.text(needs_budget + wants_budget / 2 + 0.05 * total_income, bar_height + 0.05, f"Wants\n${wants_spent:.2f}/{wants_budget:.2f}", 
        #                 ha='center', va='bottom', color="white", fontsize=8, fontweight='bold', 
        #                 bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=2))
        #     budget_ax.text(needs_budget + wants_budget + savings_budget / 2 + 0.1 * total_income, bar_height + 0.05, f"Savings\n${savings_spent:.2f}/{savings_budget:.2f}", 
        #                 ha='center', va='bottom', color="white", fontsize=8, fontweight='bold', 
        #                 bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=2))

        # Remove the grid, ticks, and set smooth background
        budget_ax.set_xlim(0, total_income if total_income > 0 else 1)
        budget_ax.set_ylim(0, 0.4)
        budget_ax.set_yticks([])
        budget_ax.set_xticks([])
        budget_ax.set_facecolor('#2d2d2d')  # Dark background
        budget_fig.patch.set_facecolor('#1a1a1a')  # Dark background for the figure

        # Remove green border and spines around the plot
        for spine in budget_ax.spines.values():
            spine.set_visible(False)

        # Clear previous budget bar and draw new one
        for widget in self.budget_frame.winfo_children():
            widget.destroy()
        budget_canvas = tkagg.FigureCanvasTkAgg(budget_fig, master=self.budget_frame)
        budget_canvas.get_tk_widget().pack(fill="x")
        budget_canvas.draw()

        # Update Net Income
        current_month = datetime.now().strftime("%Y-%m")
        month_income = sum(i["amount"] for i in self.income if i["date"].startswith(current_month))
        month_expense = sum(e["amount"] for e in self.expenses if e["date"].startswith(current_month))
        net_income = month_income - month_expense
        color = "green" if net_income >= 0 else "red"
        self.net_label.config(text=f"Net Income ({current_month}): ${net_income:.2f}", fg=color)
        

    def update_expense_list(self):
        self.expense_listbox.delete(0, tk.END)
        for exp in self.expenses:
            self.expense_listbox.insert(tk.END, f"{exp['where']} - ${exp['amount']:.2f} ({exp['date']}) - {exp['category']}")
        
        # Expense Chart (still visible)
        self.expense_ax.clear()
        total_expense = sum(e["amount"] for e in self.expenses)
        if not self.expenses:
            self.expense_ax.text(0.5, 0.5, "No Expenses", ha='center', va='center', 
                               color="white", fontsize=12)
            self.expense_center_text = self.expense_ax.text(0, 0, "$0.00", 
                                                          ha='center', va='center', 
                                                          color="white", fontsize=16, fontweight='bold')
        else:
            category_totals = {}
            for exp in self.expenses:
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
        
        self.expense_ax.set_title("Expense Breakdown", color="white", pad=20)
        self.expense_canvas.draw()

    def toggle_expense_view(self):
        if not self.showing_list:
            # Hide income chart, show expense list
            self.income_canvas.get_tk_widget().grid_remove()
            self.expense_listbox.grid()
            self.view_list_button.config(text="See Pie Chart")
            self.showing_list = True
            self.update_expense_list()
        else:
            # Hide expense list, show income chart
            self.expense_listbox.grid_remove()
            self.income_canvas.get_tk_widget().grid()
            self.view_list_button.config(text="View List")
            self.showing_list = False
            self.update_charts()

    def on_income_hover(self, event):
        if not self.income or self.showing_list:
            return
        
        amounts = [i["amount"] for i in self.income]
        sources = [i["source"] for i in self.income]
        explode = [0] * len(amounts)  # Match length to number of wedges
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
            textprops={'color': 'white', 'fontsize': 10}, colors=plt.cm.Set3.colors,
            explode=explode, labeldistance=1.1
        )
        
        self.income_wedges = wedges
        total_income = sum(i["amount"] for i in self.income)
        center_text = hovered_text if hovered else f"${total_income:.2f}"
        
        self.income_center_text = self.income_ax.text(
            0, 0, center_text, ha='center', va='center', fontsize=14, color="white"
        )
        
        self.income_ax.set_title("Income Breakdown", color="white", pad=20)
        self.income_canvas.draw()

    def on_expense_hover(self, event):
        if not self.expenses:
            return
        
        # Aggregate expenses by category
        category_totals = {}
        for exp in self.expenses:
            cat = exp["category"]
            category_totals[cat] = category_totals.get(cat, 0) + exp["amount"]
        
        amounts = list(category_totals.values())
        labels = list(category_totals.keys())
        
        # Default explode state (no slice exploded)
        explode = [0] * len(amounts)
        hovered_text = None
        hovered = False

        # Check if a wedge is hovered over
        for i, wedge in enumerate(self.expense_wedges):
            if event.inaxes == self.expense_ax and wedge.contains_point([event.x, event.y]):
                explode[i] = 0.1
                hovered_text = f"${amounts[i]:.2f}"
                hovered = True
                break  # Only one section should be exploded at a time
        
        # Clear and redraw the chart
        self.expense_ax.clear()
        
        # Redraw pie chart with updated explode effect
        wedges, texts, autotexts = self.expense_ax.pie(
            amounts, labels=labels, autopct='', startangle=90,
            textprops={'color': 'white'}, colors=plt.cm.Paired.colors,
            explode=explode, labeldistance=1.1
        )

        # # Hide text labels to maintain clean UI
        # for text in texts:
        #     text.set_visible(False)
        # for autotext in autotexts:
        #     autotext.set_visible(False)
        
        # Update stored references
        self.expense_wedges = wedges
        self.expense_autotexts = autotexts

        # Restore or update the center text
        total_expense = sum(self.expense_amounts)
        center_text = hovered_text if hovered else f"${total_expense:.2f}"

        # Explicitly re-add the center text after clearing the axis
        self.expense_center_text = self.expense_ax.text(
            0, 0, center_text, ha='center', va='center', fontsize=14, color="white"
        )

        # Restore chart title and update canvas
        self.expense_ax.set_title("Expense Breakdown", color="white", pad=20)
        self.expense_canvas.draw()
        
    def on_income_click(self, event):
        if event.inaxes != self.income_ax or not self.income:
            return
        self.detail_listbox.delete(0, tk.END)
        for i, wedge in enumerate(self.income_wedges):
            if wedge.contains_point([event.x, event.y]):
                inc = self.income[i]
                self.detail_listbox.insert(tk.END, f"Income: {inc['source']}")
                self.detail_listbox.insert(tk.END, f"Amount: ${inc['amount']:.2f}")
                self.detail_listbox.insert(tk.END, f"Date: {inc['date']}")
                self.detail_listbox.insert(tk.END, "-" * 30)
                break
        
    def on_expense_click(self, event):
        if event.inaxes != self.expense_ax or not self.expenses:
            return
        self.detail_listbox.delete(0, tk.END)
        for i, wedge in enumerate(self.expense_wedges):
            if wedge.contains_point([event.x, event.y]):
                category = self.expense_categories[i]
                self.detail_listbox.insert(tk.END, f"Category: {category}")
                total = 0
                for exp in self.expenses:
                    if exp["category"] == category:
                        self.detail_listbox.insert(tk.END, f"{exp['where']} - ${exp['amount']:.2f} ({exp['date']})")
                        total += exp["amount"]
                self.detail_listbox.insert(tk.END, f"Total: ${total:.2f}")
                self.detail_listbox.insert(tk.END, "-" * 30)
                break
    
    def analyze_months(self):
        window = tk.Toplevel(self.root)
        window.title("Analyze Months")
        window.geometry("400x400")
        window.configure(bg="#2d2d2d")
        
        tk.Label(window, text="Analyze Spending", font=("Arial", 16, "bold"), 
                fg="white", bg="#2d2d2d").pack(pady=10)
        
        frame = tk.Frame(window, bg="#2d2d2d")
        frame.pack(pady=10)
        
        tk.Label(frame, text="Month 1 (YYYY-MM):", fg="white", bg="#2d2d2d").grid(row=0, column=0, padx=5, pady=5)
        month1_entry = ttk.Entry(frame)
        month1_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Month 2 (YYYY-MM):", fg="white", bg="#2d2d2d").grid(row=1, column=0, padx=5, pady=5)
        month2_entry = ttk.Entry(frame)
        month2_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(frame, text="Category:", fg="white", bg="#2d2d2d").grid(row=2, column=0, padx=5, pady=5)
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=self.categories)
        category_combo.grid(row=2, column=1, padx=5, pady=5)
        category_combo.set("Other")
        
        def compare_months():
            try:
                month1 = month1_entry.get()
                month2 = month2_entry.get()
                category = category_var.get()
                
                month1_total = sum(exp["amount"] for exp in self.expenses 
                                 if exp["date"].startswith(month1) and exp["category"] == category)
                month2_total = sum(exp["amount"] for exp in self.expenses 
                                 if exp["date"].startswith(month2) and exp["category"] == category)
                
                self.detail_listbox.delete(0, tk.END)
                self.detail_listbox.insert(tk.END, f"Analysis for {category}:")
                self.detail_listbox.insert(tk.END, f"{month1}: ${month1_total:.2f}")
                self.detail_listbox.insert(tk.END, f"{month2}: ${month2_total:.2f}")
                self.detail_listbox.insert(tk.END, "-" * 30)
                if month1_total > month2_total:
                    self.detail_listbox.insert(tk.END, f"More spent in {month1}")
                elif month2_total > month1_total:
                    self.detail_listbox.insert(tk.END, f"More spent in {month2}")
                else:
                    self.detail_listbox.insert(tk.END, "Equal spending")
                
                window.destroy()
            except Exception as e:
                print(f"Error: {e}")
                
        ttk.Button(window, text="Compare", command=compare_months).pack(pady=20)
    
    def on_closing(self):
        plt.close('all')
        self.root.destroy()
        self.root.quit()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    tracker = BudgetTracker()
    tracker.run()

