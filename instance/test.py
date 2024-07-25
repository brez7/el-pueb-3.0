import sqlite3

connection = sqlite3.connect("catering.db")
cursor = connection.cursor()

# Retrieve orders
cursor.execute('SELECT * FROM "Order";')
orders = cursor.fetchall()
print("Orders:", orders)

# Retrieve items
cursor.execute("SELECT * FROM Item;")
items = cursor.fetchall()
print("Items:", items)

connection.close()
