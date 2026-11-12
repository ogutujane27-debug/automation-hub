import sqlite3
con = sqlite3.connect('db.sqlite3')
con.execute("delete from django_migrations where app='recurring_invoices'")
con.commit()
print("Migration history for recurring_invoices cleared.")
