from flask import jsonify, abort
from random import randrange

DATA = [{'id': 1, 'name': 'HVAC 1'}, {'id': 2, 'name': 'HVAC 2'}, {'id': 3, 'name': 'HVAC 3'}]

def hvac_reading_get(id) -> str:
    for hvac in DATA:
        if hvac['id'] == id:
            reading = {}
            reading['id'] = id
            reading['temp'] = randrange(10, 25)
            reading['power_consumption'] = randrange(50, 100)
            return jsonify(reading)
    abort(404)

def list_hvac() -> str:
    return jsonify(DATA)
