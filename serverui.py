import socket 
import sqlite3   ##count for data base of sellers when client buy count =0
import threading
from datetime import datetime,timedelta
import json
import hashlib
import time
import os
import base64
import requests

Connections = {}
UserToSocket = {}
user_data = {}
stop_reply = False # to fix a certain problem with add function


message_list = "\nYour messages:\n"

def create_socket():
    '''creates socket for client to bind'''
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind(('localhost', 1235))
    server.listen(5)
    print("Server is listening...")
    return server
    
    
def create_database():
    '''creating necessary database'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS userInfo(
                            email text, 
                            password text, 
                            username text, 
                            name text,
                            points INTEGER DEFAULT 0,
                            status INTEGER Default 0)
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS objForSell(
                            name_of_product text, 
                            username text,
                            price REAL,
                            description TEXT,
                            image_path TEXT, 
                            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            quantity INTEGER,
                            total_rating FLOAT DEFAULT 0 NOT NULL,
                            number_of_ratings INTEGER DEFAULT 0)
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS log(
                            buyer text, 
                            product text, 
                            product_id text,
                            seller text,
                            quantity_bought INTEGER,
                            price FLOAT, 
                            image_path TEXT, 
                            description TEXT)
                       ''')
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS bumped_listings(
                            product_id INTEGER,
                            bump_expiry TIMESTAMP,
                            PRIMARY KEY (product_id))
                        ''')
        # cursor.execute('''
        #                CREATE TABLE IF NOT EXISTS messages(
        #                    from_user TEXT,
        #                    to_user TEXT,
        #                    message TEXT,
        #                    delivered INTEGER DEFAULT 0)
        #                ''')
        # cursor.execute('''
        #                CREATE TABLE IF NOT EXISTS productRatings(
        #                    product_id INTEGER PRIMARY KEY,
        #                    total_rating FLOAT DEFAULT 0 NOT NULL,
        #                    number_of_ratings INTEGER)
        #                ''')
        
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS followers(
                           follower_username TEXT,
                           followed_username TEXT)
                       ''')
        conn.commit()


def handle_client_log_reg(client_socket):
    '''handles process of registration and logging in'''
    while True :
        req = client_socket.recv(1024).decode()
        req = json.loads(req)
        action = req["action"]
        if action=="login":
            if handle_client_log(client_socket, req["user"], req["password"]):
                break
        elif action=="reg":
            handle_client_reg(client_socket, req["name"], req["mail"], req["username"], req["password"])
                
            
       
                
                
def handle_client_reg(client_socket,name, mail, username, hashed_password):
    '''handles reg'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()

        if user_exists(username):
            reply = {"action" : "reg", "completed" : False, "msg" : "Username already exists, please try a different username, or log in with your account."}
            send_reply(client_socket, reply)
        else:
            try :
                cursor.execute("INSERT INTO userInfo (name, email, username, password) VALUES (?, ?, ?, ?)", (name, mail, username, hashed_password))
                conn.commit()
                # print(f""" after reg added to db: {name} 
                #       {mail} 
                #       {username} 
                #       {hashed_password}""")
                reply = {"action" : "reg", "completed" : True, "msg" : "Account created. Please log in with your new account."}
                # print("reg success")
            except sqlite3.IntegrityError:
                reply = {"action" : "reg", "completed" : False, "msg" : "An error occured. Please try again"}
            finally:
                send_reply(client_socket, reply)


