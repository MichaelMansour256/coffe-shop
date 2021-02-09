import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()


@app.route('/drinks')
def get_drinks():

    try:

        drinks = Drink.query.all()
        drinks_list=[d.short() for d in drinks]
        return jsonify({
            'success': True,
            'drinks': drinks_list
        }), 200
    except BaseException:
        abort(500)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):

    try:

        drinks = Drink.query.all()
        drinks_list=[d.long() for d in drinks]
        return jsonify({
            'success': True,
            'drinks': drinks_list
        }), 200
    except BaseException:
        abort(500)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):

    body = request.get_json()

    if 'title' not in body or 'recipe' not in body:
        abort(422)

    title = body['title']
    recipe = body['recipe']

    if not isinstance(recipe, list):
        abort(422)

    for ingredient in recipe:
        if 'color' not in ingredient or 'name' not in ingredient or 'parts' not in ingredient:
            abort(422)

    recipe = json.dumps(recipe)

    try:

        new_drink = Drink(title=title, recipe=recipe)
        new_drink.insert()
        drink = [new_drink.long()]
        return jsonify({
            'success': True,
            'drinks': drink
        }), 200
    except BaseException:
        abort(422)


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):

    drink = Drink.query.get(id)

    if drink is None:
        abort(404)

    body = request.get_json()
    if 'title' not in body and 'recipe' not in body:
        abort(422)

    title = body.get('title')
    recipe = body.get('recipe')

    if title is not None:
        drink.title = title

    if recipe is not None:

        if not isinstance(recipe, list):
            abort(422)

        for ingredient in recipe:
            if 'color' not in ingredient or 'name' not in ingredient or 'parts' not in ingredient:
                abort(422)

        recipe = json.dumps(recipe)
        drink.recipe = recipe

    try:

        drink.update()
        drink=[drink.long()]
        return jsonify({
            'success': True,
            'drinks': drink
        }), 200
    except BaseException:
        abort(422)


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    """ Delete a drink. Needs delete:drinks permission """
    drink = Drink.query.get(id)

    if not drink:
        abort(404)

    try:

        drink.delete()
        return jsonify({
            'success': True,
            'delete': id
        }), 200
    except BaseException:
        abort(422)


#  ####### Error Handling #########


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Resource Not Found'
    }), 404


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'Not Processable'
    }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'Bad Request'
    }), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'Internal Server Error'
    }), 500


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'Method Not Allowed'
    }), 405


@app.errorhandler(AuthError)
def auth_error(e):

    return jsonify({
        'success': False,
        'error': e.status_code,
        'message': e.error['description']
    }), e.status_code
