# Copyright 2017 by Alexander Watzinger and others. Please see README.md for licensing information
from flask import url_for
from openatlas import app, EntityMapper, NodeMapper
from openatlas.models.link import LinkMapper
from openatlas.test_base import TestBaseCase


class InvolvementTests(TestBaseCase):

    def test_involvement(self):
        self.login()
        with app.app_context():
            actor_id = EntityMapper.insert('E21', 'Captain Miller').id
            event_id = EntityMapper.insert('E8', 'Event Horizon').id
            involvement_id = NodeMapper.get_hierarchy_by_name('Involvement').id

            # add involvement
            rv = self.app.get(url_for('involvement_insert', origin_id=actor_id))
            assert b'Involvement' in rv.data
            rv = self.app.post(
                url_for('involvement_insert', origin_id=actor_id),
                data={'event': '[' + str(event_id) + ']', 'activity': 'P11', involvement_id: 8},
                follow_redirects=True)
            assert b'Event Horizon' in rv.data
            rv = self.app.post(
                url_for('involvement_insert', origin_id=event_id),
                data={'actor': '[' + str(actor_id) + ']', 'continue_': 'yes', 'activity': 'P11'},
                follow_redirects=True)
            assert b'Event Horizon' in rv.data

            # update involvement
            link_id = LinkMapper.get_links(event_id, 'P11')[0].id
            rv = self.app.get(url_for('involvement_update', id_=link_id, origin_id=event_id))
            assert b'Captain' in rv.data
            rv = self.app.post(
                url_for('involvement_update', id_=link_id, origin_id=actor_id),
                data={'description': 'Infinite Space - Infinite Terror', 'activity': 'P11'},
                follow_redirects=True)
            assert b'Infinite Space - Infinite Terror' in rv.data