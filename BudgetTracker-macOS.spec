# Build on macOS with Python 3.12 and requirements-build.txt.
import os
from PyInstaller.utils.hooks import collect_data_files

version = os.environ.get('BUDGETTRACKER_VERSION', '2.0.2').removeprefix('v')
a = Analysis(
    ['budget_track.py'],
    pathex=[], binaries=[],
    datas=collect_data_files('babel') + collect_data_files('tkcalendar'),
    hiddenimports=['babel.numbers', 'matplotlib.backends.backend_tkagg', 'openpyxl'],
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='BudgetTracker', console=False, debug=False,
    strip=False, upx=False, argv_emulation=False,
    target_arch=None, codesign_identity=None, entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='BudgetTracker')
app = BUNDLE(
    coll, name='BudgetTracker.app', icon='icon.icns',
    bundle_identifier='com.cgreenewald7.budgettracker',
    info_plist={
        'CFBundleShortVersionString': version,
        'CFBundleVersion': version,
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': os.environ.get('BUDGETTRACKER_MIN_MACOS', '15.0'),
        'NSDocumentsFolderUsageDescription': 'Budget Tracker saves your budget in Documents/BudgetTracker.',
    },
)
