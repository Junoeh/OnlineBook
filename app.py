from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

envuser = os.getenv("user")
envpassword = os.getenv("password")
envhost = os.getenv("host")
envsecret = os.getenv("secret_key")

app = Flask(__name__)
app.secret_key = envsecret


CATEGORIES = ["Horror", "Funny", "Sad"]


db = mysql.connector.connect(
    host=envhost,
    user=envuser,
    password=envpassword,
    database="booksite"
)


@app.route("/")
def home():
    category = request.args.get("category")

    cursor = db.cursor()

    if category in CATEGORIES:
        cursor.execute("""
            SELECT books.id, books.title, books.content, books.category, users.email, books.created_at
            FROM books
            JOIN users ON books.user_id = users.id
            WHERE books.category = %s
            ORDER BY books.created_at DESC
        """, (category,))
    else:
        cursor.execute("""
            SELECT books.id, books.title, books.content, books.category, users.email, books.created_at
            FROM books
            JOIN users ON books.user_id = users.id
            ORDER BY books.created_at DESC
        """)

    books = cursor.fetchall()
    cursor.close()

    return render_template("index.html", books=books)


@app.route("/book/<book_id>")
def book_detail(book_id):
    cursor = db.cursor()
    cursor.execute("""
        SELECT books.id, books.title, books.content, books.category, users.email, books.created_at
        FROM books
        JOIN users ON books.user_id = users.id
        WHERE books.id = %s
    """, (book_id,))
    book = cursor.fetchone()
    cursor.close()

    if not book:
        return "Book not found", 404

    return render_template("book_detail.html", book=book)


@app.route("/submit", methods=["GET", "POST"])
def submit_book():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        category = request.form["category"]

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO books (user_id, title, content, category)
            VALUES (%s, %s, %s, %s)
        """, (session["user_id"], title, content, category))
        db.commit()
        cursor.close()

        return redirect("/")

    return render_template("submit_book.html", categories=CATEGORIES)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, password)
        )
        db.commit()
        cursor.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor = db.cursor()
        cursor.execute(
            "SELECT id, password FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()

        if user and user[1] == password:
            session["user_id"] = user[0]
            return redirect("/")
        else:
            return "Invalid login", 401

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
