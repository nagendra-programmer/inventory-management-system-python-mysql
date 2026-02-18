import mysql.connector
import csv
import datetime

DB_CONFIG = {
    "host": "localhost",
    "user": "root",          # change if needed
    "password": "nagendra@developer",  # change this
    "database": "inventory_db"
}

LOW_STOCK_THRESHOLD = 5


# ---------- CONNECTION ----------
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ---------- INITIALIZE DATABASE ----------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        quantity INT NOT NULL CHECK (quantity >= 0),
        price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
        category VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


# ---------- ADD PRODUCT ----------
def add_product(name, quantity, price, category):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO products (name, quantity, price, category) VALUES (%s, %s, %s, %s)",
        (name.strip(), quantity, price, category.strip() if category else None)
    )
    conn.commit()
    conn.close()
    print(f"✅ Added product '{name}' successfully!")


# ---------- FETCH ALL ----------
def fetch_all_products(order_by="product_id"):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(f"SELECT * FROM products ORDER BY {order_by} ASC")
    rows = cur.fetchall()

    conn.close()
    return rows


# ---------- FIND BY ID ----------
def find_product_by_id(pid):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM products WHERE product_id = %s", (pid,))
    row = cur.fetchone()

    conn.close()
    return row


# ---------- SEARCH ----------
def search_products(keyword):
    pattern = f"%{keyword}%"
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM products WHERE name LIKE %s OR category LIKE %s ORDER BY name",
        (pattern, pattern)
    )
    rows = cur.fetchall()

    conn.close()
    return rows


# ---------- UPDATE ----------
def update_product(product_id, quantity=None, price=None, name=None, category=None):

    set_parts = []
    params = []

    if name is not None:
        set_parts.append("name = %s")
        params.append(name.strip())

    if quantity is not None:
        set_parts.append("quantity = %s")
        params.append(quantity)

    if price is not None:
        set_parts.append("price = %s")
        params.append(price)

    if category is not None:
        set_parts.append("category = %s")
        params.append(category.strip())

    if not set_parts:
        print("⚠️ No updates provided.")
        return

    params.append(product_id)

    sql = f"UPDATE products SET {', '.join(set_parts)} WHERE product_id = %s"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    conn.commit()

    if cur.rowcount:
        print("✅ Product updated successfully!")
    else:
        print("⚠️ Product not found.")

    conn.close()


# ---------- DELETE ----------
def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
    conn.commit()

    if cur.rowcount:
        print("🗑️ Product deleted.")
    else:
        print("⚠️ Product not found.")

    conn.close()


# ---------- LOW STOCK ----------
def low_stock_report(threshold=LOW_STOCK_THRESHOLD):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM products WHERE quantity < %s ORDER BY quantity ASC", (threshold,))
    rows = cur.fetchall()

    conn.close()

    if not rows:
        print("All products sufficiently stocked.")
    else:
        print_formatted_products(rows)

    return rows


# ---------- TOTAL VALUE ----------
def total_stock_value():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT SUM(quantity * price) AS total_value FROM products")
    val = cur.fetchone()["total_value"]
    val = val if val else 0

    print(f"💰 Total stock value = ₹{val:.2f}")
    conn.close()


# ---------- EXPORT ----------
def export_to_csv():
    rows = fetch_all_products()
    if not rows:
        print("No data to export.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_export_{ts}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "name", "quantity", "price", "category", "created_at"])

        for r in rows:
            writer.writerow([
                r["product_id"],
                r["name"],
                r["quantity"],
                r["price"],
                r["category"],
                r["created_at"]
            ])

    print(f"📤 Exported to {filename}")


# ---------- DISPLAY ----------
def print_formatted_products(rows):
    print(f"{'ID':<6}{'Name':<24}{'Qty':<8}{'Price':<10}{'Category':<14}")
    print("-" * 60)
    for r in rows:
        print(f"{r['product_id']:<6}{r['name'][:22]:<24}{r['quantity']:<8}₹{r['price']:<9}{(r['category'] or ''):<14}")


# ---------- MAIN ----------
def main():
    init_db()

    while True:
        print("\n===== INVENTORY MANAGEMENT SYSTEM =====")
        print("1. Add Product")
        print("2. View All Products")
        print("3. Search")
        print("4. Update")
        print("5. Delete")
        print("6. Low Stock")
        print("7. Total Value")
        print("8. Export CSV")
        print("9. Exit")

        choice = input("Choice: ")

        if choice == "1":
            name = input("Name: ")
            quantity = int(input("Quantity: "))
            price = float(input("Price: "))
            category = input("Category: ")
            add_product(name, quantity, price, category)

        elif choice == "2":
            print_formatted_products(fetch_all_products())

        elif choice == "3":
            keyword = input("Search: ")
            print_formatted_products(search_products(keyword))

        elif choice == "4":
            pid = int(input("Product ID: "))
            name = input("New name (blank skip): ") or None
            quantity = input("New quantity (blank skip): ")
            quantity = int(quantity) if quantity else None
            price = input("New price (blank skip): ")
            price = float(price) if price else None
            category = input("New category (blank skip): ") or None
            update_product(pid, quantity, price, name, category)

        elif choice == "5":
            pid = int(input("Product ID: "))
            delete_product(pid)

        elif choice == "6":
            low_stock_report()

        elif choice == "7":
            total_stock_value()

        elif choice == "8":
            export_to_csv()

        elif choice == "9":
            print("Goodbye 👋")
            break


if __name__ == "__main__":
    main()