def handle_client_log(client_socket, username, hashed_password):
    '''handles login'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        # print("login entries")
        # print(f"username: {username}")
        # print(f"password: {hashed_password}") 
        cursor.execute("SELECT * FROM userInfo WHERE username=? AND password=?",(username, hashed_password)) #checks if user pass pair exists
        user = cursor.fetchone()
        if not check_if_online(username): #if user isnt logged in in another place
            if user: #if user,pass exists in database

                # set his status to online by putting user, socket in dictionary
                Connections[client_socket] = username
                UserToSocket[username] = client_socket
                cursor.execute("UPDATE userInfo SET status = ? WHERE username=?",(1, username))
                reply = {"action" : "login", "completed" : True, "msg" : "Login Successfull!"}
                send_reply(client_socket, reply)
                
                return True
            else :
                reply = {"action" : "login", "completed" : False, "msg" : "Invalid username or password, please try again or register!"}
        else:
            reply = {"action" : "login", "completed" : False, "msg" : " User logged in elsewhere!"}
        send_reply(client_socket, reply)
        return False

 
        
        
def hash_password(password): 
    '''takes care of encryption'''
    hash_object = hashlib.sha256() 
    hash_object.update(password.encode('utf-8')) 
    return hash_object.hexdigest()



        
def check_if_online(username): 
    '''checks if user is online'''

    return username in UserToSocket
    
    
def user_exists(user):
    '''checks if user has an account'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM userInfo WHERE username=?", (user,))
        return cursor.fetchone() is not None




def send_reply(client_socket, reply):
    '''takes care of communicating with client using json'''
    global stop_reply
    if not stop_reply:
        print("servers reply", reply)
        
        reply = json.dumps(reply) + "\n"
        client_socket.send(reply.encode())


'''Adding And Buying'''

def add_product_to_marketplace(client_socket, name, price, desc, image_base64, quantity):
    '''adds product to database'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        username = Connections[client_socket]
        try:  
            # Decode the image
            image_data = base64.b64decode(image_base64)
            
            # Save the image to a file
            image_dir = "product_images"
            os.makedirs(image_dir, exist_ok=True)
            image_path = os.path.join(image_dir, f"{name}_{Connections[client_socket]}.png")  # Unique filename
            
            with open(image_path, "wb") as image_file: #write binary
                image_file.write(image_data)
        
            cursor.execute("INSERT INTO objForSell(name_of_product,username,price,description,image_path, quantity)VALUES(?,?,?,?,?,?)",(name, username, price, desc, image_path, quantity))
            conn.commit()
            message="Product added successfully"
            
            #to notify followers of the added product
            cursor.execute("SELECT follower_username FROM followers WHERE followed_username = ?", (username,))
            followers = cursor.fetchall()
            for follower in followers :
                follower_socket = UserToSocket.get(follower)
                if follower_socket :
                    notification = {"action" : "message", "message" : f"{username} added a new product : {name}."}
                    send_reply(follower_socket, notification)
                    
        except Exception as e:
            message = "Product could not be added please try again later!", e
        finally:
            reply={"action":"add","message": message}
            send_reply(client_socket, reply)
        
        
def buy_product(client_socket, product_id, quantity_bought):
    '''manipulates databses for buying process'''
    with sqlite3.connect("AUBoutique.db") as conn:
        try:

            cursor = conn.cursor()
            cursor.execute("SELECT name_of_product, username, price, quantity, image_path, description FROM objForSell WHERE product_id=?", (product_id,))
            product=cursor.fetchone()
            if product :
                name_of_product, seller, price, quantity_available, image, description = product[0], product[1], product[2], product[3], product[4], product[5]
                quantity_remaining = quantity_available - quantity_bought
                buyer = Connections[client_socket] 
                
                update_objForSell_after_buying(client_socket, quantity_remaining, product_id)
                update_log_after_buying(client_socket, name_of_product, buyer, seller, quantity_bought, product_id, price, image, description)
                
                collection_date=(datetime.now()+timedelta(days=7)).strftime("%Y-%m-%d")
                confirmation_message=f"Purchase confirmed! Please collect '{name_of_product}' from the AUB Post Office on { collection_date}."
                
                #add points to users profile which can be used as discounts
                points_message = add_pts_after_buying(client_socket, product[2])
                reply={"action":"buy","message": confirmation_message + " " + points_message, "points" : price//10} #
               
                send_reply(client_socket, reply)
        except sqlite3.Error as e:
            print(f"An error occurred in buy_product: {e}")
            


def view_buyer(client_socket) :
    '''view buyers of a client's products'''
    # try:
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        seller = Connections.get(client_socket)
        
        cursor.execute("SELECT buyer, product, product_id, quantity_bought, price FROM log WHERE seller = ?", (seller,))
        purchase = cursor.fetchall()           
        if purchase:
            purchase_list = []
            for buyer, product, product_id, quantity_bought, price in purchase:
                purchase_list.append({"buyer" : buyer, "product" : product, "ID" : product_id, "quantity_bought" : quantity_bought, "price": price})

        else:
            purchase_list = []
        return purchase_list
        
    # except sqlite3.Error as e:
    #     print(f"SQLite error: {e}")
    #     message = "An error occurred while accessing purchase data."
    #     reply = {"action" : "message", "message" : message}
    #     send_reply(client_socket, reply)
    # except Exception as e:
    #     print(f"General error: {e}")  
    #     message = "An unexpected error occurred."
    #     reply = reply = {"action" : "message", "message" : message}
    #     send_reply(client_socket, reply)


