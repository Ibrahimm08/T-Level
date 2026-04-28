from flask import Flask, request, render_template, redirect, url_for ,session
import sqlite3
import bcrypt

DB = "database.db" # Path to our database

# Generate the salt 
salt = bcrypt.gensalt()

# Points per £ spent
POINT_RATE = 2 



app = Flask(__name__)

# As this is a prototype a secure key is not needed
# If this were to be a public the key must be securely made and stored to prevent insecure cookies
app.secret_key = "Replace-Key-After-Development"


# Functions to connect and disconnect our Database
def ConnectDB():
    global conn, cursor # Allows us to use outside of this function
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

# Must use commit function before if changes are made to database
def CloseDB():
    cursor.close()
    conn.close()


# Function to login
# account_type can be "CustomerAccount" or "BusinessAccount"
def LoginAccountType(account_type, email, password):
    account = False

    if account_type == "CustomerAccount":
        query = "SELECT * FROM CustomerAccount"
    else:
        query = "SELECT * FROM BusinessAccount"

    query = query + " WHERE LOWER(Email) = LOWER(?)" # Using placeholders prevent SQL injection by separating values from query
    values = (email,) 

    ConnectDB()
    account = (cursor.execute(query,values)).fetchone() # Gets the first result
    CloseDB()


    if account:
        # Hash the entered password and compare it with the hashed password in the Database
        if bcrypt.checkpw(password.encode("utf-8"), account[3]):
            session["user"] = account[0] # Creates a session storing ID keeping user logged in
            session["name"] = account[1] # Create a session to store name to display
            session["type"] = account_type # Store what type of account is signed in
            print("redirecting")
            return True
    # No need to check if account not exists as if we don't get redirected something went wrong
    # Provide error message
    return False



# Function to create an account
# Used at /register
# Password and password confirmation will be checked in front-end using JavaScript
def CreateAccount(account_type, full_name, email, password):
    
    # Hash and encode the password into bytes before putting in DB for security
    password = bcrypt.hashpw(password.encode("utf-8"), salt)
    
    if account_type == "CustomerAccount":
        query = "INSERT INTO CustomerAccount"
    else:
        query = "INSERT INTO BusinessAccount"

    # Concattonate string onto query
    query = query + " (Name, Email, Password) VALUES (?,?,?)"
    values = (full_name, email, password)

    ConnectDB()
    # Try to add account into the database
    # If an error occurs, provide an error message to be displayed
    try:
        cursor.execute(query,values)
        conn.commit() # Save our changes
    except:
        print("Error has occured in Function CreatAccount")
        CloseDB()    
        return False
    else:
        CloseDB()
    # If successfull redirect to login page
    return True





@app.route("/")

@app.route("/index")
def Index():
    page_name="Greenfield Local Hub"
    return render_template("index.html", page_name=page_name)



@app.route("/about")
def About():
    page_name="About"

    return render_template("about.html", page_name=page_name)



# Use POST method for security - doesn't put values in the url 
@app.route("/login", methods=["GET", "POST"])
def Login():
    page_name="Login"
    error_msg= False # Error message won't be shown on page load

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Tells us which table to look into for the account based on radio value
        account_type = request.form.get("account-type")
        
        # If login failed user wont be redirected, giving error message instead
        if LoginAccountType(account_type, email, password):
             return redirect(url_for("Dashboard"))


        error_msg = "Invalid Email or Password, please check if the right account type is selected"
        
    return render_template("login.html", page_name=page_name, error_msg=error_msg)



# Use POST method for security - doesn't put values in the url
@app.route("/register", methods=["GET", "POST"])
def Register():
    page_name = "Register an Account"
    error_msg = False

    if request.method == "POST":
        # Similar process to Login()
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Tells us which table to look into for the account based on radio value
        account_type = request.form.get("account-type")
        
        # If register failed user wont be redirected, giving error message instead
        if CreateAccount(account_type, name, email, password):
            return redirect("/login")
      

        error_msg = "There was an issue when creating your account. Please try again later or contact us for help"

    return render_template("register.html", page_name = page_name, error_msg = error_msg)



@app.route("/products", methods=["GET", "POST"])
def Products():
    page_name="Products"
    products = False

    # Implement sorting and filtering by combining where clauses using .join()
    query = "SELECT * FROM Product"
    categories_query = "SELECT * FROM Category"
    

    # if request.method == "GET":
    #     # Go through each form entry and add onto parameter and values to combine in a where_clause using .join
    #     # Attach at the end of the query

    #     where_clause = ""
    #     params = []
    #     values = []

    #     # Get min and max values
    #     min = request.form.get("min")
    #     max = request.form.get("max")

    #     # Get Category

    #     # Get checked values

    #     # Combine Parameters into where clause

    #     where_clause = where_clause.join(params) if params else "1 = 1"

    #     # Update query and execute with values



    ConnectDB()
    products = cursor.execute(query).fetchall()
    
    categories = cursor.execute(categories_query).fetchall()
    CloseDB()

    return render_template("products.html", page_name=page_name, categories = categories, products=products)



