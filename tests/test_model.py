from typing import Any, Dict

from flask import url_for

from openatlas import app
from openatlas.models.entity import EntityMapper
from tests.base import TestBaseCase


class ModelTests(TestBaseCase):

    def test_model(self) -> None:
        with app.app_context():  # type: ignore
            rv = self.app.get(url_for('model_index'))
            assert b'Browse' in rv.data
            rv = self.app.get(url_for('class_index'))
            assert b'E1' in rv.data
            rv = self.app.get(url_for('class_view', code='E4'))
            assert b'Domain for' in rv.data
            rv = self.app.get(url_for('property_index'))
            assert b'P1' in rv.data
            rv = self.app.get(url_for('property_view', code='P68'))
            assert b'P68' in rv.data
            data: Dict[str, Any] = {'domain': 'E1', 'range': 'E1', 'property': 'P13'}
            rv = self.app.post(url_for('model_index'), data=data)
            assert b'Wrong domain' in rv.data
            data = {'domain': 'E1', 'range': 'E1', 'property': 'P67'}
            self.app.post(url_for('model_index'), data=data)

            self.login()
            with app.test_request_context():  # Insert data to display in network view
                app.preprocess_request()  # type: ignore
                actor = EntityMapper.insert('E21', 'King Arthur')
                event = EntityMapper.insert('E7', 'Battle of Camlann')
                source = EntityMapper.insert('E33', 'Tha source')
                actor.link('P11', event)
                actor.link('P67', EntityMapper.insert('E89', 'Propositional Object'))
                source.link('P67', event)
            rv = self.app.get(url_for('model_network'))
            assert b'orphans' in rv.data
            data = {'orphans': True, 'width': 100, 'height': 40, 'distance': -666, 'charge': 500}
            rv = self.app.post(url_for('model_network'), data=data)
            assert b'666' in rv.data

            # Translations
            self.app.get('/index/setlocale/de')
            rv = self.app.get(url_for('property_view', code='P68'))
            assert b'verweist auf' in rv.data
            rv = self.app.get(url_for('class_view', code='E18'))
            assert b'Materielles' in rv.data
            rv = self.app.get(url_for('property_view', code='P166'))
            assert b'was a presence of' in rv.data
