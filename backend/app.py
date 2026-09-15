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
app.config["SESSION_COOKIE_PATH"] = "/"

# =========================================================
# CORS CONFIGURATION
# =========================================================

CORS(
    app,
    origins=[
    "http://18.60.55.13:30080",
    "http://18.60.251.24:30080",
    "http://18.61.84.133:30080"],
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

        cursor.execute(
            """
            INSERT INTO order_status_history
            (
                order_id,
                status,
                message
            )
            VALUES (%s, %s, %s)
            """,
            (
                order_id,
                "Pending",
                "Order placed successfully"
            )
        )

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
# GET ORDER TRACKING
# =========================================================

@app.route("/my-orders/<int:order_id>/tracking", methods=["GET"])
def get_order_tracking(order_id):

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
                h.id,
                h.status,
                h.message,
                h.created_at
            FROM order_status_history h
            JOIN orders o
                ON o.id = h.order_id
            WHERE h.order_id = %s
              AND o.customer_email = %s
            ORDER BY h.id ASC
            """,
            (
                order_id,
                session["email"]
            )
        )

        history = cursor.fetchall()

        cursor.close()
        db.close()

        if not history:
            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        return jsonify({
            "success": True,
            "order_id": order_id,
            "tracking": history
        }), 200

    except Exception as e:

        print("ORDER TRACKING ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load order tracking",
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
# ADMIN RATINGS
# =========================================================

@app.route("/admin/ratings", methods=["GET"])
def admin_ratings():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                customer_email,
                rating,
                comment,
                created_at
            FROM ratings
            ORDER BY created_at DESC
        """)

        ratings = cursor.fetchall()

        return jsonify({
            "success": True,
            "ratings": ratings
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


# =========================================================
# ADMIN API
# =========================================================

def admin_required():
    role = session.get("role") or request.headers.get("X-Admin-Role")
    return role == "admin"


@app.route("/admin/login", methods=["POST"])
def admin_login():
    try:
        data = request.get_json()

        email = data.get("email", "").strip()
        password = data.get("password", "")

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, password, role FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        db.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid admin login"
            }), 401

        if user["role"] != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required"
            }), 403

        if not check_password_hash(user["password"], password):
            return jsonify({
                "success": False,
                "message": "Invalid admin login"
            }), 401

        return jsonify({
            "success": True,
            "message": "Admin login successful",
            "admin": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
        })

    except Exception as e:
        print("ADMIN LOGIN ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Admin login failed",
            "error": str(e)
        }), 500


@app.route("/admin/stats", methods=["GET"])
def admin_stats():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total_users FROM users")
        total_users = cursor.fetchone()["total_users"]

        cursor.execute("SELECT COUNT(*) AS total_orders FROM orders")
        total_orders = cursor.fetchone()["total_orders"]

        cursor.execute("SELECT COUNT(*) AS total_foods FROM foods")
        total_foods = cursor.fetchone()["total_foods"]

        cursor.execute(
            "SELECT COALESCE(SUM(total), 0) AS total_sales FROM orders"
        )
        total_sales = cursor.fetchone()["total_sales"]

        cursor.execute(
            "SELECT COUNT(*) AS pending_orders FROM orders WHERE status='Pending'"
        )
        pending_orders = cursor.fetchone()["pending_orders"]

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_orders": total_orders,
                "total_foods": total_foods,
                "total_sales": float(total_sales),
                "pending_orders": pending_orders
            }
        })

    except Exception as e:
        print("ADMIN STATS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load statistics",
            "error": str(e)
        }), 500


@app.route("/admin/users", methods=["GET"])
def admin_users():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            "SELECT id, name, email, role FROM users ORDER BY id DESC"
        )

        users = cursor.fetchall()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "users": users
        })

    except Exception as e:
        print("ADMIN USERS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load users",
            "error": str(e)
        }), 500


