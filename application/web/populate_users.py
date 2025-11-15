#!/usr/bin/python
#
# from werkzeug.security import generate_password_hash
# from pymongo import MongoClient
# from pymongo.errors import DuplicateKeyError
#
#
# def populate_user(client, user, password):
#     # Connect to the DB
#     # collection = MongoClient()["crawler"]["users"]
#
#     # Ask for data to store
#     user = user
#     password = password
#     pass_hash = generate_password_hash(password, method='pbkdf2:sha256')
#
#     # Insert the user in the DB
#     try:
#         client.insert({"_id": user, "password": pass_hash})
#         print ("User created.")
#     except DuplicateKeyError:
#         print ("User already present in DB.")
#

# if __name__ == '__main__':
#     main()
