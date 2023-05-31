from flask import Flask , render_template, request , session
from flask_session import Session
from credentials import *
from flask_mail import Mail , Message
import sqlite3
import random
from binance.client import Client
import pandas as pd

app = Flask(__name__)
app.secret_key = session_secrete_key
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = mail_data['email']
app.config['MAIL_PASSWORD'] = mail_data['password']
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

def send_email(recepient):
    with app.app_context():
        sender = mail_data['email']
        receiver = [recepient]
        global otp
        otp = random.randint(100000,999999)
        session['otp'] = otp
        msg = Message('OTP', sender = sender, recipients = receiver)
        msg.body = f'The one time OTP password is: {otp}'
        mail.send(msg)
        print("Email sent")





@app.route('/')
def homepage():
    return render_template('base.html')


@app.route('/register', methods = ['POST','GET'])
def register():
    return render_template('register.html')

@app.route('/signupcompleted', methods = ['POST','GET'])
def register_():
    if request.method == 'POST':
        username = request.form['original_username']
        email = request.form ['username']
        password = request.form['pswrd']
        confirm_password = request.form['retype_pswrd']

        #connect to the database
        conn = sqlite3.connect('mydatabase.db')
        c = conn.cursor()

        # Check if the email already exists in the database
        c.execute("SELECT COUNT(*) FROM users WHERE email = ?", (email,))
        result = c.fetchone()

        if result[0] > 0:
            conn.close()
            return 'Email already exists'

         # Insert the user data into the database
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        conn.close()
        return render_template('signupcompleted.html')


@app.route('/twofactorauth', methods = ['POST','GET'])
def auth():
    if request.method == 'POST':
        email = request.form ['username']
        password = request.form['pswrd']

         #connect to the database
        conn = sqlite3.connect('mydatabase.db')
        c = conn.cursor()

        # Retrieve the user with the provided email
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        result = c.fetchall()

         #check if the email and password matched with the registered user
        if result:
            for row in result:
                stored_password = row[3]  #password is stored at index 3 in the table
                print(f"entered_Password: {password}, stored_password: {stored_password}")
                if password == stored_password:
                    # Store the email in session
                    session['email'] = email
                    send_email(email)
                    
                    conn.close()
                    return render_template('2FA.html')
                conn.close()
                return 'Invalid Email or password'
        return "No email Found, Retry"

@app.route('/home', methods = ['POST','GET'])
def home():
    if request.method == 'POST':
        entered_otp = request.form['OTP']
        session['otp'] = entered_otp
        print(f"entered_otp: {entered_otp}, stored_otp: {otp}")

        if int(entered_otp) == int(otp):
        
            #Loading dashboard.
            client = Client(API_key, API_Secrete_Key,  testnet= True)

            #get all ticket prices
            tickers = client.get_ticker()
            df = pd.DataFrame(tickers)
            new_df = df[['symbol', 'priceChange', 'prevClosePrice','lastPrice','bidPrice','highPrice','lowPrice','volume']]
            new_df
            ticker_price = client.get_all_tickers()
            price_df = pd.DataFrame(ticker_price)
            merged_df = pd.merge(new_df, price_df, on='symbol')
            merged_df
            dict__ = merged_df.to_dict('records')
            return render_template('dashboard.html', data = dict__)
        else:
            return "The entered OTP doestnot match, try again."
@app.route('/portfolio', methods = ['POST','GET'])
def portfolio():
    email = session['email']
    conn = sqlite3.connect('mydatabase.db')
    c = conn.cursor()
    # Retrieve the sell data for non-matching emails from the database
    c.execute("SELECT symbol, coin_amount, total_price FROM sell WHERE email != ?", (email,))
    sell_data = c.fetchall()
    
    # Calculate sell_total_data
    sell_total_data = 0
    symbol =0
    coin_amount =0
    for record in sell_data:
        symbol = record[0]
        coin_amount = record[1]
        total_price = record[2]
        sell_total_data += coin_amount * total_price

    # Delete the sell data records for non-matching emails
    
    c.execute("DELETE FROM sell WHERE email != ?", (email,))
    conn.commit()

    conn.close()
    return render_template('portfolio.html', sell_total_data=sell_total_data, symbol=symbol, total_coin=coin_amount)


if __name__ == '__main__':
    app.run(debug=True)