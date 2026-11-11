import sqlite3, shutil, pathlib, datetime
root = pathlib.Path(__file__).resolve().parent
dest_base = pathlib.Path.home() / "Desktop" / "AUTO-12-Backups" / "daily"
stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
dest = dest_base / stamp
dest.mkdir(parents=True, exist_ok=True)

src = sqlite3.connect(str(root / "db.sqlite3"))
dst = sqlite3.connect(str(dest / "db.sqlite3"))
src.backup(dst)
dst.close(); src.close()

for name in (".env", "manage.py"):
    f = root / name
    if f.exists():
        shutil.copy2(f, dest / name)
for folder in ("recurring_invoices", "backend_core"):
    shutil.copytree(root / folder, dest / folder, ignore=shutil.ignore_patterns("__pycache__", "*.bak*"))
shutil.copytree(root / "frontend" / "src", dest / "frontend_src", ignore=shutil.ignore_patterns("*.bak*"))

folders = sorted([p for p in dest_base.iterdir() if p.is_dir()])
for old in folders[:-14]:
    shutil.rmtree(old, ignore_errors=True)
print("Backup saved to", dest)