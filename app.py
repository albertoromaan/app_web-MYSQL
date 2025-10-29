from flask import Flask, render_template, request, redirect, session
import mysql.connector

app = Flask(__name__)
app.secret_key = "clave123"  
HOST = "192.168.122.85"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            conn = mysql.connector.connect(host=HOST, user=username, password=password)
            conn.close()
            session["username"] = username
            session["password"] = password
            return redirect("/databases")
        except mysql.connector.Error:
            return render_template("login.html", error="Usuario o contraseña incorrectos")

    return render_template("login.html", error=None)

@app.route("/databases")
def databases():
    if "username" not in session:
        return redirect("/")

    try:
        conn = mysql.connector.connect(
            host=HOST,
            user=session["username"],
            password=session["password"]
        )
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        dbs = [db[0] for db in cursor.fetchall()]
        cursor.close()
        conn.close()
        return render_template("databases.html", databases=dbs)
    except mysql.connector.Error as err:
        return f"Error: {err}"

@app.route("/database/<db_name>/tables", methods=["GET", "POST"])
def tables(db_name):
    if "username" not in session:
        return redirect("/")

    try:
        conn = mysql.connector.connect(
            host=HOST,
            user=session["username"],
            password=session["password"],
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables_list = [table[0] for table in cursor.fetchall()]

        searched_tables = None
        error = None
        if request.method == "POST":
            table_name = request.form.get("table_name", "").strip()

            base_query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_name = %s
            """
            cursor.execute(base_query, (db_name, table_name))
            searched_tables = [row[0] for row in cursor.fetchall()]

            if not searched_tables:
                error = f"No se encontró la tabla '{table_name}'."

        cursor.close()
        conn.close()
        return render_template(
            "tables.html",
            db_name=db_name,
            tables=tables_list,
            searched_tables=searched_tables,
            error=error
        )
    except mysql.connector.Error as err:
        return render_template("tables.html", db_name=db_name, tables=[], searched_tables=None, error=str(err))

@app.route("/database/<db_name>/table/<table_name>")
def table_data(db_name, table_name):
    if "username" not in session:
        return redirect("/")

    try:
        conn = mysql.connector.connect(
            host=HOST,
            user=session["username"],
            password=session["password"],
            database=db_name
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM `{table_name}`")
        data = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        cursor.close()
        conn.close()
        return render_template("table_data.html", db_name=db_name, table_name=table_name, columns=columns, data=data)
    except mysql.connector.Error as err:
        return f"Error: {err}"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
