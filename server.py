from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import MySQLConnector
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.secret_key = "WallWallWallWallWallWallWallWall"

bcrypt = Bcrypt(app)

mysql = MySQLConnector(app, "another_wall")

@app.route("/")
def index():
	print(mysql.query_db("SELECT * FROM users"))
	return render_template("login.html")

@app.route("/register", methods=["POST"])
def register():
	first_name = request.form["first_name"]

	errors = []

	if len(request.form["password"]) < 8:
		errors.append("Password too short")
	elif request.form["password"] != request.form["confirm"]:
		errors.append("Passwords don't match")

	if errors:
		for error in errors:
			flash(error)
		return redirect("/")
	else:
		query = "INSERT INTO users (first_name, last_name, username, password, created_at, updated_at) VALUES (:first_name, :last_name, :username, :password, NOW(), NOW())"
		data = {
			"first_name": request.form["first_name"],
			"last_name": request.form["last_name"],
			"username": request.form["username"],
			"password": bcrypt.generate_password_hash(request.form["password"])
			}
		session["user_id"] = mysql.query_db(query, data)

		return redirect("/wall")

@app.route("/login", methods=["POST"])
def login():
	query = "SELECT * FROM users WHERE username=:username LIMIT 1"
	data = {"username": request.form["username"]}

	user = mysql.query_db(query, data)

	if user and bcrypt.check_password_hash(user[0]["password"], request.form["password"]):
		session["user_id"] = user[0]["id"]
		return redirect("/wall")
	else:
		flash("User name or password incorrect")
		return redirect("/")

@app.route("/wall")
def wall():
	if "user_id" not in session:
		return redirect("/")
	else:
		query = "SELECT * FROM users WHERE id=:user_id"
		data = {"user_id": session["user_id"]}
		user = mysql.query_db(query, data)[0]

	query = "SELECT messages.message, users.first_name, users.last_name, messages.id, messages.created_at, users.id as user_id FROM messages LEFT JOIN users ON messages.user_id=users.id"
	messages = mysql.query_db(query)[::-1]

	query = "SELECT users.first_name, users.last_name, comments.message_id, comments.comment, comments.created_at FROM comments LEFT JOIN users ON users.id=comments.user_id"
	comments = mysql.query_db(query)


	return render_template("wall.html", user=user, messages=messages, comments=comments)

@app.route("/message", methods=["POST"])
def post_message():
	if not request.form["message"] or "user_id" not in session:
		return redirect("/wall")

	query = "INSERT INTO messages (message, user_id, created_at, updated_at) VALUES (:message, :user_id, NOW(), NOW())"
	data = {
		"message": request.form["message"],
		"user_id": session["user_id"],
	}

	mysql.query_db(query, data)
	return redirect("/wall")

@app.route("/comment", methods=["POST"])
def comment():
	if not request.form["comment"] or not request.form["message_id"] or "user_id" not in session:
		return redirect("/wall")

	query = "INSERT INTO comments (comment, message_id, user_id, created_at, updated_at) VALUES (:comment, :message_id, :user_id, NOW(), NOW())"
	data = {
		"comment": request.form["comment"],
		"message_id": request.form["message_id"],
		"user_id": session["user_id"]
	}

	mysql.query_db(query, data)

	return redirect("/wall")

@app.route("/delete/<message_id>", methods=["POST"])
def delete_message(message_id):
	message = mysql.query_db("SELECT * FROM messages WHERE id=:id LIMIT 1", {"id": message_id})
	if not message:
		return redirect("/wall")
	else:
		message = message[0]

	if message["user_id"] != session["user_id"]:
		return redirect('/wall')

	query = "DELETE FROM comments WHERE message_id=:message_id"
	data = {"message_id": message_id}
	mysql.query_db(query, data)

	query = "DELETE FROM messages WHERE id=:message_id"
	mysql.query_db(query, data)

	return redirect("/wall")



app.run(debug=True)