# Copyright 2017 by Alexander Watzinger and others. Please see README.md for licensing information
from collections import OrderedDict
from flask import render_template, flash, url_for, request
from flask_babel import lazy_gettext as _
from flask_wtf import Form
from werkzeug.utils import redirect
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import InputRequired

import openatlas
from openatlas import app, NodeMapper, EntityMapper
from openatlas.forms import build_node_form
from openatlas.util.util import required_group, sanitize, link, truncate_string


class NodeForm(Form):
    name = StringField(_('name'), validators=[InputRequired()])
    name_inverse = StringField(_('inverse'))
    description = TextAreaField(_('description'))
    save = SubmitField(_('insert'))


@app.route('/types')
@required_group('readonly')
def node_index():
    nodes = {'system': OrderedDict(), 'custom': OrderedDict(), 'places': OrderedDict()}
    for id_, node in openatlas.nodes.items():
        if not node.root:
            type_ = 'system' if node.system else 'custom'
            type_ = 'places' if node.class_.code == 'E53' else type_
            nodes[type_][node] = tree_select(node.name)
    return render_template('types/index.html', nodes=nodes)


@app.route('/types/insert/<int:root_id>', methods=['POST'])
@required_group('editor')
def node_insert(root_id):
    root = openatlas.nodes[root_id]
    form = build_node_form(NodeForm, root)
    # check if form is valid and if it wasn't a submit of the search form
    if 'name_search' not in request.form and form.validate_on_submit():
        name = form.name.data
        if hasattr(form, 'name_inverse') in form:
            name += ' (' + form.name_inverse.data + ')'
        node = save(form, None, root)
        flash(_('entity created'), 'info')
        return redirect(url_for('node_view', id_=node.id))
    if 'name_search' in request.form:
        form.name.data = request.form['name_search']
    return render_template('types/insert.html', form=form, root=root)


@app.route('/types/update/<int:id_>', methods=['POST', 'GET'])
@required_group('editor')
def node_update(id_):
    node = openatlas.nodes[id_]
    if node.system:
        flash(_('error forbidden'), 'error')
        return redirect(url_for('node_view', id_=id_))
    form = build_node_form(NodeForm, node, request)
    root = openatlas.nodes[node.root[-1]] if node.root else None
    if form.validate_on_submit():
        if save(form, node):
            flash(_('info update'), 'info')
            return redirect(url_for('node_view', id_=id_))
        return render_template('types/update.html', node=node, root=root, form=form)
    return render_template('types/update.html', node=node, root=root, form=form)


@app.route('/types/view/<int:id_>')
@required_group('readonly')
def node_view(id_):
    node = openatlas.nodes[id_]
    root = openatlas.nodes[node.root[-1]] if node.root else None
    super_ = openatlas.nodes[node.root[0]] if node.root else None
    tables = {'entities': {
        'name': 'entities',
        'header': [_('name'), _('class'), _('info')],
        'data': []}}
    for entity in node.get_linked_entities(['P2', 'P89'], True):
        # if its a place location get the corresponding object
        entity = entity if node.class_.code == 'E55' else entity.get_linked_entity('P53', True)
        tables['entities']['data'].append([
            link(entity),
            openatlas.classes[entity.class_.id].name,
            truncate_string(entity.description)])
    tables['subs'] = {
        'name': 'subs',
        'header': [_('name'), _('count'), _('info')],
        'data': []}
    for sub_id in node.subs:
        sub = openatlas.nodes[sub_id]
        tables['subs']['data'].append([
            link(sub),
            sub.count,
            truncate_string(sub.description)])
    return render_template('types/view.html', node=node, super_=super_, tables=tables, root=root)


@app.route('/types/delete/<int:id_>', methods=['POST', 'GET'])
@required_group('editor')
def node_delete(id_):
    node = openatlas.nodes[id_]
    if node.system or node.subs or node.count:
        flash(_('error forbidden'), 'error')
        return redirect(url_for('node_view', id_=id_))
    openatlas.get_cursor().execute('BEGIN')
    EntityMapper.delete(node.id)
    openatlas.get_cursor().execute('COMMIT')
    flash(_('entity deleted'), 'info')
    root = openatlas.nodes[node.root[-1]] if node.root else None
    if root:
        return redirect(url_for('node_view', id_=root.id))
    return redirect(url_for('node_index'))


def walk_tree(param):
    items = param if isinstance(param, list) else [param]
    text = ''
    for id_ in items:
        item = openatlas.nodes[id_]
        count_subs = " (" + str(item.count_subs) + ")" if item.count_subs else ''
        text += "{href: '" + url_for('node_view', id_=item.id) + "',"
        text += "text: '" + item.name + " " + str(item.count) + count_subs
        text += "', 'id':'" + str(item.id) + "'"
        if item.subs:
            text += ",'children' : ["
            for sub in item.subs:
                text += walk_tree(sub)
            text += "]"
        text += "},"
    return text


def tree_select(name):
    tree = "'core':{'data':[" + walk_tree(NodeMapper.get_nodes(name)) + "]}"
    name = sanitize(name)
    html = '<div id="' + name + '-tree"></div>'
    html += '<script>'
    html += '    $(document).ready(function () {'
    html += '        $("#' + name + '-tree").jstree({'
    html += '            "search": {"case_insensitive": true, "show_only_matches": true},'
    html += '            "plugins" : ["core", "html_data", "search"],' + tree + '});'
    html += '        $("#' + name + '-tree-search").keyup(function() {'
    html += '            $("#' + name + '-tree").jstree("search", $(this).val());'
    html += '        });'
    html += '        $("#' + name + '-tree").on("select_node.jstree", '
    html += '           function (e, data) { document.location.href = data.node.original.href; })'
    html += '    });'
    html += '</script>'
    return html


def save(form, node=None, root=None):
    openatlas.get_cursor().execute('BEGIN')
    if not node:
        node = NodeMapper.insert(root.class_.code, form.name.data)
        super_ = 'new'
    else:
        root = openatlas.nodes[node.root[-1]] if node.root else None
        super_ = openatlas.nodes[node.root[0]] if node.root else None
    new_super_id = getattr(form, str(root.id)).data
    new_super = openatlas.nodes[int(new_super_id)] if new_super_id else openatlas.nodes[root.id]
    if new_super.id == node.id:
        flash(_('error node self as super'), 'error')
        return False
    if new_super.root and node.id in new_super.root:
        flash(_('error node sub as super'), 'error')
        return False
    node.name = sanitize(form.name.data, 'node')
    if root.directional and sanitize(form.name_inverse.data, 'node'):
        node.name += ' (' + sanitize(form.name_inverse.data, 'node') + ')'
    node.description = form.description.data
    node.update()
    # update super if changed and node is not a root node
    if super_ and (super_ == 'new' or super_.id != new_super.id):
        property_code = 'P127' if node.class_.code == 'E55' else 'P89'
        node.delete_links(property_code)
        node.link(property_code, new_super.id)
    openatlas.get_cursor().execute('COMMIT')
    return node