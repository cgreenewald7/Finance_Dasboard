# macOS release guide

## Feasibility and cost

The app uses Tkinter, Matplotlib, tkcalendar and openpyxl; none of its current
features requires Windows or a paid service. The release bundles Python and
these dependencies, including Excel export (Microsoft Excel is not required).
The same data format and `~/Documents/BudgetTracker/budget_data.csv` location
are retained. The Mac interface uses Helvetica Neue instead of Segoe UI.

This release targets macOS 15 or later, with separate native Apple Silicon
and Intel downloads. Older macOS versions are not validated.

Standard GitHub Actions runners are free for public repositories. Private
repositories have a limited allowance; if you want to guarantee no hosting
build charges, use the local build instructions instead. Do not change your
repository's visibility just to run this workflow.

The free app uses ad-hoc signing, without a paid Apple Developer certificate
or notarization. Downloaded copies may need approval in System Settings →
Privacy & Security → Open Anyway. This is a distribution difference, not a
missing app feature. See [Apple's instructions](https://support.apple.com/en-us/102445)
and [GitHub's runner billing documentation](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

## Push and create the draft release

Run these commands in Terminal. This guide uses the next version, `2.0.2`,
with tag `v2.0.2-macos`; existing Windows tags and releases are preserved.

```bash
cd /Users/calvin/code/Finance_Dasboard
git status --short
git add budget_track.py requirements.txt requirements-build.txt \
  BudgetTracker-macOS.spec icon.icns icon.ico .gitignore \
  .github/workflows/macos-release.yml scripts/build_macos.sh \
  release_checks.py MACOS_RELEASE.md MACOS_RELEASE_NOTES.md ReadMe.md
git commit -m "Prepare native macOS builds and draft release workflow"
git push origin main
git tag v2.0.2-macos
git push origin v2.0.2-macos
```

If the tag already exists on GitHub, use a new version and update both
`BUDGETTRACKER_VERSION` and the release title in the workflow first. Do not
replace existing release tags.

1. Open https://github.com/cgreenewald7/Finance_Dasboard/actions and select
   **macOS release**. Both build jobs and **draft-release** must succeed.
2. Open https://github.com/cgreenewald7/Finance_Dasboard/releases and find
   the draft **Budget Tracker 2.0.2 for macOS**.
3. Download the ZIP for your Mac (arm64 for M-series, x86_64 for Intel).
   Unzip it, move the app to Applications and open it. Approve it through
   Privacy & Security if blocked, and allow Documents access when prompted.
4. Before publishing, back up your budget file and check adding/editing/deleting
   income, expenses and savings; credit card authorized users; category and
   percentage goals; charts and list views; monthly comparison; both exports;
   both themes; and persistence after quitting and reopening. Check the other
   architecture on a matching Mac if available.
5. Edit the draft on GitHub and click **Publish release** when satisfied.

The workflow runs source checks and frozen-app checks against temporary data,
then verifies the app's ad-hoc signature. It attaches two ZIPs and their SHA-256
checksums only when both architectures pass. Failures stop draft creation.
The smoke checks cover startup, calendar creation, themes/chart rendering,
CSV persistence, categories/goals, credit card metadata, and CSV/Excel exports;
interactive edit/delete and month-comparison flows still need the manual check.

To build without creating a release, open **Actions → macOS release → Run
workflow**, select `main`, and download the build artifacts when it finishes.
A manual run does not create a GitHub release.

If Actions is disabled, enable it under **Settings → Actions → General**.
If repository or organization policy blocks release creation, allow the
workflow's `contents: write` permission or download the build artifacts and
attach the ZIPs/checksums to a draft release manually.

## Free local build

Install Python **3.12** using the macOS installer from python.org (which includes
Tcl/Tk), then run:

```bash
cd /Users/calvin/code/Finance_Dasboard
python3.12 -m venv .venv-macos
source .venv-macos/bin/activate
bash scripts/build_macos.sh
```

The script installs dependencies into the activated environment and writes
`dist/BudgetTracker.app` and `release/BudgetTracker-macOS-<architecture>.zip`.
It builds for the architecture of the running Python; use a native Python
installation on each architecture. GitHub runners use native Python too.
The app's minimum macOS version is set to the build machine's major version.
The preparation Mac is Intel with macOS 11.7.10: to run on that Mac, use this
local build with Python 3.12 instead of the macOS 15 hosted downloads. The local
build still must pass its GUI/export/signature checks before distribution;
older-system compatibility is not established merely by changing bundle metadata.
No paid signing account is needed. To publish locally built files, create a
new GitHub release tag and attach the ZIP and checksum. Use a tag outside the
`v*-macos*` pattern if you want to avoid triggering the hosted build workflow.

## Validation in the preparation workspace

The supplied workspace runs macOS 11.7.10 on Intel, with Python 3.7/3.8 and Tcl/Tk 8.5; package downloads
are blocked by its network environment. Syntax checks, icon-format checks,
and headless CSV persistence checks can run here, but the pinned Python 3.12
source/frozen GUI checks and native builds must run through the workflow or
on a Mac with the documented local environment. A successful release build
has not been claimed before those checks run.

The repository already tracks a Windows virtual environment and old build
outputs. They are retained to keep this change focused. Builds use a fresh
Python environment, and `.gitignore` excludes new generated files; ignoring
files does not remove files that were already tracked.
