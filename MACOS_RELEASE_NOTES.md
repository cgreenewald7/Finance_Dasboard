Budget Tracker for macOS 15 or later, with the same features as the Python app:
income and expense editing, categories and goals, credit card authorized users,
savings/investments, charts, monthly analysis, CSV and Excel export, and light/dark themes.

- Apple Silicon (M1 and newer): download `BudgetTracker-macOS-arm64.zip`.
- Intel: download `BudgetTracker-macOS-x86_64.zip`.

Unzip, drag BudgetTracker.app to Applications, and open it. Python and Excel are
not required. This free build is ad-hoc signed, without Apple notarization.
If macOS blocks it, attempt to open it once, then go to System Settings →
Privacy & Security → Open Anyway and confirm.

Allow access to Documents if requested. Data stays in
`~/Documents/BudgetTracker/budget_data.csv`. Back up that file before upgrades;
it can also be copied from a Windows installation to move your existing budget.

The `.sha256` files contain archive checksums. These builds target macOS 15+;
older macOS versions are not validated by this release workflow.
