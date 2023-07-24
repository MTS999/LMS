from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

app = Flask(__name__)
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user1'
app.config['MYSQL_PASSWORD'] = 'Password!!!....123'
app.config['MYSQL_DB'] = 'lms1'

mysql = MySQL(app)

# Set the secret key for session management
app.secret_key = '00000'


@app.route('/')
def home():
    error = request.args.get('error')
    return render_template("login.html", error=error)


@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    connection = mysql.connection
    cursor = connection.cursor()

    query = f"CALL Librarian_login('{username}', '{password}');"
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        librarian_info_query = f"CALL Librarian_info('{result[0]}', @FName, @LName, @Email, @PNumber)"
        cursor.execute(librarian_info_query)

        cursor.execute("SELECT @FName, @LName, @Email, @PNumber")
        admin_info = cursor.fetchone()

        session['librarian_info'] = admin_info
        
        get_books_query = "SELECT * FROM Book"
        cursor.execute(get_books_query)
        books = cursor.fetchall()
        
        return render_template('librarian.html', fName=admin_info[0], lName=admin_info[1], email=admin_info[2], pNumber=admin_info[3], books=books)

    query = f"CALL LibraryMember_login('{username}', '{password}');"
    cursor.execute(query)
    result = cursor.fetchone()

    if result:
        member_info_query = f"CALL LibraryMember_info('{result[0]}',@FName, @LName, @Email, @PNumber)"
        cursor.execute(member_info_query)
        cursor.execute("SELECT @FName, @LName, @Email, @PNumber")
        member_info = cursor.fetchone()
        session['member_id'] = result[0]
        # Store the member Info in session
        session['member_info'] = member_info
        get_books_query = "SELECT * FROM Book WHERE Status = 'Available'"
        cursor.execute(get_books_query)
        a_books = cursor.fetchall()
        print(a_books)
        return render_template('member.html', fName=member_info[0], lName=member_info[1], email=member_info[2], pNumber=member_info[3],a_books=a_books)

    else:
        return redirect(url_for('home', error="Login unsuccessful!"))

    cursor.close()

@app.route('/logout', methods=['POST'])
def logout():
  
    return redirect(url_for('home'))

@app.route('/member', methods=['GET', 'POST'])
def member():
    connection = mysql.connection
    cursor = connection.cursor()

    
    book_name = request.form.get('book_name')
    search_query = f"CALL SearchBook('{book_name}')"
    cursor.execute(search_query)
    books = cursor.fetchall()
    member_info = session.get('member_info')

        # member_info = session.get('member_info')
    return render_template('member.html', fName=member_info[0], lName=member_info[1], email=member_info[2],pNumber=member_info[3], books=books)


   



@app.route('/search_results', methods=['GET'])
def search_results():
    connection = mysql.connection
    cursor = connection.cursor()
    book_name = request.args.get('book_name')

    if book_name:
        search_query = f"CALL SearchBook('{book_name}')"
        cursor.execute(search_query)
        books = cursor.fetchall()
       
        member_info = session.get('member_info')

        print(books)
        return render_template('member.html', fName=member_info[0], lName=member_info[1], email=member_info[2],pNumber=member_info[3], books=books)
    else:
        return redirect(url_for('home'))


@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form.get('username')
    password = request.form.get('password')
    firstname = request.form.get('firstname')
    lastname = request.form.get('lastname')
    email = request.form.get('email')
    phone = request.form.get('phone')

    connection = mysql.connection
    cursor = connection.cursor()
    
    username_query = "SELECT COUNT(*) FROM LibraryMember WHERE Username = %s"
    cursor.execute(username_query, (username,))
    
    username_count = cursor.fetchone()[0]

    if username_count > 0:
        cursor.close()
        return "Username already exists. Please choose a different username."
    query = "CALL AddLibraryMember(%s, %s, %s, %s, %s, %s)"
    values = (username, password, firstname, lastname, email, phone)
    cursor.execute(query, values)
    connection.commit()

    cursor.close()

    return redirect(url_for('home'))


