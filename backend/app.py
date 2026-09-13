from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app.secret_key = "foodhub-secret-key-2026"

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False

# =========================================================
# CORS CONFIGURATION
# =========================================================

CORS(
    app,
    origins=["http://18.60.251.24:30080"],
    supports_credentials=True
)

# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-service",
        user="appuser",
        password="password",
        database="three_tier_db"
    )

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "FoodHub Backend is running"
    })

# =========================================================
# SIGNUP
# =========================================================

@app.route("/signup", methods=["POST"])
def signup():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Email already registered"
            }), 409

        hashed_password = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (name, email, hashed_password)
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Signup successful"
        }), 201

    except Exception as e:

        print("SIGNUP ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Database error"
        }), 500

# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, password, role
            FROM users
            WHERE email = %s
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if not user:

            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        if not check_password_hash(user["password"], password):

            return jsonify({
                "success": False,
                "message": "Invalid email or password"
            }), 401

        session["user_id"] = user["id"]
        session["name"] = user["name"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    except Exception as e:

        print("LOGIN ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Database error"
        }), 500

# =========================================================
# CURRENT USER
# =========================================================

@app.route("/me", methods=["GET"])
def me():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Not logged in"
        }), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session["user_id"],
            "name": session["name"],
            "email": session["email"],
            "role": session["role"]
        }
    })

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "message": "Logout successful"
    })

# =========================================================
# foods
# =========================================================

@app.route("/foods", methods=["GET"])
def get_foods():

    try:

        db_conn = get_db_connection()

        cursor = db_conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                name,
                description,
                price,
                category,
                image,
                is_available
            FROM foods
            WHERE is_available = TRUE
            ORDER BY id ASC
            """
        )

        foods = cursor.fetchall()

        cursor.close()

        return jsonify({
            "status": "success",
            "foods": foods
        })

    except Exception as e:

        print("FOODS ERROR:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
# CREATE ORDER
# =========================================================

@app.route("/order", methods=["POST"])
def create_order():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    data = request.get_json() or {}

    items = data.get("items")
    total = data.get("total")
    customer_name = data.get("customer_name") or session.get("name")
    phone = data.get("phone")
    address = data.get("address")
    payment_method = data.get("payment_method")

    if not items:
        return jsonify({
            "success": False,
            "message": "Order items are required"
        }), 400

    if total is None:
        return jsonify({
            "success": False,
            "message": "Order total is required"
        }), 400

    if not address:
        return jsonify({
            "success": False,
            "message": "Delivery address is required"
        }), 400

    if not payment_method:
        return jsonify({
            "success": False,
            "message": "Payment method is required"
        }), 400

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO orders
            (
                items,
                total,
                customer_email,
                customer_name,
                phone,
                address,
                payment_method,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(items),
                float(total),
                session["email"],
                customer_name,
                phone,
                address,
                payment_method,
                "Pending"
            )
        )

        order_id = cursor.lastrowid

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Order placed successfully",
            "order_id": order_id
        }), 201

    except Exception as e:

        print("ORDER ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to place order",
            "error": str(e)
        }), 500

# =========================================================
# GET MY ORDERS
# =========================================================

@app.route("/my-orders", methods=["GET"])
def get_my_orders():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                items,
                total,
                customer_email,
                customer_name,
                phone,
                address,
                payment_method,
                status,
                created_at
            FROM orders
            WHERE customer_email = %s
            ORDER BY id DESC
            """,
            (session["email"],)
        )

        orders = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "orders": orders
        }), 200

    except Exception as e:

        print("MY ORDERS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load orders",
            "error": str(e)
        }), 500


# =========================================================
# CANCEL ORDER
# =========================================================

@app.route("/my-orders/<int:order_id>/cancel", methods=["PUT"])
def cancel_order(order_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, customer_email, status
            FROM orders
            WHERE id = %s AND customer_email = %s
            """,
            (order_id, session["email"])
        )

        order = cursor.fetchone()

        if not order:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        if order["status"] == "Cancelled":
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Order is already cancelled"
            }), 400

        cursor.execute(
            """
            UPDATE orders
            SET status = 'Cancelled'
            WHERE id = %s AND customer_email = %s
            """,
            (order_id, session["email"])
        )

        cursor.execute(
            """
            INSERT INTO notifications
            (
                customer_email,
                order_id,
                message,
                status
            )
            VALUES (%s, %s, %s, 'unread')
            """,
            (
                session["email"],
                order_id,
                "Your order #" + str(order_id) + " has been cancelled."
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Order cancelled successfully"
        }), 200

    except Exception as e:

        print("CANCEL ORDER ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to cancel order",
            "error": str(e)
        }), 500


# =========================================================
# GET NOTIFICATIONS
# =========================================================

@app.route("/notifications", methods=["GET"])
def get_notifications():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                order_id,
                message,
                status,
                created_at
            FROM notifications
            WHERE customer_email = %s
            ORDER BY id DESC
            """,
            (session["email"],)
        )

        notifications = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "notifications": notifications
        }), 200

    except Exception as e:

        print("NOTIFICATIONS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load notifications",
            "error": str(e)
        }), 500


# =========================================================
# MARK NOTIFICATION AS READ
# =========================================================

@app.route("/notifications/<int:notification_id>/read", methods=["PUT"])
def mark_notification_read(notification_id):

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE notifications
            SET status = 'read'
            WHERE id = %s
            AND customer_email = %s
            """,
            (notification_id, session["email"])
        )

        if cursor.rowcount == 0:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Notification not found"
            }), 404

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Notification marked as read"
        }), 200

    except Exception as e:

        print("READ NOTIFICATION ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to update notification",
            "error": str(e)
        }), 500


# =========================================================
# CONTACT MESSAGE
# =========================================================

@app.route("/contact", methods=["POST"])
def submit_contact():

    data = request.get_json() or {}

    name = str(data.get("name") or "").strip()
    email = str(data.get("email") or "").strip()
    message = str(data.get("message") or "").strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Name is required"
        }), 400

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    if not message:
        return jsonify({
            "success": False,
            "message": "Message is required"
        }), 400

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO messages
            (
                name,
                email,
                message
            )
            VALUES (%s, %s, %s)
            """,
            (
                name,
                email,
                message
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Message sent successfully"
        }), 201

    except Exception as e:

        print("CONTACT ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to send message",
            "error": str(e)
        }), 500


# =========================================================
# RATING
# =========================================================

@app.route("/rating", methods=["POST"])
def submit_rating():

    if "user_id" not in session:
        return jsonify({
            "success": False,
            "message": "Please login first"
        }), 401

    data = request.get_json() or {}

    rating = data.get("rating")
    comment = str(data.get("comment") or "").strip()

    if rating is None:
        return jsonify({
            "success": False,
            "message": "Rating is required"
        }), 400

    try:

        rating = int(rating)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message": "Rating must be a number"
        }), 400

    if rating < 1 or rating > 5:
        return jsonify({
            "success": False,
            "message": "Rating must be between 1 and 5"
        }), 400

    try:

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO ratings
            (
                customer_email,
                rating,
                comment
            )
            VALUES (%s, %s, %s)
            """,
            (
                session["email"],
                rating,
                comment
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Rating submitted successfully"
        }), 201

    except Exception as e:

        print("RATING ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to submit rating",
            "error": str(e)
        }), 500


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
