from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, String, Integer
from marshmallow import ValidationError
from typing import List, Optional
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://root:pa$$w0rd!@localhost/flask_api_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

user_pet = Table(
    "user_pet",
    Base.metadata,
    Column("user_id", ForeignKey("user_account.id"), primary_key=True),
    Column("pet_id", ForeignKey("pets.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "user_account"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    pets: Mapped[List["pet"]] = relationship(
        "Pet", secondary=user_pet, back_populates="owners"
    )


class Pet(Base):
    __tablename__ = "pets"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    animal: Mapped[str] = mapped_column(String(200), nullable=False)
    owners: Mapped[List["User"]] = relationship(
        "User", secondary=user_pet, back_populates="pets"
    )


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User


class PetSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Pet


# --- --- --- POSTS --- --- ---


@app.route("/users", methods=["POST"])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_user = User(name=user_data["name"], email=user_data["email"])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201


@app.route("/pets", methods=["POST"])
def create_pet():
    try:
        pet_data = pet_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_pet = Pet(name=pet_data["name"], animal=pet_data["animal"])
    db.session.add(new_pet)
    db.session.commit()

    return pet_schema.jsonify(new_pet), 201


@app.route("/users/<int:user_id>/add_pets", methods=["POST"])
def add_pets(user_id):
    user = db.session.get(User, user_id)
    pet_data = request.json

    for id in pet_data["pet_ids"]:
        pet = db.session.get(Pet, id)
        user.pets.append(pet)
        db.session.commit()

    return jsonify({"message": "All pets added!"}), 200


# --- --- --- GETS --- --- ---


@app.route("/users", methods=["GET"])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200


@app.route("/users/<int:id>", methods=["GET"])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200


@app.route("/users/<int:user_id>/add_pet/<int:pet_id>", methods=["GET"])
def adopt_pet(user_id, pet_id):
    user = db.session.get(User, user_id)
    pet = db.session.get(Pet, pet_id)

    users.pets.append(pet)
    db.sesion.commit()
    return (
        jsonify({"message": f"{user.name} adopted the {pet.animal}, {pet.name}!"}),
        200,
    )


# --- --- --- PUTS --- --- ---


@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400

    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    user.name = user_data["name"]
    user.email = user_data["email"]

    db.session.commit()
    return user_schema.jsonify(user), 200


# --- --- --- DELETES --- --- ---


@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"successfully deleted user {id}"}), 200


user_schema = UserSchema()
users_schema = UserSchema(many=True)
pet_schema = PetSchema()
pets_schema = PetSchema(many=True)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
