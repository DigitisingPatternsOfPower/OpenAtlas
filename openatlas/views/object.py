from typing import Any, Optional, Union

from flask import flash, g, render_template, request, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired

from openatlas import app, logger
from openatlas.forms.forms import build_form, build_table_form
from openatlas.models.entity import Entity, EntityMapper
from openatlas.util.table import Table
from openatlas.util.util import (get_base_table_data, link, required_group, truncate_string,
                                 was_modified)


class InformationCarrierForm(FlaskForm):  # type: ignore
    name = StringField(_('name'), [InputRequired()], render_kw={'autofocus': True})
    description = TextAreaField(_('description'))
    save = SubmitField(_('insert'))
    insert_and_continue = SubmitField(_('insert and continue'))
    continue_ = HiddenField()
    opened = HiddenField()


@app.route('/object')
@app.route('/object/<action>/<int:id_>')
@required_group('readonly')
def object_index(action: Optional[str] = None, id_: Optional[int] = None) -> str:
    if id_ and action == 'delete':
        EntityMapper.delete(id_)
        logger.log_user(id_, 'delete')
        flash(_('entity deleted'), 'info')
    table = Table(Table.HEADERS['object'] + ['description'])
    for object_ in EntityMapper.get_by_codes('object'):
        data = get_base_table_data(object_)
        data.append(truncate_string(object_.description))
        table.rows.append(data)
    return render_template('object/index.html', table=table)


@app.route('/object/add/source/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def object_add_source(id_: int) -> Union[str, Response]:
    object_ = EntityMapper.get_by_id(id_, view_name='object')
    if request.method == 'POST':
        if request.form['checkbox_values']:
            object_.link_string('P128', request.form['checkbox_values'])
        return redirect(url_for('entity_view', id_=id_) + '#tab-source')
    form = build_table_form('source', object_.get_linked_entities(['P128']))
    return render_template('add_source.html', entity=object_, form=form)


@app.route('/object/insert', methods=['POST', 'GET'])
@required_group('contributor')
def object_insert() -> Union[str, Response]:
    form = build_form(InformationCarrierForm, 'Information Carrier')
    if form.validate_on_submit():
        return redirect(save(form))
    return render_template('object/insert.html', form=form)


@app.route('/object/update/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def object_update(id_: int) -> Union[str, Response]:
    object_ = EntityMapper.get_by_id(id_, nodes=True, view_name='object')
    form = build_form(InformationCarrierForm, object_.system_type.title(), object_, request)
    if form.validate_on_submit():
        if was_modified(form, object_):  # pragma: no cover
            del form.save
            flash(_('error modified'), 'error')
            modifier = link(logger.get_log_for_advanced_view(object_.id)['modifier'])
            return render_template('object/update.html', form=form, object_=object_,
                                   modifier=modifier)
        save(form, object_)
        return redirect(url_for('entity_view', id_=id_))
    return render_template('object/update.html', form=form, object_=object_)


def save(form: Any, object_: Optional[Entity] = None) -> str:
    g.cursor.execute('BEGIN')
    log_action = 'update'
    try:
        if not object_:
            log_action = 'insert'
            object_ = EntityMapper.insert('E84', form.name.data, 'information carrier')
        object_.name = form.name.data
        object_.description = form.description.data
        object_.update()
        object_.save_nodes(form)
        url = url_for('entity_view', id_=object_.id)
        url = url_for('object_insert') if form.continue_.data == 'yes' else url
        g.cursor.execute('COMMIT')
        logger.log_user(object_.id, log_action)
        flash(_('entity created') if log_action == 'insert' else _('info update'), 'info')
    except Exception as e:  # pragma: no cover
        g.cursor.execute('ROLLBACK')
        logger.log('error', 'database', 'transaction failed', e)
        flash(_('error transaction'), 'error')
        url = url_for('object_index')
    return url
