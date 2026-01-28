# POS NRC Verification System

## Overview
A Point of Sale (POS) system with National Registration Card (NRC) verification for secure customer identity verification before processing transactions. This is an academic final year project demonstrating requirements engineering, system design, and software architecture concepts.

## Technologies
- **Backend**: Python 3.11, Flask
- **Database**: SQLite (local file: pos_database.db)
- **Frontend**: HTML, CSS, JavaScript (Jinja2 templates)

## Project Structure
```
/
├── app.py              # Main Flask application
├── pos_database.db     # SQLite database (auto-created)
├── templates/          # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── index.html      # Homepage
│   ├── pos.html        # Point of sale interface
│   ├── customers.html  # Customer list
│   ├── products.html   # Product list
│   └── transactions.html # Transaction history
├── static/
│   ├── style.css       # Styles
│   └── script.js       # JavaScript utilities
└── README.md           # Project description
```

## Running the Application
The Flask server runs on port 5000:
```bash
python app.py
```

## Features
1. **NRC Verification**: Verify customer identity using NRC numbers
2. **Customer Registration**: Register new customers with NRC, name, phone, address
3. **Product Management**: View products with prices and stock levels
4. **POS Interface**: Add products to cart, process sales
5. **Transaction History**: View all completed transactions

## Database Schema
- **customers**: id, nrc, name, phone, address, verified, created_at
- **products**: id, name, price, stock, category
- **transactions**: id, customer_id, total, transaction_date
- **transaction_items**: id, transaction_id, product_id, quantity, price

## Recent Changes
- Initial setup with Flask application (Jan 28, 2026)
- Created all templates and static files
- Database auto-initializes with sample products
