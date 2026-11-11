import sqlite3, sys
con = sqlite3.connect('db.sqlite3')
con.execute("attach database 'db.sqlite3.bak-before-emaillog' as old")
tables = ['recurring_invoices_recurringinvoicetemplate', 'recurring_invoices_generatedinvoicelog', 'recurring_invoices_auditlog']
try:
    for t in tables:
        new_cols = [r[1] for r in con.execute(f'pragma main.table_info({t})')]
        old_cols = [r[1] for r in con.execute(f'pragma old.table_info({t})')]
        cols = [c for c in new_cols if c in old_cols]
        if set(new_cols) != set(old_cols):
            print("Note:", t, "columns differ:", set(new_cols) ^ set(old_cols))
        lst = ', '.join(cols)
        n = con.execute(f'insert into main.{t} ({lst}) select {lst} from old.{t}').rowcount
        print(f'{t}: copied {n} rows')
    con.commit()
except Exception as e:
    con.rollback()
    print("FAILED, nothing copied:", e); sys.exit(1)
print("Foreign key problems:", con.execute('pragma foreign_key_check').fetchall())
for t in tables:
    print(t, 'now has', con.execute(f'select count(*) from main.{t}').fetchone()[0], 'rows')