@app.route("/products-single/<int:id>")
def ProductSingle(id):
    page_name="ProductName" # Change into the products name that has been clicked

    # If id failed to pass through give user an error message 
    try:
        # Join the category with matching IDs
        query = "SELECT * FROM Product JOIN Category ON Product.CategoryID = Category.ID WHERE Product.ID = ? "
        business_query = "SELECT Name FROM BusinessAccount LEFT JOIN Product ON BusinessAccount.ID = Product.BusinessAccountID"
        values = (id,)

        ConnectDB()
        product = cursor.execute(query,values).fetchone()
        business_name = cursor.execute(business_query).fetchone()
        CloseDB()

        page_name = product[1]
    except:
        return ("Something went wrong: Failed to load product")
       

    return render_template("products_single.html", page_name=page_name, product=product, business_name = business_name)



# --------- Cart & Cart Functions --------


@app.route("/add-to-cart", methods=["GET", "POST"])
def AddToCart():
    if request.method == "POST":
        if session.get("user", {}):
            
            # Prevent business users from adding to cart that they don't have
            if  session.get("type", {}) == "BusinessAccount":
                return redirect("/index")
            
            amount = request.form.get("amount")
            product_id = request.form.get("product-id")
            user_id = session.get("user", {})

            # Update on duplicate if user already has item in cart
            query = "INSERT INTO Cart (CustomerAccountID, ProductID, Amount) VALUES (?, ?, ?) ON CONFLICT DO UPDATE SET Amount = ?" 
            values = (user_id, product_id, amount, amount)

            ConnectDB()
            cursor.execute(query,values)
            conn.commit()
            CloseDB()

            print("Added item into cart")

            return redirect("/cart")
        else:
            print("not logged in")
            return redirect("/login")


# Should only be accessible by Customers
@app.route("/cart")
def Cart():
    page_name = "Your Cart"
    
    user_id = session.get("user", {})
    user_type = session.get("type", {})

    # If user is business account send them to home page
    if user_type == "BusinessAccount":
        return redirect("/index")

    # Get Products based off of Cart contents 
    query = "Select * From Cart JOIN Product ON Product.ID = Cart.ProductID Where Cart.CustomerAccountID = ?"
    values = (user_id, )

    ConnectDB()
    products = cursor.execute(query, values).fetchall()
    CloseDB()

    return render_template("cart.html", products=products, page_name=page_name)



# id is passed from front end 
@app.route("/remove-product/<int:id>")
def RemoveFromCart(id):
    user_id = session.get("user", {})
    product_id = id
    
    query = "DELETE FROM Cart WHERE CustomerAccountID = ? AND ProductID = ?"
    values = (user_id, product_id)

    ConnectDB()
    cursor.execute(query,values)
    conn.commit()
    CloseDB()

    return redirect("/cart")



# ------- Checkout/Purchasing Routes --------



# Set a value to decide if order is preferred to be delivered or collected
@app.route("/checkout/<int:method>")
def CheckoutMethod(method):
    # 1 = collection
    # 0 = delivery
    if method == 1:
        session["order-method"] = "Collection"
    else:
        session["order-method"] = "Delivery"
    
    return redirect("/checkout/order-details")



@app.route("/checkout/review")
def CheckoutReviewCart():
    page_name = "Checkout Review Cart"

    user_id = session.get("user", {})


    # Get Products based off of Cart.productID with user ID to display 
    query = "Select * From Cart JOIN Product ON Product.ID = Cart.ProductID Where Cart.CustomerAccountID = ?"
    values = (user_id, )

    ConnectDB()
    products = cursor.execute(query, values).fetchall()
    CloseDB()

    return render_template("checkout/review.html", page_name=page_name, products = products)



@app.route("/checkout/order-details", methods = ["GET", "POST"])
def CheckoutDetails():
    page_name = "Checkout Order Details"
    
    user_id = session.get("user", {})
    address = None


    # Get user information regarding address 
    # Allow user to use existing address or update it
    query = "SELECT Address From CustomerAccount WHERE ID = ?"
    values = (user_id, )

    ConnectDB()
    address = cursor.execute(query,values).fetchone()
    CloseDB()

    if request.method == "POST":
        # Get or prefferred date and store it in session
        session["order-date"] = request.form.get("date")

        return redirect("/checkout/review-order")

        

    return render_template("checkout/order_details.html", page_name = page_name, address = address)



