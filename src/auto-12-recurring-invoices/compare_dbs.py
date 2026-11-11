import sqlite3, json, datetime
from pathlib import Path
from collections import Counter

bk = Path.home() / 'Desktop' / 'AUTO-12-Backups' / '2026-11-10_0902'
files = {
    'CURRENT db.sqlite3': Path('db.sqlite3'),
    'backup 09:02 db': bk / 'project' / 'db.sqlite3',
    'db.sqlite3.bak-before-emaillog': Path('db.sqlite3.bak-before-emaillog'),
}

def q(cur, sql):
    try:
        return cur.execute(sql).fetchall()
    except Exception as e:
        return '(n/a: %s)' % e

for label, p in files.items():
    mod = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
    print("\n=== %s (%d bytes, modified %s)" % (label, p.stat().st_size, mod))
    con = sqlite3.connect(p.resolve().as_uri() + '?mode=ro', uri=True)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("select name from sqlite_master where type='table' and name like 'recurring_invoices_%' order by name")]
    if not tables:
        print("  no recurring_invoices tables")
    for t in tables:
        n = cur.execute('select count(*) from ' + t).fetchone()[0]
        print("  %s: %d rows" % (t, n))
    print("  users:", q(cur, "select count(*) from auth_user"))
    print("  last migration:", q(cur, "select name from django_migrations where app='recurring_invoices' order by id desc limit 1"))
    print("  latest audit entry (UTC):", q(cur, "select max(timestamp) from recurring_invoices_auditlog"))
    print("  invoices (id, status):", q(cur, "select id, status from recurring_invoices_generatedinvoicelog order by id"))
    con.close()

print("\n=== data.json in the 09:02 backup")
data = json.load(open(bk / 'data.json', encoding='utf-8'))
for m, n in sorted(Counter(r['model'] for r in data).items()):
    print("  %s: %d" % (m, n))
