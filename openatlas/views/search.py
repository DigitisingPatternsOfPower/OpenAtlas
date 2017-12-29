# Copyright 2017 by Alexander Watzinger and others. Please see README.md for licensing information
from flask import render_template, request
from flask_babel import lazy_gettext as _
from flask_wtf import Form
from wtforms import SubmitField, StringField, SelectMultipleField, widgets, BooleanField
from wtforms.validators import InputRequired

from openatlas import app, EntityMapper
from openatlas.util.util import link, uc_first, truncate_string, required_group


class SearchForm(Form):
    term = StringField('', [InputRequired()], render_kw={"placeholder": uc_first(_('search term'))})
    own = BooleanField(_('Only entities edited by me'))
    desc = BooleanField(_('Also search in description'))
    classes = SelectMultipleField(
        _('classes'),
        [InputRequired()],
        choices=(),
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False))
    search = SubmitField('Search')


@app.route('/overview/search', methods=['POST', 'GET'])
@required_group('editor')
def index_search():
    classes = ['source', 'event', 'actor', 'place', 'reference']
    form = SearchForm()
    form.classes.choices = [(x, uc_first(_(x))) for x in classes]
    form.classes.default = classes
    form.classes.process(request.form)
    table = {'data': []}
    if request.method == 'POST' and 'global-term' in request.form and request.form['global-term']:
        # coming from global search
        form.term.data = request.form['global-term']
        form.classes.data = classes
        table = build_search_table(form)
    if form.validate_on_submit():
        table = build_search_table(form)
    return render_template('search/index.html', form=form, table=table)


def build_search_table(form):
    table = {
        'name': 'search',
        'header': ['name', 'class', 'first', 'last', 'description'],
        'data': []}
    codes = []
    for name in form.classes.data:
        codes += app.config['CLASS_CODES'][name]
        if name == 'actor':
            codes.append('E82')
        if name == 'place':
            codes.append('E41')
    for entity in EntityMapper.search(form.term.data, codes, form.desc.data, form.own.data):
        table['data'].append([
            link(entity),
            entity.class_.name,
            entity.first,
            entity.last,
            truncate_string(entity.description)])
    return table