'''Displaying Items'''
def display_products_of_user(client_socket, user, username_is_client = False):
    '''displays sellables of a specific user'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()

        if user_exists(user):
            cursor.execute("SELECT * FROM objForSell WHERE username=?", (user,))
            products = cursor.fetchall()

            if products: #fetch the product list in appropriate format
                product_list = product_display_format(products)[0]
            else:
                product_list = {}
                
            if username_is_client: #if username is requesting to update his products for sale
                return product_list
            
            else: #if user is requesting to see a users products
                reply = {"action" : "display_user", "username" : user ,"content" : product_list}
                send_reply(client_socket, reply)
        else:
            send_reply(client_socket, {"action" : "message", "message" : "Username not found!"})
        

    
    
def display_matching_products(client_socket, search_term):
    '''displays item that closely match the serach term'''
    if len(search_term)==0: 
        display_all_objects(client_socket)
    else:
        with sqlite3.connect("AUBoutique.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM objForSell WHERE name_of_product LIKE ?", ('%' + search_term + '%',))
            products = cursor.fetchall()
            if products:
                product_list, product_ids = product_display_format(products)
                reply = {"action" : "show_matching", "content" : product_list, "IDs" : product_ids} #sends a list of matching prods
            else:
                product_list = []
                reply = {"action" : "show_matching", "content" : product_list}
            send_reply(client_socket, reply)

        
    
def display_all_objects(client_socket, on_start_up=False):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        # First get bumped items that haven't expired
        cursor.execute("""
            SELECT o.* FROM objForSell o
            LEFT JOIN bumped_listings b ON o.product_id = b.product_id
            WHERE b.bump_expiry > CURRENT_TIMESTAMP OR b.bump_expiry IS NULL
            ORDER BY 
                CASE 
                    WHEN b.bump_expiry > CURRENT_TIMESTAMP THEN 0 
                    ELSE 1 
                END,
                o.product_id DESC
        """)
        products = cursor.fetchall()
        if products:
            product_list = product_display_format(products)[0]
        else:
            product_list = []
        if on_start_up:
            return product_list
        reply = {"action" : "show_matching", "content" : product_list}
        send_reply(client_socket, reply)
        

def display_products_bought_by_user(client_socket, on_start = False):
    '''displays sellables of a specific user'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        user = Connections[client_socket]
   
        cursor.execute("SELECT * FROM log WHERE buyer=?", (user,))
        products = cursor.fetchall()
        purchase_list = []
        if products:
            for buyer, product, product_id, seller, quantity_bought, price, image, description in products:
                purchase_list.append({"seller" : seller, "item" : product, "ID" : product_id, "quantity_bought" : quantity_bought, "price": price, "image" : image, "description" : description})

        if on_start:
            return purchase_list
        else:
            send_reply(client_socket, {"action" : "your_bought_products", "content" : purchase_list})




