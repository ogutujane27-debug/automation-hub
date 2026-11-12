import os
import hdbcli.dbapi


connection_args = {
    "address": os.environ["HANA_HOST"],
    "port": int(os.environ["HANA_PORT"]),
    "user": os.environ["HANA_USER"],
    "password": os.environ["HANA_PASSWORD"],
    "databaseName": os.environ["HANA_DATABASE"],
}


conn = None
cursor = None

try:
    print("Connecting to HANA...")
    print(f"Host: {connection_args['address']}")
    print(f"Port: {connection_args['port']}")
    print(f"Database: {connection_args['databaseName']}")
    print("")

    conn = hdbcli.dbapi.connect(**connection_args)

    print("HANA DATABASE CONNECTION: SUCCESS")
    print("")

    cursor = conn.cursor()

    cursor.execute(
        'SELECT COUNT(*) FROM "IAL01_DEV"."ODLN"'
    )

    row_count = cursor.fetchone()[0]

    print("Schema: IAL01_DEV")
    print("Table: ODLN")
    print("ODLN TABLE ACCESS: SUCCESS")
    print(f"ODLN rows: {row_count}")

    print("\n--- UKAGUZI WA 26101193 NDANI YA DEV ---")

    cursor.execute(
        'SELECT "DocEntry", "DocNum", "CardName", "U_Attachment" '
        'FROM "IAL01_DEV"."ODLN" '
        'WHERE "DocNum" = 26101193'
    )

    rows_dev = cursor.fetchall()

    print(f"Data zilizopo DEV: {rows_dev}")

    print("\n--- UKAGUZI WA 26101193 NDANI YA LIVE (UZALISHAJI) ---")

    try:
        cursor.execute(
            'SELECT "DocEntry", "DocNum", "CardName", "U_Attachment" '
            'FROM "IAL01_LIVE"."ODLN" '
            'WHERE "DocNum" = 26101193'
        )

        rows_live = cursor.fetchall()

        print(f"Data zilizopo LIVE: {rows_live}")

    except Exception as live_err:
        print(
            "[INFO] Haijaweza kusoma schema ya LIVE, "
            f"labda jina lake si IAL01_LIVE: {str(live_err)}"
        )

except Exception as exc:
    print("")
    print("HANA TEST FAILED:")
    print(repr(exc))

finally:
    if cursor:
        cursor.close()

    if conn:
        conn.close()
        print("")
        print("Connection closed.")