@app.route("/admin/orders", methods=["GET"])
def admin_orders():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, items, total, customer_email,
                   customer_name, phone, address,
                   payment_method, status, created_at
            FROM orders
            ORDER BY id DESC
            """
        )

        orders = cursor.fetchall()

        cursor.close()
        db.close()

        for order in orders:
            if order.get("total") is not None:
                order["total"] = float(order["total"])

        return jsonify({
            "success": True,
            "orders": orders
        })

    except Exception as e:
        print("ADMIN ORDERS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load orders",
            "error": str(e)
        }), 500


@app.route("/admin/orders/<int:order_id>/status", methods=["PUT"])
def admin_update_order_status(order_id):

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    try:
        data = request.get_json() or {}
        status = data.get("status", "").strip()

        allowed_statuses = [
            "Pending",
            "Confirmed",
            "Preparing",
            "Out for Delivery",
            "Delivered",
            "Cancelled"
        ]

        status_messages = {
            "Pending": "Order placed successfully",
            "Confirmed": "Your order has been confirmed",
            "Preparing": "Your food is being prepared",
            "Out for Delivery": "Your order is out for delivery",
            "Delivered": "Your order has been delivered",
            "Cancelled": "Your order has been cancelled"
        }

        if status not in allowed_statuses:
            return jsonify({
                "success": False,
                "message": "Invalid order status"
            }), 400

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, customer_email, status
            FROM orders
            WHERE id = %s
            """,
            (order_id,)
        )

        order = cursor.fetchone()

        if not order:
            cursor.close()
            db.close()

            return jsonify({
                "success": False,
                "message": "Order not found"
            }), 404

        old_status = order["status"]

        if old_status == status:
            cursor.close()
            db.close()

            return jsonify({
                "success": True,
                "message": "Order status is already " + status
            }), 200

        cursor.execute(
            """
            UPDATE orders
            SET status = %s
            WHERE id = %s
            """,
            (status, order_id)
        )

        cursor.execute(
            """
            INSERT INTO order_status_history
            (
                order_id,
                status,
                message
            )
            VALUES (%s, %s, %s)
            """,
            (
                order_id,
                status,
                status_messages[status]
            )
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
            VALUES (%s, %s, %s, %s)
            """,
            (
                order["customer_email"],
                order_id,
                status_messages[status],
                "unread"
            )
        )

        db.commit()

        cursor.close()
        db.close()

        return jsonify({
            "success": True,
            "message": "Order status updated",
            "order_id": order_id,
            "old_status": old_status,
            "new_status": status
        }), 200

    except Exception as e:
        try:
            db.rollback()
        except:
            pass

        print("ADMIN ORDER STATUS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to update order status",
            "error": str(e)
        }), 500



@app.route("/admin/messages", methods=["GET"])
def admin_messages():
    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                message,
                created_at
            FROM messages
            ORDER BY created_at DESC
        """)

        messages = cursor.fetchall()

        return jsonify({
            "success": True,
            "messages": messages
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/admin/messages/<int:message_id>/reply", methods=["POST"])
def admin_reply_message(message_id):
    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    data = request.get_json(silent=True) or {}
    reply = str(data.get("reply") or "").strip()

    if not reply:
        return jsonify({
            "success": False,
            "message": "Reply is required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email
            FROM messages
            WHERE id = %s
        """, (message_id,))

        customer = cursor.fetchone()

        if not customer:
            return jsonify({
                "success": False,
                "message": "Message not found"
            }), 404

        # Store admin reply as a notification for the customer.
        cursor.execute("""
            INSERT INTO notifications
                (customer_email, order_id, message, status)
            VALUES
                (%s, NULL, %s, 'unread')
        """, (
            customer["email"],
            reply
        ))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Reply sent successfully"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()



@app.route("/admin/foods", methods=["POST"])
def admin_add_food():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    price = data.get("price")
    category = data.get("category", "").strip()
    food_type = data.get("food_type", "Veg").strip()
    image = data.get("image", "").strip()
    is_available = data.get("is_available", 1)

    if not name or price is None or not category:
        return jsonify({
            "success": False,
            "message": "Name, price and category are required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO foods
            (name, description, price, category, food_type, image, is_available)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            name,
            description,
            price,
            category,
            food_type,
            image,
            is_available
        ))

        conn.commit()
        food_id = cursor.lastrowid

        return jsonify({
            "success": True,
            "message": "Food added successfully",
            "food_id": food_id
        }), 201

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN ADD FOOD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to add food",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/admin/foods/<int:food_id>", methods=["PUT"])
def admin_update_food(food_id):

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    data = request.get_json() or {}

    name = data.get("name", "").strip()
    description = data.get("description", "").strip()
    price = data.get("price")
    category = data.get("category", "").strip()
    food_type = data.get("food_type", "Veg").strip()
    image = data.get("image", "").strip()
    is_available = data.get("is_available", 1)

    if not name or price is None or not category:
        return jsonify({
            "success": False,
            "message": "Name, price and category are required"
        }), 400

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE foods
            SET name=%s,
                description=%s,
                price=%s,
                category=%s,
                food_type=%s,
                image=%s,
                is_available=%s
            WHERE id=%s
        """, (
            name,
            description,
            price,
            category,
            food_type,
            image,
            is_available,
            food_id
        ))

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Food not found"
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Food updated successfully"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN UPDATE FOOD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to update food",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/admin/foods/<int:food_id>", methods=["DELETE"])
def admin_delete_food(food_id):

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM foods WHERE id=%s",
            (food_id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "message": "Food not found"
            }), 404

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Food deleted successfully"
        })

    except Exception as e:
        if conn:
            conn.rollback()

        print("ADMIN DELETE FOOD ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to delete food",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route("/admin/foods", methods=["GET"])
def admin_foods():

    if not admin_required():
        return jsonify({
            "success": False,
            "message": "Admin access required"
        }), 403

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, description, price,
                   category, food_type, image, is_available
            FROM foods
            ORDER BY id DESC
            """
        )

        foods = cursor.fetchall()

        cursor.close()
        db.close()

        for food in foods:
            if food.get("price") is not None:
                food["price"] = float(food["price"])

        return jsonify({
            "success": True,
            "foods": foods
        })

    except Exception as e:
        print("ADMIN FOODS ERROR:", e)

        return jsonify({
            "success": False,
            "message": "Failed to load foods",
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