@app.route('/add_book', methods=['POST'])
def add_book():
    isbn = request.form.get('isbn')
    title = request.form.get('title')
    publisher = request.form.get('publisher')
    edition = request.form.get('edition')
    author = request.form.get('author')
    year = request.form.get('year')
    # status = request.form.get('status')

    connection = mysql.connection
    cursor = connection.cursor()

    # Call the procedure to add a new book
    add_book_query = f"CALL AddBook('{isbn}', '{title}', '{publisher}', '{edition}', '{author}', {year})"
    cursor.execute(add_book_query)
    connection.commit()

    # Retrieve the updated book info from the database
    get_books_query = "SELECT * FROM Book"
    cursor.execute(get_books_query)
    books = cursor.fetchall()

    cursor.close()

    admin_info = session.get('librarian_info')
    
    # Redirect back to the admin page with the updated book info
    return render_template('librarian.html', fName=admin_info[0], lName=admin_info[1], email=admin_info[2], pNumber=admin_info[3], books=books)
@app.route('/available_books', methods=['GET'])
def available_books():
    connection = mysql.connection
    cursor = connection.cursor()
    get_books_query = "SELECT * FROM Book WHERE status = 'Available'"
    cursor.execute(get_books_query)
    available_books = cursor.fetchall()
    admin_info = session.get('librarian_info')

    # Render the library member template with the available book list
    return render_template('librarian.html', fName=admin_info[0], lName=admin_info[1], email=admin_info[2], pNumber=admin_info[3], books=available_books)


@app.route('/commit_issue_request', methods=['POST'])
def commit_issue_request():
    connection = mysql.connection
    cursor = connection.cursor()
    member_info = session.get('member_info')
    book_id = request.form['book_id']  # Retrieve the book ID from the form submission
    member_id = session.get('member_id')

    update_book_status_query = "CALL update_bookStatus(%s)"
    cursor.execute(update_book_status_query, (int(book_id),))
    connection.commit()

    insert_issuance_query = "CALL InsertIssuance(%s, %s, %s, %s)"
    cursor.execute(insert_issuance_query, (int(book_id), member_id, '2023-06-24', '2023-07-24'))
    connection.commit()
    
    get_books_query = "SELECT * FROM Book WHERE Status = 'Available'"
    cursor.execute(get_books_query)
    a_books = cursor.fetchall()
    # Redirect to the Member Page
    return render_template('member.html', fName=member_info[0], lName=member_info[1], email=member_info[2], pNumber=member_info[3], book_id=book_id,a_books=a_books)





@app.route('/pending_request', methods=['GET'])


def pending_request():

    connection = mysql.connection
    cursor = connection.cursor()
    cursor.callproc('pending_request')
    result = cursor.fetchall()
    cursor.close()
    admin_info = session.get('librarian_info')
    print(result)
    # Render the library member template with the available book list
    return render_template('librarian.html', fName=admin_info[0], lName=admin_info[1], email=admin_info[2], pNumber=admin_info[3], pending_book=result,books=None)

@app.route('/issued_books', methods=['GET'])
def issued_books():

    connection = mysql.connection
    cursor = connection.cursor()
    cursor.callproc('Issued_books')
    result = cursor.fetchall()
    cursor.close()
    admin_info = session.get('librarian_info')
    print(result)
    # Render the library member template with the available book list
    return render_template('librarian.html', fName=admin_info[0], lName=admin_info[1], email=admin_info[2], pNumber=admin_info[3], pending_book=result,books=None)

@app.route('/request_accept', methods=['POST'])
def request_accept():
    connection = mysql.connection
    cursor = connection.cursor()
    member_info = session.get('member_info')
    book_id = request.form['book_id']  # Retrieve the book ID from the form submission
    # member_id = session.get('member_id')

    update_book_status_query = "CALL issue_book(%s)"
    cursor.execute(update_book_status_query, (int(book_id),))
    connection.commit()
    cursor.callproc('pending_request')
    result = cursor.fetchall()
    cursor.close()

    # Redirect to the Member Page
    return render_template('librarian.html', fName=member_info[0], lName=member_info[1], email=member_info[2], pNumber=member_info[3], pending_book=result,books=None)
@app.route('/request_reject', methods=['POST'])
def request_reject():
    connection = mysql.connection
    cursor = connection.cursor()
    member_info = session.get('member_info')
    book_id = request.form['book_id']  # Retrieve the book ID from the form submission
    # member_id = session.get('member_id')

    update_book_status_query = "CALL reject_request(%s)"
    cursor.execute(update_book_status_query, (int(book_id),))
    connection.commit()
    cursor.callproc('pending_request')
    result = cursor.fetchall()
    cursor.close()

    # Redirect to the Member Page
    return render_template('librarian.html', fName=member_info[0], lName=member_info[1], email=member_info[2], pNumber=member_info[3], pending_book=result,books=None)
if __name__ == '__main__':
    app.run(debug=True)
