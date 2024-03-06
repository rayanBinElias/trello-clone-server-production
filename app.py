from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
import os, json
from dotenv import load_dotenv
from pymongo import MongoClient
from rich import print
from bson import json_util
from bson.objectid import ObjectId
from flask_bcrypt import Bcrypt

from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager


# app instance
app = Flask(__name__)
CORS(app)  # Enables cors to all route
bcrypt = Bcrypt(app)

# Load config from a .env file:
load_dotenv()
MONGODB_URI = os.environ["MONGODB_URI_ATLAS"]
JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
jwt = JWTManager(app)

# Connect to your MongoDB cluster:
client = MongoClient(MONGODB_URI)

# List all the databases in the cluster:
print("\n----")
print("Databases are:\n")
for db_info in client.list_database_names():
    print(db_info)

# Get a reference to the 'trello-clone' database:
db = client["trello-clone"]

# List all collections in terminal
collections = db.list_collection_names()
print("\n----")
print("Collections are:\n")
for collection in collections:
    print(collection)


# initilaize collection to login credentials storage
login = db["login"]

# initilaize collection to user profile
users = db["users"]

# initilaize collection to todos task
todos = db["todos"]


# List all documents in terminal
print("\n----")
print("Documents are:\n")
document = todos.find({})
for doc in document:
    print(doc)


# Route endpoint to list all documents
@app.route("/", methods=["GET"])
def connect():
    try:
        return Response(
            response=json.dumps({"message": "Server and Database Activated"}),
            status=200,
            mimetype="application/json",
        )

    except Exception as ex:
        print("--------")
        print(ex)
        print("--------")

        return Response(
            response=json.dumps(
                {"message": "Please run the server Again and fix the error: " + ex}
            ),
            status=500,
            mimetype="application/json",
        )


# Route endpoint to list all documents
@app.route("/todos", methods=["GET"])
def list_all():
    documents = todos.find({})
    return json.loads(json_util.dumps(list(documents)))


# Route endpoint to create one document
@app.route("/create", methods=["POST"])
def create_doc():
    title = request.json["title"]
    status = request.json["status"]
    if "image" in request.json:
        image = request.json["image"]
    else:
        image = ""

    doc_create = todos.insert_one(
        {
            "status": status,
            "title": title,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "image": image,
        }
    )
    return jsonify({"id": f"{doc_create.inserted_id}"})


# Route endpoint to list one document
@app.route("/todos/<id>", methods=["GET"])
def list_doc(id):
    document = todos.find({"_id": ObjectId(id)})
    return json.loads(json_util.dumps(document))
    # return json.loads(json_util.dumps(title[0]["title"]))


# # Route endpoint to list one document
# @app.route("/todos/<id>", methods=["GET"])
# def list_doc(id):
#     user = users.find({"_id": ObjectId(id)})
#     return json.loads(json_util.dumps(user[0]["password"]))
# return json.loads(json_util.dumps(title[0]["title"]))


# Route endpoint to modify to do status
@app.route("/todos/update/<id>/<columnId>")
def update_todoStatus(id, columnId):
    try:
        queryId = {"_id": ObjectId(id)}
        newStatus = {"$set": {"status": columnId}}
        todos.update_one(queryId, newStatus)

        return Response(
            response=json.dumps(
                {"message": "Document updated successfully", "id": f"{id}"}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as ex:
        print("--------")
        print(ex)
        print("--------")

        return Response(
            response=json.dumps(
                {"message": "Sorry, wrong ID, Please input the right ID"}
            ),
            status=500,
            mimetype="application/json",
        )


# Route endpoint to modify users name
@app.route("/user/update/name", methods=["POST"])
def update_userName():
    try:
        userID = request.json["id"]
        newName = request.json["newName"]
        queryId = {"_id": ObjectId(userID)}
        newStatus = {"$set": {"name": newName}}
        users.update_one(queryId, newStatus)

        return Response(
            response=json.dumps(
                {"message": "Name updated successfully", "id": f"{id}"}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as ex:
        print("--------")
        print(ex)
        print("--------")

        return Response(
            response=json.dumps(
                {"message": "Sorry, wrong ID, Please input the right ID"}
            ),
            status=500,
            mimetype="application/json",
        )


# Route endpoint to delete document
@app.route("/todos/delete/<id>")
def delete_todos(id):
    try:
        dbResponse = todos.delete_one({"_id": ObjectId(id)})
        for attr in dir(dbResponse):
            print(f"***{attr}***")

        return Response(
            response=json.dumps(
                {"message": "Document deleted successfully", "id": f"{id}"}
            ),
            status=200,
            mimetype="application/json",
        )

    except Exception as ex:
        print("--------")
        print(ex)
        print("--------")

        return Response(
            response=json.dumps(
                {"message": "Sorry, wrong ID, Please input the right ID"}
            ),
            status=500,
            mimetype="application/json",
        )


# Route endpoint to store signup information
@app.route("/signup", methods=["POST"])
def create_user():
    name = request.json["name"]
    email = request.json["email"]
    password = request.json["password"]

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    if not email or not name or not password:
        return Response(
            response=json.dumps({"message": "Incorrect submission"}),
            status=500,
            mimetype="application/json",
        )

    else:
        login.insert_one(
            {
                "email": email,
                "password": pw_hash,
            }
        )

        users.insert_one(
            {
                "email": email,
                "name": name,
            }
        )
        user_profile = users.find(
            {
                "email": email,
                "name": name,
            }
        )
        return json.loads(json_util.dumps(user_profile))


# Route endpoint for login authentication
@app.route("/login", methods=["POST"])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user_login = login.find(
        {
            "email": email,
        }
    )

    isValid = bcrypt.check_password_hash(user_login[0]["password"], password)

    if isValid:
        # generate JWT
        access_token = create_access_token(identity=email)
        return jsonify(token=access_token)
    else:
        return jsonify({"message": "Incorrect Username or Password!"})


# Route endpoint for profile user datta with token as an authorization/access ID
@app.route("/user")
@jwt_required()
def profile_user():
    current_user = get_jwt_identity()
    user = users.find(
        {
            "email": current_user,
        }
    )
    return json.loads(json_util.dumps(user))
    # return jsonify(logged_in_as=current_user), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5001)
