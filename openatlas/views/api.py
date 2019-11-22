# Created by Alexander Watzinger and others. Please see README.md for licensing information
from flask import json, render_template

from openatlas import app
from openatlas.models.api import Api
from openatlas.util.util import required_group


@app.route('/api/<version>/entity/<int:id_>')
@required_group('manager')
def api_entity(version: str, id_: int) -> str:
    return json.dumps(Api.get_entity(id_))


@app.route('/api')
@required_group('manager')
def api_index() -> str:
    return render_template('api/index.html')