@app.route("/checkout/add-address", methods = ["GET", "POST"])
def CheckoutAddAddress():
    page_name = "Add Address"
    user_id = session.get("user", {})

    if request.method == "POST":
        # Get address and Store it in user data
        postcode = request.form.get("postcode")
        city = request.form.get("city")

        address_line_1 = request.form.get("address-line-1")
        address_line_2 = request.form.get("address-line-2")

        # Concat our address to store together
        address = f"Postcode: {postcode}    City: {city}   Address Line 1: {address_line_1}  Address Line 2: {address_line_2}"

        query = "UPDATE CustomerAccount SET Address = ? WHERE ID = ?"
        values = (address, user_id)

        ConnectDB()
        cursor.execute(query,values)
        conn.commit()
        CloseDB()

        return redirect("/checkout/order-details")
    
    return render_template("checkout/add_address.html", page_name=page_name)



@app.route("/checkout/review-order")
def CheckoutReviewOrder():
    page_name = "Review Order"
    # Get Cart Info and calculate fees and total
    # Get Order date
    # Get order method
    # Get Address

    user_id = session.get("user", {})
    order_method = session.get("order-method", {})
    order_date = session.get("order-date", {})

    # Get our address and cart items
    address_query = "SELECT Address From CustomerAccount WHERE ID = ?"
    cart_query = "Select * From Cart JOIN Product ON Product.ID = Cart.ProductID Where Cart.CustomerAccountID = ?"
    
    # Alter the query so that user can only checkout items that meets their prefference
    if order_method == "Delivery":
        cart_query += " AND Product.DeliveryAvailable = 1"
    else:
        cart_query += " AND Product.CollectionAvailable = 1"

    values = (user_id, )

    ConnectDB()
    address = cursor.execute(address_query,values).fetchone()
    cart = cursor.execute(cart_query, values).fetchall()
    CloseDB()

    # calculate the total by looping through each item   
    total = 0
    for item in cart:
        amount = item[2]
        cost = item[6]
        total += (cost*amount)

    # if delivery add £3 fee
    if order_method == "Delivery":
        total += 3

    # Store total for later use
    session["total"] = total

    return render_template("checkout/review_order.html", page_name = page_name, order_method = order_method, order_date = order_date, address = address, products = cart, total = total)

    

