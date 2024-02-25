from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import csv
import openpyxl
import os.path

client = MongoClient('mongodb://localhost:27017/')
db = client['my_database']

current_user = None

def main_menu():
    global current_user
    while True:
        print("\nWelcome to the CRUD Application")
        print("1. Register")
        print("2. Login")
        print("3. Post a Message")
        print("4. Search Messages")
        print("5. Update User Information")
        print("6. Exit")

        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            register_user()
        elif choice == '2':
            current_user = user_login()
        elif choice == '3' and current_user:
            post_message_to_wall()
        elif choice == '4':
            title = input("Enter title to search for: ")
            search_for_message_by_title(title)
        elif choice == '5' and current_user:
            update_user_info()
        elif choice == '6':
            print("Thank you for using the application.")
            break
        else:
            print("Invalid choice. Please choose again.")

def register_user():
    username = input("Enter username: ")
    password = input("Enter password: ")
    first_name = input("Enter first name: ")
    last_name = input("Enter last name: ")
    address = input("Enter address: ")
    phone_number = input("Enter phone number: ")

    user = {
        "username": username,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "address": address,
        "phone_number": phone_number
    }
    db.users.insert_one(user)
    print("User registered successfully.")

def user_login():
    username = input("Enter username: ")
    password = input("Enter password: ")
    user = db.users.find_one({"username": username, "password": password})

    if user:
        print("Login successful")
        log_to_csv(username)
        log_to_mongodb(username)
        update_login_history_excel()  # Update login history when user logs in
        return username
    else:
        print("Login failed")
        return None
    
def log_to_csv(username):
    df = pd.DataFrame({'username': [username], 'login_time': [datetime.now()]})
    df.to_csv('user login.csv', mode='a', header=False)

def log_to_mongodb(username):
    login_record = {
        "username": username,
        "login_time": datetime.now()
    }
    db.login_records.insert_one(login_record)
    print("Login record logged to MongoDB.")

def update_login_history_excel():
    pipeline = [
        {"$group": {
            "_id": {
                "year": {"$year": "$login_time"},
                "month": {"$month": "$login_time"},
                "day": {"$dayOfMonth": "$login_time"},
                "hour": {"$hour": "$login_time"}
            },
            "count": {"$sum": 1}
        }}
    ]
    results = db.login_records.aggregate(pipeline)
    data = [{
        "Year": result['_id']['year'],
        "Month": result['_id']['month'],
        "Day": result['_id']['day'],
        "Hour": result['_id']['hour'],
        "Logins": result['count']
    } for result in results]

    df = pd.DataFrame(data)

    if not os.path.isfile('login_history.xlsx'):
        df.to_excel('login_history.xlsx', index=False)
    
    with pd.ExcelWriter('login_history.xlsx', engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, index=False)

def post_message_to_wall():
    title = input("Enter the title of your message: ")
    message = input("Enter your message: ")

    message_document = {
        "username": current_user,
        "title": title,
        "message": message,
        "posted_at": datetime.now()
    }
    db.messages.insert_one(message_document)
    print("Message posted successfully.")

def search_for_message_by_title(title):
    results = db.messages.find({"title": {"$regex": title, "$options": "i"}})
    found = False
    for message in results:
        print("\nTitle:", message["title"])
        print("User:", message["username"])
        print("Message:", message["message"])
        found = True

    if not found:
        print("No messages found with that title.")

def update_user_info():
    if not current_user:
        print("You need to be logged in to update your information.")
        return

    # User selects which information to update
    print("\nWhat would you like to update?")
    print("1. First Name")
    print("2. Last Name")
    print("3. Password")
    print("4. Address")
    print("5. Phone Number")
    update_choice = input("Enter your choice (1-5): ")

    update_field = None
    update_value = None

    if update_choice == '1':
        update_field = "first_name"
        update_value = input("Enter new first name: ")
    elif update_choice == '2':
        update_field = "last_name"
        update_value = input("Enter new last name: ")
    elif update_choice == '3':
        update_field = "password"
        update_value = input("Enter new password: ")
    elif update_choice == '4':
        update_field = "address"
        update_value = input("Enter new address: ")
    elif update_choice == '5':
        update_field = "phone_number"
        update_value = input("Enter new phone number: ")
    else:
        print("Invalid choice. Please choose again.")
        return

    if update_field and update_value:
        db.users.update_one({"username": current_user}, {"$set": {update_field: update_value}})
        print("User information updated successfully.")


if __name__ == "__main__":
    main_menu()
