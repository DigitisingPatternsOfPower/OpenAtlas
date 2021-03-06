from typing import Optional, Union

from flask import flash, g, render_template, request, url_for
from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from werkzeug.utils import redirect
from werkzeug.wrappers import Response
from wtforms import HiddenField, StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired

from openatlas import app, logger
from openatlas.forms.forms import TableMultiField, build_form, build_table_form
from openatlas.models.entity import Entity, EntityMapper
from openatlas.util.table import Table
from openatlas.util.util import get_base_table_data, link, required_group, uc_first, was_modified
from openatlas.views.reference import AddReferenceForm


class SourceForm(FlaskForm):  # type: ignore
    name = StringField(_('name'), [InputRequired()], render_kw={'autofocus': True})
    information_carrier = TableMultiField()
    description = TextAreaField(_('content'))
    save = SubmitField(_('insert'))
    insert_and_continue = SubmitField(_('insert and continue'))
    continue_ = HiddenField()
    opened = HiddenField()


@app.route('/source')
@app.route('/source/<action>/<int:id_>')
@required_group('readonly')
def source_index(action: Optional[str] = None, id_: Optional[int] = None) -> str:
    if id_ and action == 'delete':
        EntityMapper.delete(id_)
        logger.log_user(id_, 'delete')
        flash(_('entity deleted'), 'info')
    table = Table(Table.HEADERS['source'])
    for source in EntityMapper.get_by_codes('source'):
        data = get_base_table_data(source)
        table.rows.append(data)
    return render_template('source/index.html', table=table)


@app.route('/source/insert/<int:origin_id>', methods=['POST', 'GET'])
@app.route('/source/insert', methods=['POST', 'GET'])
@required_group('contributor')
def source_insert(origin_id: Optional[int] = None) -> Union[str, Response]:
    origin = EntityMapper.get_by_id(origin_id) if origin_id else None
    form = build_form(SourceForm, 'Source')
    if origin:
        del form.insert_and_continue
    if form.validate_on_submit():
        return redirect(save(form, origin=origin))
    if origin and origin.class_.code == 'E84':
        form.information_carrier.data = [origin_id]
    return render_template('source/insert.html', form=form, origin=origin)


@app.route('/source/add/<int:id_>/<class_name>', methods=['POST', 'GET'])
@required_group('contributor')
def source_add(id_: int, class_name: str) -> Union[str, Response]:
    source = EntityMapper.get_by_id(id_, view_name='source')
    if request.method == 'POST':
        if request.form['checkbox_values']:
            source.link_string('P67', request.form['checkbox_values'])
        return redirect(url_for('entity_view', id_=source.id) + '#tab-' + class_name)
    form = build_table_form(class_name, source.get_linked_entities('P67'))
    return render_template('source/add.html', source=source, class_name=class_name, form=form)


@app.route('/source/add/reference/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def source_add_reference(id_: int) -> Union[str, Response]:
    source = EntityMapper.get_by_id(id_, view_name='source')
    form = AddReferenceForm()
    if form.validate_on_submit():
        source.link_string('P67', form.reference.data, description=form.page.data, inverse=True)
        return redirect(url_for('entity_view', id_=id_) + '#tab-reference')
    form.page.label.text = uc_first(_('page / link text'))
    return render_template('add_reference.html', entity=source, form=form)


@app.route('/source/add/file/<int:id_>', methods=['GET', 'POST'])
@required_group('contributor')
def source_add_file(id_: int) -> Union[str, Response]:
    source = EntityMapper.get_by_id(id_, view_name='source')
    if request.method == 'POST':
        if request.form['checkbox_values']:
            source.link_string('P67', request.form['checkbox_values'], inverse=True)
        return redirect(url_for('entity_view', id_=id_) + '#tab-file')
    form = build_table_form('file', source.get_linked_entities('P67', inverse=True))
    return render_template('add_file.html', entity=source, form=form)


@app.route('/source/update/<int:id_>', methods=['POST', 'GET'])
@required_group('contributor')
def source_update(id_: int) -> Union[str, Response]:
    source = EntityMapper.get_by_id(id_, nodes=True, view_name='source')
    form = build_form(SourceForm, 'Source', source, request)
    if form.validate_on_submit():
        if was_modified(form, source):  # pragma: no cover
            del form.save
            flash(_('error modified'), 'error')
            modifier = link(logger.get_log_for_advanced_view(source.id)['modifier'])
            return render_template('source/update.html', form=form, source=source,
                                   modifier=modifier)
        save(form, source)
        return redirect(url_for('entity_view', id_=id_))
    form.information_carrier.data = [entity.id for entity in
                                     source.get_linked_entities('P128', inverse=True)]
    return render_template('source/update.html', form=form, source=source)


def save(form: FlaskForm, source: Optional[Entity] = None, origin: Optional[Entity] = None) -> str:
    g.cursor.execute('BEGIN')
    log_action = 'update'
    try:
        if not source:
            source = EntityMapper.insert('E33', form.name.data, 'source content')
            log_action = 'insert'
        url = url_for('entity_view', id_=source.id)
        source.name = form.name.data
        source.description = form.description.data
        source.update()
        source.save_nodes(form)

        # Information carrier
        source.delete_links(['P128'], inverse=True)
        if form.information_carrier.data:
            source.link_string('P128', form.information_carrier.data, inverse=True)

        if origin:
            url = url_for('entity_view', id_=origin.id) + '#tab-source'
            if origin.view_name == 'reference':
                link_id = origin.link('P67', source)[0]
                url = url_for('reference_link_update', link_id=link_id, origin_id=origin)
            elif origin.view_name == 'file':
                origin.link('P67', source)
            elif origin.class_.code != 'E84':
                source.link('P67', origin)
        g.cursor.execute('COMMIT')
        if form.continue_.data == 'yes':
            url = url_for('source_insert', origin_id=origin.id if origin else None)
        logger.log_user(source.id, log_action)
        flash(_('entity created') if log_action == 'insert' else _('info update'), 'info')
    except Exception as e:  # pragma: no cover
        g.cursor.execute('ROLLBACK')
        logger.log('error', 'database', 'transaction failed', e)
        flash(_('error transaction'), 'error')
        url = url_for('source_insert', origin_id=origin.id if origin else None)
    return url