@app.route("/checkout/payment", methods = ["GET", "POST"])
def Payment():
    page_name = "Payment"

    # Get the total of the order
    total = session.get("total", {})

    # As this is a prototype no payment portal and functionality will be introduced later in development
    # Ideally if this process failed we would offer a refund
    
    
    # Assuming payment portal provided confirmation of payment being made

    if request.method == "POST":
        user_id = session.get("user", {})
        order_method = session.get("order-method", {})

        if order_method == "Delivery":
            method_check = " AND Product.DeliveryAvailable = 1"
        else:
            method_check = " AND Product.CollectionAvailable = 1"



        # GOAL - Seperate orders based on the BusinessAccountID on Products
        # Sort products in cart based on business id
        # Remove Cart items meeting OrderMethod requirements and add it to OrderItem
        # Create customerOrder with businessID FK
        # OrderItem will get FK of order based on BusinessID from products 


        # Inserts values from Cart with matching userID and put it into OrderItem columns
        # Bindings 1
        order_item_query = "INSERT INTO OrderItem (CustomerAccountID, ProductID, Amount, BusinessAccountID) SELECT Cart.CustomerAccountID, Cart.ProductID, Cart.Amount, Product.BusinessAccountID FROM Cart JOIN Product ON Product.ID = Cart.ProductID Where Cart.CustomerAccountID = ?"

        # Make sure we are only getting the products that the user can order based on method
        order_item_query += method_check
        order_item_values = (user_id, )

        # Create a new order 
        new_order_query = "INSERT INTO CustomerOrder (Status, Type, Total, CustomerAccountID, BusinessAccountID) VALUES (?, ?, ?, ?, (SELECT OrderItem.BusinessAccountID FROM OrderItem WHERE OrderItem.CustomerAccountID = ?)) "
        new_order_values = ("Pending", order_method, total, user_id, user_id )

    
        # Remove items from cart as we have purchased them
        # Binding 1
        remove_query = f"DELETE FROM Cart WHERE ProductID IN (Select ProductID FROM CART JOIN Product ON Product.ID = Cart.ProductID WHERE Cart.CustomerAccountID = ? {method_check} )" # Make sure we only affect product we bought
        remove_values = (user_id, )

        # Insert Most Recent OrderID into OrderItems with same BusinessID and CustomerID From CustomerOrders
        # Makes sure that the Order only contains items the the Business User owns/provides
        # Only update feilds that are empty to prevent updating all rows
        insert_id_query = "UPDATE OrderItem SET OrderID = ? WHERE OrderID IS NULL"
        get_values = "SELECT MAX(CustomerOrder.ID) FROM CustomerOrder JOIN OrderItem ON OrderItem.CustomerAccountID = CustomerOrder.CustomerAccountID WHERE CustomerOrder.CustomerAccountID = OrderItem.CustomerAccountID AND CustomerOrder.BusinessAccountID = OrderItem.BusinessAccountID"
        insert_id_values = None


        # Calculate total and points gained by getting the Products from The OrderItem with the same most recent OrderID (MAX)
        # EG if we made an order with two products the OrderItem with MAX OrderID will contain those products 
        get_total_query = "SELECT SUM(Cost) From Product JOIN OrderItem ON OrderItem.ProductID = Product.ID WHERE OrderItem.OrderID = (SELECT MAX(OrderID) FROM OrderItem)"
        get_total_value = None

        # Give customer points
        customer_points_query = "UPDATE CustomerAccount SET Points = ? WHERE ID = ?"
        # Values = (get_total_value, user_id)

    
        ConnectDB()
        try:
            cursor.execute(order_item_query, order_item_values)
            cursor.execute(new_order_query, new_order_values)

            cursor.execute(remove_query, remove_values)

            # Commit so there are values in OrderItem table before we insert based of its values
            conn.commit()

            insert_id_values = cursor.execute(get_values).fetchone()
            cursor.execute(insert_id_query, insert_id_values)

            conn.commit()

            get_total_value = cursor.execute(get_total_query).fetchone()[0]
            get_total_value *= POINT_RATE
            print(get_total_value)
            cursor.execute(customer_points_query, (get_total_value, user_id))
        except:
            CloseDB()
            print("an error occured in the Function 'Payment'")
        else:        
            CloseDB()

        return redirect("/confirmation")

        

    return render_template("checkout/payment.html", page_name = page_name)



@app.route("/confirmation")
def Confirmation():
    page_name = "Order Successful"

    return render_template("checkout/confirmation.html", page_name = page_name)



# ------- Dashboard Routes -----------



@app.route("/dashboard", methods = ["GET", "POST"])
def Dashboard():
    page_name="My Dashboard"
    user_id = session.get("user", {}) # Gets user ID from session
    user_type = session.get("type", {})
    
    # Set false so that business users don't have points displayed on their dashboard
    points = False

    # If user is customer get their points to display
    if user_type == "CustomerAccount":
        query = "SELECT Points FROM CustomerAccount WHERE ID = ?"
        values = (user_id,)

        ConnectDB()

        points = cursor.execute(query,values).fetchone()[0]
        
        CloseDB()    
        

    return render_template("dashboard/dashboard.html", page_name=page_name, points=points )



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/index")


# View Inactive orders
@app.route("/order-history")
def OrderHistory():
    page_name = "Order History"
    user_id = session.get("user", {}) # Gets user ID from session
    user_type = session.get("type", {})

    order_list = None

    # Check column based on account type
    if user_type == "BusinessAccount":
        and_clause = " AND BusinessAccountID = ?"
    else:
        and_clause = " AND CustomerAccountID = ?"

    # Get orders that are completed
    query = "SELECT * FROM CustomerOrder WHERE Status = ('Cancelled') OR Status = ('Completed')  " + and_clause
    values = (user_id, )

    ConnectDB()

    order_list = cursor.execute(query,values).fetchall()

    CloseDB()


    return render_template("dashboard/view_order.html", page_name = page_name, orders = order_list)



# View active orders
@app.route("/view-order")
def ViewOrder():
    page_name = "View Orders"
    user_id = session.get("user", {}) # Gets user ID from session
    user_type = session.get("type", {})

    order_list = None

    # Check column based on account type
    if user_type == "BusinessAccount":
        and_clause = " AND BusinessAccountID = ?"
    else:
        and_clause = " AND CustomerAccountID = ?"

    # Get Orders that are not cancelled or not completed
    query = "SELECT * FROM CustomerOrder WHERE Status <> ('Cancelled') AND Status <> ('Completed')  " + and_clause
    values = (user_id, )

    ConnectDB()

    order_list = cursor.execute(query,values).fetchall()

    CloseDB()


    return render_template("dashboard/view_order.html", page_name = page_name, orders = order_list)



