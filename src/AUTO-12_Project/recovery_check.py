import sqlite3, sys
cur = sqlite3.connect('file:db.sqlite3?mode=ro', uri=True)
old = sqlite3.connect('file:db.sqlite3.bak-before-emaillog?mode=ro', uri=True)
n = cur.execute("select count(*) from sqlite_master where name like 'recurring_invoices_%'").fetchone()[0]
if n:
    print("STOP: current database already has", n, "recurring_invoices tables."); sys.exit(1)
cu = dict(cur.execute("select id, username from auth_user"))
ou = dict(old.execute("select id, username from auth_user"))
bad = [(i, u) for i, u in ou.items() if cu.get(i) != u]
if bad:
    print("STOP: users differ between the two databases:", bad); sys.exit(1)
print("Users match:", ou)
for t in ('recurring_invoices_recurringinvoicetemplate', 'recurring_invoices_generatedinvoicelog', 'recurring_invoices_auditlog'):
    print(t, "in the 09:39 copy:", old.execute("select count(*) from " + t).fetchone()[0])
