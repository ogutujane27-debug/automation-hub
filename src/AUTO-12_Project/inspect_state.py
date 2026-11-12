import sqlite3, re
con = sqlite3.connect('file:db.sqlite3?mode=ro', uri=True)
cur = con.cursor()
print("== tables with row counts")
for (name,) in cur.execute("select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name").fetchall():
    n = cur.execute(f'select count(*) from "{name}"').fetchone()[0]
    print(f"  {name}: {n}")
print("\n== applied recurring_invoices migrations")
for row in cur.execute("select name, applied from django_migrations where app='recurring_invoices' order by id"):
    print("  ", row)
print("\n== models.py")
src = open('recurring_invoices/models.py', encoding='utf-8').read()
print("  chars:", len(src), " lines:", src.count('\n') + 1)
print("\n== migration 0007 operations")
m = open('recurring_invoices/migrations/0007_remove_auditlog_user_delete_emaillog_and_more.py', encoding='utf-8').read()
for line in m.splitlines():
    if 'migrations.' in line and 'import' not in line:
        print("  ", line.strip())
print("\n== database settings (backend_core)")
for line in open('backend_core/settings.py', encoding='utf-8'):
    if re.search(r"ENGINE|'NAME'|DATABASES", line):
        print("  ", line.strip())
