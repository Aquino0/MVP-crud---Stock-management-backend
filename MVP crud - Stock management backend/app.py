from flask import Flask, request, jsonify, render_template
from flask_restx import Api, Resource, fields
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
cors=CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Configuração da API e documentação Swagger
api = Api(app, doc='/swagger')  # Define o endpoint da documentação Swagger

# Define o namespace para organizar as rotas
ns = api.namespace('products', description='Operations related to products')

# Define o modelo para o produto
product_model = api.model('Product', {
    'id': fields.String(required=True, description='The product id'),
    'name': fields.String(required=True, description='The product name'),
    'category': fields.String(required=True, description='The product category'),
    'price': fields.Float(required=True, description='The product price'),
    'quantity': fields.Integer(required=True, description='The product quantity')
})

DATABASE = 'products.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@ns.route('/')
class ProductList(Resource):
    @ns.doc('list_products')
    @ns.marshal_list_with(product_model)
    def get(self):
        """List all products"""
        conn = get_db_connection()
        products = conn.execute('SELECT * FROM products').fetchall()
        conn.close()
        return [dict(product) for product in products]

    @ns.doc('create_product')
    @ns.expect(product_model)
    @ns.response(201, 'Product created')
    def post(self):
        """Create a new product"""
        data = request.json
        name = data['name']
        category = data['category']
        price = data['price']
        quantity = data['quantity']
        conn = get_db_connection()
        conn.execute('INSERT INTO products (name, category, price, quantity) VALUES (?, ?, ?, ?)',
                     (name, category, price, quantity))
        conn.commit()
        conn.close()
        return '', 201

@ns.route('/<int:id>')
class Product(Resource):
    @ns.doc('get_product')
    @ns.marshal_with(product_model)
    def get(self, id):
        """Fetch a product by ID"""
        conn = get_db_connection()
        product = conn.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
        conn.close()
        if product is None:
            api.abort(404, "Product not found")
        return dict(product)

    @ns.doc('delete_product')
    @ns.response(204, 'Product deleted')
    def delete(self, id):
        """Delete a product by ID"""
        conn = get_db_connection()
        conn.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return '', 204

    @ns.doc('update_product')
    @ns.expect(product_model)
    @ns.response(204, 'Product updated')
    def put(self, id):
        """Update a product by ID"""
        data = request.json
        name = data['name']
        category = data['category']
        price = data['price']
        quantity = data['quantity']
        conn = get_db_connection()
        conn.execute('UPDATE products SET name = ?, category = ?, price = ?, quantity = ? WHERE id = ?',
                     (name, category, price, quantity, id))
        conn.commit()
        conn.close()
        return '', 204

@app.route('/home')
def home():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return render_template('index.html', products=products)

if __name__ == '__main__':
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL
    )
    ''')
    conn.close()
    app.run(debug=True)