def relay_msg(client_socket, from_user, to_user, message):
    '''adds messages to database'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        if user_exists(to_user):
            if check_if_online(to_user):
                cursor.execute("INSERT INTO messages(from_user, to_user, message, delivered)VALUES(?,?,?,0)", (from_user, to_user, message))
                msg = f"Message sent to {to_user} successfully."
                send_reply(UserToSocket[to_user], {"action" : "new_message"})
            else:
                msg = f"{to_user} is not online, message could not be sent."
        else:
            msg = "User does not exist please make sure you spelled it correctly."
        reply = {"action" : "message", "message" : msg}
        send_reply(client_socket, reply)
            
            
def get_undelivered_messages(client_socket):
    '''Send unread messages to user'''
    global message_list
    username = Connections[client_socket]
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT from_user, message FROM messages WHERE to_user=? AND delivered=0", (username,))
        messages = cursor.fetchall()
        if messages:
            for msg in messages:
                message_list += f"From: {msg[0]}, Message: {msg[1]}\n\n"
            cursor.execute("UPDATE messages SET delivered=1 WHERE to_user=?", (username,))
            conn.commit()
            reply = {"action": "get_msgs", "new" : True, "content": message_list}
            message_list = "\nYour messages:\n"
        else:
            message_list = "No new messages."
            reply = {"action": "message", "message": message_list}
        send_reply(client_socket, reply)     
        
        
def rate_product(client_socket, product_id, rating):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        if check_if_bought_product(client_socket, product_id):
            try:
                cursor.execute("UPDATE objForSell SET total_rating = total_rating + ?, number_of_ratings = number_of_ratings + ? WHERE product_id = ?", (rating, 1, product_id))
                reply = {"action" : "message", "message" : "Successfully rated product!"}
            except:
                reply = {"action" : "message", "message" : "An error occured could not rate product!"}
            finally:
                send_reply(client_socket, reply)
        else:
            reply = {"action" : "message", "message" : "You can not rate a product you have not bought yet!"}
            send_reply(client_socket, reply)
            
            
def add_pts_after_buying(client_socket, price):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        points = price//10
        try:
            cursor.execute("UPDATE userinfo SET points = points + ? WHERE username = ?", (points, Connections[client_socket]))
            message = f" {int(points)} BlissPoints have been added to your balance!"
        except sqlite3.Error:
            message = "AUBPoints could not be added!"
        finally:
            return message
          
        

def get_P2P_info(client_socket, username):
    if username in user_data: #IF Target online
        target_ip, target_port = user_data[username]["ip"], (user_data[username])["port"]
    else: 
        target_ip, target_port = "offline", "offline"
    send_reply(client_socket, {"action" : "p2p_info", "ip" : target_ip, "port" : target_port})
    print(target_ip, "sent t_ip", target_port, 'sent port')


def p2p_req(client_socket, username):
    '''send request for p2p with recieving user'''
    if username in UserToSocket:
        target_socket = UserToSocket[username]
        requesting_user = Connections[client_socket]
        send_reply(target_socket, {
            "action": "p2p_req", 
            "from_user": Connections[client_socket],
            "init_ip": user_data[requesting_user]["ip"], 
            "init_port": user_data[requesting_user]["port"] # send to the reciever the ip and port of requester
        })
    else:
        send_reply(client_socket, {"action": "error", "message": "User not online."})       


def fetch_all_users(client_socket):
    '''Fetch all users except the current user from the database and send them to the client'''
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        current_user = Connections.get(client_socket)  # Get the current user's username
        print(f"Current user requesting users list: {current_user}")  # Debug
        cursor.execute("SELECT username, status FROM userInfo WHERE username != ?", (current_user,))
        users = cursor.fetchall()
        if users:
            user_list  = []
            for user, status in users:
                user_list += [(user, status)]  # add to the list a list [username, status]
                
                
            reply = {"action": "show_users", "users": user_list}
        else:
            reply = {"action": "show_users", "users": []}
        send_reply(client_socket, reply)   
        
        
def unfollow_user(client_socket, unfollowed_username) :
    follower_username = Connections.get(client_socket)
    with sqlite3.connect("AUBoutique.db") as conn :
        cursor = conn.cursor()
        try :
            cursor.execute(
                "DELETE FROM followers WHERE follower_username = ? AND followed_username = ?",
                (follower_username, unfollowed_username)
                )
            conn.commit()
            print(f"User '{follower_username}' unfollowed '{unfollowed_username}'.")  # Debugging
            reply = {"action": "message", "status": "success", "message": f"You have unfollowed {unfollowed_username}. You will no longer recieve updates from this user."}
        except sqlite3.Error as e:
            print(f"Database error during unfollow: {e}")
            reply = {"action": "message", "status": "error", "message": "Could not unfollow. Please try again."}
        send_reply(client_socket, reply)   
        
        
def add_follower_to_database(client_socket, followed_username): 
    """Adds a follow relationship to the database."""
    try:
        follower = Connections[client_socket]
        with sqlite3.connect("AUBoutique.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO followers (follower_username, followed_username) VALUES (?, ?)",
                (follower, followed_username))
            conn.commit()
            reply = {"action": "message", "message": f"You have followed {followed_username}. You will now recieve updates from this user."}
            send_reply(client_socket, reply)
        print(f"Added follow relationship: {follower} -> {followed_username}")
    except sqlite3.Error as e:
        print(f"Database error while adding follow relationship: {e}")
        
        
def handle_client_currency_change(client_socket, selected_currency):
    """Fetch and convert product prices to the selected currency."""
    price_multiplier = convert_currency("USD", selected_currency, 1)  # Assuming DB prices are in USD
    reply = {
        "action": "change_currency",
        "multiplier": price_multiplier
    }
    send_reply(client_socket, reply)

def convert_currency(from_currency, to_currency, amount):
    """Use the CurrencyBeacon API to convert currencies."""
    url = "https://api.currencybeacon.com/v1/convert"
    api_key = "xkULjLTYThztpAPpk7qdH7P4gMrw8bBf"
    params = {
        "from": from_currency,
        "to": to_currency,
        "amount": amount,
        "api_key": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["response"]["value"]
    else:
        print(f"Currency conversion error: {response.status_code}, {response.text}")
        return amount  # Fallback to the original amount
        
    
def bump_listing(client_socket, product_id):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        # Check if user has enough points
        username = Connections[client_socket]
        cursor.execute("SELECT points FROM userInfo WHERE username = ?", (username,))
        current_points = cursor.fetchone()[0]
        
        if current_points >= 200:
            # Deduct points
            cursor.execute("UPDATE userInfo SET points = points - 200 WHERE username = ?", (username,))
            
            # Add bump record (expires in 24 hours)
            bump_expiry = datetime.now() + timedelta(hours=24)
            cursor.execute("REPLACE INTO bumped_listings (product_id, bump_expiry) VALUES (?, ?)",
                         (product_id, bump_expiry))
            
            conn.commit()
            reply = {"action": "message", "message": "Listing bumped successfully!"}
        else:
            
            reply = {"action": "message", "message": "Not enough points to bump listing."}
        
        send_reply(client_socket, reply)
#HELPER FUNCTIONS

        
        
def handle_send(client_socket, request):
    '''handles sending msgs to other users'''
    from_user = Connections[client_socket]
    recipient = request["to_user"]
    message = request["message"]
    if recipient == from_user:
        reply = {"action" : "message", "message" : "Cannot send messages to yourself."}
        send_reply(client_socket, reply)
    else:
        relay_msg(client_socket, from_user, recipient, message)

            
     
def handle_check(client_socket, user):
    '''checks online status of user'''
    if user_exists(user):
        if check_if_online(user):
            msg = f"{user} is online."
        else:
            msg =f"{user} is not online."
    else:
        msg ="User does not exist please make sure you spelled it correctly."
    reply = {"action" : "message" , "message" : msg}
    send_reply(client_socket, reply)
    
    
def handle_log_out(client_socket, username):
    '''logs user out'''
    try:
        Connections.pop(client_socket, None)
        UserToSocket.pop(username, None)
        user_data.pop(username, None)
        print("conncections: ", Connections)
        print("usertosocke: ",UserToSocket)
        print("user_data: ",user_data)
        print()
        
        with sqlite3.connect("AUBoutique.db") as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE userInfo SET status = 0 WHERE username = ?", (username,))
            conn.commit()
        
    except Exception as e:
        print(f"error {e} in logout")
    finally:
        client_socket.close() 
    
    
def check_if_bought_product(client_socket, product_id):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM log WHERE buyer = ? AND product_id = ?", (Connections[client_socket], product_id))
        result = cursor.fetchone()
        return result is not None
    

def check_if_client_rated_product(client_socket, product_id):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        username_buyer = Connections[client_socket]
        cursor.execute("SELECT * FROM log WHERE buyer = ? AND product_id = ? AND rated = ?", (username_buyer, product_id, 1)) # check ifuser already rated this product
        result = cursor.fetchone()
        return result is not None
    
    
def update_log_after_buying(client_socket, name_of_product, buyer, seller, quantity_bought, product_id, price, image, description):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        if check_if_bought_product(client_socket, product_id):
            cursor.execute('''UPDATE log SET quantity_bought = quantity_bought + ? 
                           WHERE product_id = ? AND buyer = ?''',
                           (quantity_bought, product_id, Connections[client_socket]))
        else:
            cursor.execute("INSERT INTO log(buyer, product, product_id, seller, quantity_bought, price, image_path, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (buyer, name_of_product, product_id, seller, quantity_bought, price, image, description))
        conn.commit()
    
    
def update_objForSell_after_buying(client_socket, quantity_remaining, product_id):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        if not quantity_remaining:
            cursor.execute("DELETE FROM objForSell WHERE product_id=?",(product_id,))
        else:
            cursor.execute("UPDATE objForSell SET quantity = ? WHERE product_id=?",(quantity_remaining, product_id))
        conn.commit()
     
    
def product_display_format(products):
    """create a list of dictionary items where each item corresponds to a certain product"""
    product_list = []
    product_ids = []
    for x in products:
        if x[7] == 0: 
            rating = "unrated"
            
        else: 
            print(x[7], x[8])
            rating = x[7]/x[8]
            rating = round(rating,1)
        product = {
                    "item" :  x[0],
                    "owner" : x[1],
                    "price" : x[2],
                    "quantity" : x[6],
                    "description" : x[3],
                    "image_path" : x[4],
                    "ID" : x[5],
                    "rating" : rating
                    }
        product_list.append(product)
        
        product_ids.append( (str(x[5]), int(x[6])) )
    return (product_list, product_ids)

def get_user_points(client_socket):
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT points FROM userInfo WHERE username = ?", (Connections[client_socket],))
        points = cursor.fetchall()[0][0]
        print(points)
    return points


def send_user_data(client_socket):
    """handles sending to the user his products for sale, following list, etc... upon log in"""
    with sqlite3.connect("AUBoutique.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT followed_username FROM followers WHERE follower_username = ?", (Connections[client_socket],))
        following = cursor.fetchall()
        following_dict = {}
        if following:
            for (user,) in following: #dictionary of form {user:1} to indicate that user is followed by our client
                following_dict[user] = 1
        all_prod = display_all_objects(client_socket, on_start_up = True)
        prod_for_sale = display_products_of_user(client_socket, Connections[client_socket], True)
        sold_prod = view_buyer(client_socket)
        bought_prod = display_products_bought_by_user(client_socket, on_start=True)
        points = get_user_points(client_socket)
        send_reply(client_socket, {"action" : "your_info", "all_products" : all_prod,"following" : following_dict, "your_sold_products" : sold_prod, "prod_for_sale" : prod_for_sale, "bought_prods" : bought_prod, "points" : points})
        
        
        
        

    
#HELPER FUNCTIONS END




       
#---MAIN DRIVER CODE FOR SERVER----
def driver(client_socket):
    global stop_reply
    try:
        buffer = ''
        while True:
            data = client_socket.recv(4096).decode()
            if not data:
                break
            buffer +=data
            while '\n' in buffer:
               raw_request, buffer = buffer.split('\n', 1)  # Extract one message at a time
            try:
                request = json.loads(raw_request)
                print("request", request)
                action = request["action"]
                if action == "display_user":
                    user = request["username"]
                    display_products_of_user(client_socket, user)
                elif action == "send":
                    handle_send(client_socket, request)
                elif action == "show_matching": 
                    display_matching_products(client_socket, request["search_term"])
                elif action == "buy":
                    buy_product(client_socket, request["ID"], request["quantity_bought"])
                elif action == "check":
                    user = request["user"]
                    handle_check(client_socket, user)
                elif action == "add":
                    stop_reply = False
                    add_product_to_marketplace(client_socket, request["name"], request["price"], request["description"],request["image"],request["quantity"])           
                elif action == "view" :
                    view_buyer(client_socket) 
                elif action == "get_msgs":
                    get_undelivered_messages(client_socket)   
                elif action == "p2p_info":
                    get_P2P_info(client_socket, request["username"])
                elif action == "p2p_req":
                    p2p_req(client_socket, request["username"])
                elif action == "p2p_confirmation":
                    requester = request["requester"]
                    response = request["response"]
                    
                    if requester in UserToSocket:
                        requester_socket = UserToSocket[requester]
                        if response == "accept":
                            send_reply(requester_socket, {"action": "p2p_conf", "response" : "accepted"})
                        else:
                            send_reply(requester_socket, {"action": "p2p_conf", "response" : "declined"})
                    
                elif action == "rate":
                    rate_product(client_socket, request["product_id"], request["rate"]) 
                
                elif action == "show_users" :
                   fetch_all_users(client_socket)
                elif action == "follow":
                   add_follower_to_database(client_socket, request["followed_username"])
                   send_reply(client_socket, {"action": "follow", "status": "success", "message": f"You are now following {request['followed_username']}."})# Send a confirmation back to the client
                elif action == "send_udp_info":
                    user_data[Connections[client_socket]] = {'ip': request["ip"], 'port': request["port"]} # Save IP and port with username in a dict of user data dicts
                    send_user_data(client_socket)
                elif action == "unfollow":
                    unfollow_user(client_socket, request['unfollowed_username'])
                elif action == "my_products":
                    prod_list = display_products_of_user(client_socket, Connections[client_socket], True)
                    send_reply(client_socket, {"action" : "your_products", "content" : prod_list})
                elif action == "my_purchases":
                    display_products_bought_by_user(client_socket, False)
                elif action == "sold_prod":
                    prod_list = view_buyer(client_socket)
                    send_reply(client_socket, {"action" : "your_sold_products", "content" : prod_list})
                elif action == "change_currency" :
                    handle_client_currency_change(client_socket, request["currency"])
                elif request == "sending_add":
                    stop_reply = True
                elif action == "bump_listing":
                    bump_listing(client_socket, request["product_id"])
                elif action == "log_out":
                    handle_log_out(client_socket, request["username"])
            except json.JSONDecodeError as e: 
                print(f"JSONDecodeError: {e} - Raw request: {request}") 
                continue
            else:
                time.sleep(1)
            request = ''
    except (ConnectionResetError, ConnectionAbortedError) as e:
        print(f"Connection error with client: {e}")
        
            
#---HANDLES CLIENTS---
def handle_client(client_socket):
    try:
        handle_client_log_reg(client_socket)
        driver(client_socket)   
    except (ConnectionAbortedError, ConnectionResetError) as e:
        print(f"Connection with client was terminated error: {e}")
    finally:
        handle_log_out(client_socket, Connections[client_socket])
        
        
#---MAIN FUNCTION---
def main():
    create_database()
    server = create_socket()
    try:
        print(Connections)
        print(user_data)
        print(UserToSocket)
        while True:
            client_socket, addr = server.accept()
            print(f"Connect established with ({client_socket}, {addr})")
            
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        print("Server is shutting down.")
    finally:
        server.close()
        
#START SERVER    
main()





