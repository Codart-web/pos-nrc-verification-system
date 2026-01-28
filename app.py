from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATABASE = 'pos_database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nrc TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            verified INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            total REAL NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        sample_products = [
            ('Rice (5kg)', 15000, 100, 'Groceries'),
            ('Cooking Oil (1L)', 8500, 50, 'Groceries'),
            ('Sugar (1kg)', 4500, 75, 'Groceries'),
            ('Salt (500g)', 1500, 100, 'Groceries'),
            ('Soap Bar', 2000, 60, 'Household'),
            ('Toothpaste', 3500, 40, 'Household'),
            ('Bottled Water (1L)', 1000, 200, 'Beverages'),
            ('Soft Drink', 1500, 150, 'Beverages'),
        ]
        cursor.executemany(
            'INSERT INTO products (name, price, stock, category) VALUES (?, ?, ?, ?)',
            sample_products
        )
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/pos')
def pos():
    conn = get_db()
    products = conn.execute('SELECT * FROM products WHERE stock > 0').fetchall()
    conn.close()
    return render_template('pos.html', products=products)

@app.route('/verify-nrc', methods=['POST'])
def verify_nrc():
    data = request.get_json()
    nrc = data.get('nrc', '').strip()
    
    if not nrc:
        return jsonify({'success': False, 'message': 'NRC number is required'})
    
    conn = get_db()
    customer = conn.execute('SELECT * FROM customers WHERE nrc = ?', (nrc,)).fetchone()
    
    if customer:
        conn.close()
        return jsonify({
            'success': True,
            'verified': True,
            'customer': {
                'id': customer['id'],
                'name': customer['name'],
                'nrc': customer['nrc'],
                'phone': customer['phone']
            }
        })
    else:
        conn.close()
        return jsonify({
            'success': True,
            'verified': False,
            'message': 'Customer not found. Please register.'
        })

@app.route('/register-customer', methods=['POST'])
def register_customer():
    data = request.get_json()
    nrc = data.get('nrc', '').strip()
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    address = data.get('address', '').strip()
    
    if not nrc or not name:
        return jsonify({'success': False, 'message': 'NRC and Name are required'})
    
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO customers (nrc, name, phone, address, verified) VALUES (?, ?, ?, ?, 1)',
            (nrc, name, phone, address)
        )
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return jsonify({
            'success': True,
            'customer': {
                'id': customer_id,
                'name': name,
                'nrc': nrc,
                'phone': phone
            }
        })
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Customer with this NRC already exists'})

@app.route('/process-sale', methods=['POST'])
def process_sale():
    data = request.get_json()
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    
    if not items:
        return jsonify({'success': False, 'message': 'No items in cart'})
    
    conn = get_db()
    cursor = conn.cursor()
    
    total = 0
    for item in items:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        if product and product['stock'] >= item['quantity']:
            total += product['price'] * item['quantity']
        else:
            conn.close()
            return jsonify({'success': False, 'message': f'Insufficient stock for {product["name"] if product else "product"}'})
    
    cursor.execute(
        'INSERT INTO transactions (customer_id, total) VALUES (?, ?)',
        (customer_id, total)
    )
    transaction_id = cursor.lastrowid
    
    for item in items:
        product = conn.execute('SELECT * FROM products WHERE id = ?', (item['product_id'],)).fetchone()
        cursor.execute(
            'INSERT INTO transaction_items (transaction_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            (transaction_id, item['product_id'], item['quantity'], product['price'])
        )
        cursor.execute(
            'UPDATE products SET stock = stock - ? WHERE id = ?',
            (item['quantity'], item['product_id'])
        )
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'transaction_id': transaction_id,
        'total': total
    })

@app.route('/customers')
def customers():
    conn = get_db()
    customers = conn.execute('SELECT * FROM customers ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('customers.html', customers=customers)

@app.route('/transactions')
def transactions():
    conn = get_db()
    transactions = conn.execute('''
        SELECT t.*, c.name as customer_name, c.nrc 
        FROM transactions t 
        LEFT JOIN customers c ON t.customer_id = c.id 
        ORDER BY t.transaction_date DESC
    ''').fetchall()
    conn.close()
    return render_template('transactions.html', transactions=transactions)

@app.route('/products')
def products():
    conn = get_db()
    products = conn.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    conn.close()
    return render_template('products.html', products=products)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