# View order in more detail
@app.route("/view-order/<int:id>")
def SingleOrder(id):
    page_name = "Order Details"
    user_id = session.get("user", {}) # Gets user ID from session
    user_type = session.get("type", {})

    item_list = None

    # Check column based on account type
    if user_type == "BusinessAccount":
        and_clause = " AND OrderItem.BusinessAccountID = ?"
    else:
        and_clause = " AND OrderItem.CustomerAccountID = ?"

    # Get All item info from order
    query = "SELECT * FROM Product LEFT JOIN OrderItem ON OrderItem.ProductID = Product.ID WHERE OrderItem.OrderID = ?" + and_clause
    values = (id, user_id)

    # Query to get order total
    order_total_query = "SELECT Total FROM CustomerOrder WHERE ID = ?"
    order_total_values = (id, )
    order_total = None
    ConnectDB()

    item_list = cursor.execute(query,values).fetchall()
    order_total = cursor.execute(order_total_query, order_total_values).fetchone()
    CloseDB()


    return render_template("dashboard/view_order_single.html", page_name = page_name, item_list = item_list, total = order_total)


# BusinessAccount Updating order Status
@app.route("/edit-order/<int:id>", methods = ["GET", "POST"] )
def EditOrder(id):
    page_name = "Edit Order"

    # Get type to display more status options in front-end
    type_query = "SELECT Type FROM CustomerOrder WHERE ID = ?"
    type_values = (id, )
    type_result = None
    
    
    ConnectDB()
    type_result = cursor.execute(type_query, type_values).fetchone()
    CloseDB()


    if request.method == "POST":
        new_status = request.form.get("status")

        query = "UPDATE CustomerOrder SET Status = ? WHERE ID = ?"
        values = (new_status, id)


        ConnectDB()
        cursor.execute(query,values)
        conn.commit()
        CloseDB()

        return redirect("/view-order")

    return render_template("dashboard/edit_order.html", page_name = page_name, order_id = id, type = type_result)


@app.route("/cancel-order/<int:id>")
def CancelOrder(id):
    new_status = "Cancelled"

    query = "UPDATE CustomerOrder SET Status = ? WHERE ID = ?"
    values = (new_status, id)


    ConnectDB()
    cursor.execute(query,values)
    conn.commit()
    CloseDB()

    return redirect("/view-order")



# Should only be accessible by BusinessAccounts
@app.route("/view-product", methods = ["GET", "POST"])
def ViewProduct():
    page_name = "View Products"
    user_id = session.get("user", {})
    user_type = session.get("type", {})

    # If user isn't business account send them to home page
    if user_type != "BusinessAccount":
        return redirect("/index")
    
    # Get all products associated with user
    query = "SELECT * FROM Product WHERE BusinessAccountID = (?)"
    values = (user_id,)
    
    ConnectDB()
    products = cursor.execute(query, values).fetchall()
    CloseDB()



    return render_template("dashboard/view_product.html", page_name=page_name, products = products)



# Should only be accessible by BusinessAccounts
@app.route("/add-product", methods = ["GET", "POST"])
def AddProduct():
    page_name = "Add Product"
    user_id = session.get("user", {})
    user_type = session.get("type", {})

    error_msg = False

    query = "SELECT * FROM Category"
    
    ConnectDB()
    categories = cursor.execute(query).fetchall()
    CloseDB()

    # If user isn't business account send them to home page
    if user_type != "BusinessAccount":
        return redirect("/index")
    
    if request.method == "POST":
        name = request.form.get("name")
        
        category_id = request.form.get("category")
        description = request.form.get("desc")
        allergen = request.form.get("allergen")

        price = request.form.get("price")
        print(price)
        unit = request.form.get("unit")
        stock = request.form.get("stock")

        delivery_available = False
        if request.form.get("delivery"):
            delivery_available = True
        
        collection_available = False
        if request.form.get("collection"):
            collection_available = True
        
        method = request.form.get("method")


        query = "INSERT INTO Product (ProductName, Description, Cost, Unit, Stock, Allergens, Method, DeliveryAvailable, CollectionAvailable, BusinessAccountID, CategoryID) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        values = (name, description, price, unit, stock, allergen, method, delivery_available, collection_available, user_id, category_id)

        ConnectDB()
        try:
            cursor.execute(query, values)
            conn.commit()
        except:
            CloseDB()
            error_msg = "Something went wrong. Please try again."
        else:
            CloseDB()

    return render_template("dashboard/add_product.html", page_name=page_name, categories=categories, error_msg = error_msg)









if __name__ == "__main__":
    app.run(debug=True)