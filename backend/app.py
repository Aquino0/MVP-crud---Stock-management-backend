import os
import sqlite3
from flask import Flask, request, redirect, url_for, render_template, send_from_directory
from flask_restx import Api, Resource, fields

# Configuração do Flask para usar o diretório de templates correto
app = Flask(__name__, template_folder='../frontend/templates')
api = Api(app, version='1.0', title='Menu API', description='A simple API for managing dishes and orders')

# Configurações dos diretórios
app.config['UPLOAD_FOLDER'] = 'static/images'  # Caminho para o diretório de imagens no backend
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads

DATABASE = 'dishes.db'
ORDERS_DATABASE = 'orders.db'

def get_db(db_name):
    conn = sqlite3.connect(db_name)
    return conn

def init_db():
    # Inicializa o banco de dados para pratos
    with get_db(DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS dishes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                image_path TEXT
            )
        ''')

    # Inicializa o banco de dados para pedidos
    with get_db(ORDERS_DATABASE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dish_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                table_number INTEGER
            )
        ''')

# Definições dos modelos para a documentação
dish_model = api.model('Dish', {
    'id': fields.Integer(readonly=True, description='The unique identifier of a dish'),
    'name': fields.String(required=True, description='The name of the dish'),
    'category': fields.String(required=True, description='The category of the dish'),
    'price': fields.Float(required=True, description='The price of the dish'),
    'image_path': fields.String(description='The path to the image of the dish')
})

order_model = api.model('Order', {
    'id': fields.Integer(readonly=True, description='The unique identifier of an order'),
    'dish_name': fields.String(required=True, description='The name of the dish ordered'),
    'quantity': fields.Integer(required=True, description='The quantity of the dish ordered'),
    'table_number': fields.Integer(description='The table number for the order')
})

@api.route('/dishes')
class DishList(Resource):
    @api.doc('list_dishes')
    @api.marshal_list_with(dish_model)
    def get(self):
        """List all dishes"""
        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dishes")
            dishes = cursor.fetchall()
        return dishes

    @api.doc('create_dish')
    @api.expect(dish_model)
    def post(self):
        """Create a new dish"""
        data = api.payload
        name = data['name']
        category = data['category']
        price = data['price']
        image_path = data.get('image_path', None)

        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dishes (name, category, price, image_path) VALUES (?, ?, ?, ?)",
                           (name, category, price, image_path))
            conn.commit()
        return {'message': 'Dish created'}, 201

@api.route('/dishes/<int:id>')
@api.response(404, 'Dish not found')
@api.param('id', 'The dish identifier')
class Dish(Resource):
    @api.doc('get_dish')
    @api.marshal_with(dish_model)
    def get(self, id):
        """Fetch a single dish"""
        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM dishes WHERE id = ?", (id,))
            dish = cursor.fetchone()
        if dish:
            return dish
        return {'message': 'Dish not found'}, 404

    @api.doc('update_dish')
    @api.expect(dish_model)
    def put(self, id):
        """Update a dish"""
        data = api.payload
        name = data['name']
        category = data['category']
        price = data['price']
        image_path = data.get('image_path', None)

        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE dishes SET name = ?, category = ?, price = ?, image_path = ?
                WHERE id = ?
            ''', (name, category, price, image_path, id))
            conn.commit()
        return {'message': 'Dish updated'}

    @api.doc('delete_dish')
    def delete(self, id):
        """Delete a dish"""
        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM dishes WHERE id = ?", (id,))
            conn.commit()
        return {'message': 'Dish deleted'}

@api.route('/orders')
class OrderList(Resource):
    @api.doc('list_orders')
    @api.marshal_list_with(order_model)
    def get(self):
        """List all orders"""
        with get_db(ORDERS_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders")
            orders = cursor.fetchall()
        return orders

    @api.doc('create_order')
    @api.expect(order_model)
    def post(self):
        """Create a new order"""
        data = api.payload
        dish_name = data['dish_name']
        quantity = data['quantity']
        table_number = data.get('table_number', None)

        with get_db(ORDERS_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO orders (dish_name, quantity, table_number) VALUES (?, ?, ?)",
                           (dish_name, quantity, table_number))
            conn.commit()
        return {'message': 'Order created'}, 201

@api.route('/orders/<int:id>')
@api.response(404, 'Order not found')
@api.param('id', 'The order identifier')
class Order(Resource):
    @api.doc('get_order')
    @api.marshal_with(order_model)
    def get(self, id):
        """Fetch a single order"""
        with get_db(ORDERS_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM orders WHERE id = ?", (id,))
            order = cursor.fetchone()
        if order:
            return order
        return {'message': 'Order not found'}, 404

    @api.doc('delete_order')
    def delete(self, id):
        """Delete an order"""
        with get_db(ORDERS_DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM orders WHERE id = ?", (id,))
            conn.commit()
        return {'message': 'Order deleted'}

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/create_dish', methods=['GET', 'POST'])
def create_dish():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        image = request.files.get('image')

        image_path = None
        if image:
            image_filename = image.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            # Salva a imagem no diretório correto
            image.save(image_path)

        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO dishes (name, category, price, image_path) VALUES (?, ?, ?, ?)",
                           (name, category, price, image_path))
            conn.commit()
        
        return redirect(url_for('management_menu'))

    return render_template('create_dish.html')

@app.route('/management_menu')
def management_menu():
    with get_db(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dishes")
        dishes = cursor.fetchall()
    return render_template('management_menu.html', dishes=dishes)

@app.route('/change_dish/<int:id>', methods=['GET', 'POST'])
def change_dish(id):
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        price = request.form['price']
        image = request.files.get('image')

        image_path = None
        if image:
            image_filename = image.filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
            image.save(image_path)

        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE dishes SET name = ?, category = ?, price = ?, image_path = ?
                WHERE id = ?
            ''', (name, category, price, image_path, id))
            conn.commit()

        return redirect(url_for('management_menu'))

    with get_db(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dishes WHERE id = ?", (id,))
        dish = cursor.fetchone()
    
    return render_template('change_dish.html', dish=dish)

@app.route('/delete_dish/<int:id>', methods=['POST'])
def delete_dish(id):
    with get_db(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM dishes WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for('management_menu'))

@app.route('/order_management')
def order_management():
    with get_db(ORDERS_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT dish_name, quantity, table_number FROM orders")
        orders = cursor.fetchall()
    return render_template('order_management.html', orders=orders)

@app.route('/delete_order/<int:id>', methods=['POST'])
def delete_order(id):
    with get_db(ORDERS_DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for('order_management'))

@app.route('/view_menu', methods=['GET', 'POST'])
def view_menu():
    category_filter = request.form.get('category', '')
    table_number = request.form.get('table_number', None)
    
    with get_db(DATABASE) as conn:
        cursor = conn.cursor()
        if category_filter:
            cursor.execute("SELECT * FROM dishes WHERE category LIKE ?", ('%' + category_filter + '%',))
        else:
            cursor.execute("SELECT * FROM dishes")
        dishes = cursor.fetchall()

    if request.method == 'POST' and 'order' in request.form:
        dish_id = request.form['dish_id']
        quantity = request.form['quantity']
        
        with get_db(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM dishes WHERE id = ?", (dish_id,))
            dish_name = cursor.fetchone()[0]

        if table_number:  # Verifica se o número da mesa foi fornecido
            with get_db(ORDERS_DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO orders (dish_name, quantity, table_number) VALUES (?, ?, ?)", 
                               (dish_name, quantity, table_number))
                conn.commit()

    return render_template('view_menu.html', dishes=dishes)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
