from flask import url_for

from openatlas import app
from openatlas.models.entity import EntityMapper
from tests.base import TestBaseCase


class TranslationTest(TestBaseCase):

    def test_source(self) -> None:
        with app.app_context():
            self.login()
            with app.test_request_context():
                app.preprocess_request()
                source = EntityMapper.insert('E33', 'Necronomicon', 'source content')
            rv = self.app.get(url_for('translation_insert', source_id=source.id))
            assert b'+ Text' in rv.data
            data = {'name': 'Test translation'}
            rv = self.app.post(url_for('translation_insert', source_id=source.id), data=data)
            with app.test_request_context():
                app.preprocess_request()
                translation_id = rv.location.split('/')[-1]
            rv = self.app.get(url_for('entity_view', id_=source.id))
            assert b'Test translation' in rv.data
            self.app.get(url_for('translation_update', id_=translation_id, source_id=source.id))
            rv = self.app.post(
                url_for('translation_update', id_=translation_id, source_id=source.id),
                data={'name': 'Translation updated'},
                follow_redirects=True)
            assert b'Translation updated' in rv.data
            rv = self.app.get(
                url_for('translation_delete', id_=translation_id, source_id=source.id),
                follow_redirects=True)
            assert b'The entry has been deleted.' in rv.data
            data = {'name': 'Translation continued', 'continue_': 'yes'}
            self.app.post(url_for('translation_insert', source_id=source.id), data=data)