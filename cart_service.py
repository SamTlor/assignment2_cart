import os, requests, json
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
basedir = os.path.abspath(os.path.dirname(__file__))



#product endpoint getters
def get_all_products():
    return requests.get('https://product-etg3.onrender.com/products').json()

def get_product(product_id):
    return requests.get(f'https://product-etg3.onrender.com/products/{product_id}').json()

def create_product(name):
    new_product = {"name": name}
    return requests.post('https://product-etg3.onrender.com/products', json=new_product).json()

def update_product(product_id, quantity):
    return requests.post(f'https://product-etg3.onrender.com/products/update/{product_id}', 
                         json = {"quantity" : quantity})







#start using flask and create a database to store products in
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'carts.sqlite')
db = SQLAlchemy(app)



# Describes the cart and what's in it
class Cart(db.Model):
    user_id = db.Column(db.Integer, primary_key = True)
    products = db.Column(db.String, nullable = False)   #products index = quantities index
    quantities = db.Column(db.String, nullable = False)

    #this is just for testing, i think
    def set_products(self, new_products):
        existing_products = [int(product) for product in self.products.split(', ')] if self.products else []
        existing_products.extend(new_products)
        
        quant_arr = []
        for i in existing_products:
            quant_arr.append(1)
            
        
        self.products = ', '.join(map(str, existing_products))
        self.quantities = ', '.join(map(str, quant_arr))
    


with app.app_context():
    db.create_all()
    
    cart1 = Cart()
    cart1.set_products([1,2])

    db.session.add(cart1)
    db.session.commit()






# Endpoint 1: Retrieve contents of user's cart
@app.route('/cart/<int:user_id>', methods=['GET'])
def get_cart(user_id):
    user_cart = Cart.query.get(user_id)
    if user_cart:
        cart_contents = []
        total_price = 0
        
        product_list = [int(prod_id) for prod_id in user_cart.products.split(', ')]
        quant_list = [int(quant) for quant in user_cart.quantities.split(', ')]
        for i, product_id in enumerate(product_list):
            product = get_product(product_id)
            cart_contents.append(product)
            
            total_price += product['task']['price'] * quant_list[i]
        
        return jsonify({
            "User Cart": cart_contents,
            "Total Price": total_price
        })
    else:
        return jsonify({"message": "Cart not found for user"}), 404

# Endpoint 2: add 'specified quantity' of a product to the cart
@app.route('/cart/<int:user_id>/add/<int:product_id>', methods=['POST'])
def add_to_cart(user_id, product_id):
    
    quantity = request.json.get('quantity', 1)     #from the json input from the body of the request
    user_cart = Cart.query.get(user_id)

    if user_cart:
        prods = [int(prod_id) for prod_id in user_cart.products.split(', ')]
        quants = [int(quant) for quant in user_cart.quantities.split(', ')]
        
        for index, prod_id in enumerate(prods):
            if product_id == prod_id and update_product(product_id, -quantity).status_code == 200:
                quants[index] += quantity
                user_cart.quantities = ', '.join(map(str, quants))
                db.session.commit()
                break
        else:
            user_cart.products = f"{user_cart.products}, {product_id}"
            user_cart.quantities = f"{user_cart.quantities}, {quantity}"
            db.session.commit()
                
    
        
    return jsonify({"message": f"Added {quantity} units of product {product_id} to user {user_id}'s cart"})
    

# Endpoint 3: remove 'specified quantity' of a product from the cart
@app.route('/cart/<int:user_id>/remove/<int:product_id>', methods=['POST'])
def remove_from_cart(user_id, product_id):
    
    quantity = request.json.get('quantity', 1)     #from the json input from the body of the request
    user_cart = Cart.query.get(user_id)

    if user_cart:
        prods = [int(prod_id) for prod_id in user_cart.products.split(', ')]
        quants = [int(quant) for quant in user_cart.quantities.split(', ')]
        
        for index, prod_id in enumerate(prods):
            if product_id == prod_id and update_product(product_id, quantity):
                quants[index] -= quantity
                user_cart.quantities = ', '.join(map(str, quants))
                db.session.commit()
                break
        else:
            return({"message": f"Error product {product_id} was not found"})
                
    
        
    return jsonify({"message": f"Removed {quantity} units of product {product_id} to user {user_id}'s cart"})
    
    

if __name__ == '__main__':
    app.run(debug=True, port = 5001)