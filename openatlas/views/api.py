# Created by Alexander Watzinger and others. Please see README.md for licensing information


from flask import render_template, json, request, url_for

from openatlas import app
from openatlas.models.entity import EntityMapper
from openatlas.models.gis import GisMapper
from openatlas.models.geonames import GeonamesMapper
from openatlas.util.util import required_group


@app.route('/api/<version>/entity/<int:id_>')
@required_group('manager')
def api_entity(version: str, id_: int) -> str:
    entity = EntityMapper.get_by_id(id_, nodes=True, aliases=True)
    # gis = GisMapper.get_all(entity)
    # location = entity.get_linked_entity('P53', nodes=True)
    # geonames = GeonamesMapper.get_geonames_link(entity)
    data = {
        "type": "FeatureCollection",
        "@context": request.base_url,
        "feature": [
            {
                "@id": url_for('place_view', id_=entity.id, _external=True),  # To Do: make dynamic
                "type": entity.system_type,  # To Do: get type
                "properties": {
                    "title": entity.name
                },
                "geometry": {
                    "type": "GeometryCollection",
                    "geometries": [
                        {
                            "type": "Point",
                            "coordinates": [
                                15.643286705017092,
                                48.586735522177
                            ],
                            "classification": "centerpoint",
                            "description": "Point in the center of the cemetery",
                            "title": "Thunau centerpoint"
                        }
                    ]
                },
                # "when": {
                #     "timespans": [
                #         {
                #             "start": {
                #                 "earliest": entity.begin_from,
                #                 "latest": entity.begin_to,
                #                 # Hab ich hinzugefügt, müssen wir noch reden ob es klug ist
                #                 "comment": entity.begin_comment
                #             },
                #             "end": {
                #                 "earliest": entity.end_from,
                #                 "latest": entity.end_to,
                #                 # Hab ich hinzugefügt, müssen wir noch reden ob es klug ist
                #                 "comment": entity.end_comment
                #             }
                #         }
                #     ]
                # },
                "names": [
                    {
                        "toponym": entity.name
                    }
                ],
                "types": [
                    {
                        "identifier": "",  # URI vom Type
                        "label": ""  # wie bekomme ich die Types
                    }
                ],
                # "links": [
                #     {
                #         "type": geonames,
                #         "identifier": geonames
                #     }
                # ]
                "relations": [
                    {
                        "relationType": "crm:P2_has_type",
                        "relationTo": "https://thanados.openatlas.eu/api/v01/5099",
                        "label": "Excavation"
                    },
                    {
                        "relationType": "crm:P67i_is_referred_to_by",
                        "relationTo": "https://thanados.openatlas.eu/api/v01/112759",
                        "label": "Nowotny 2018"
                    },
                    {
                        "relationType": "crm:P67i_is_referred_to_by",
                        "relationTo": "https://thanados.openatlas.eu/api/v01/116289",
                        "label": "https://doi.org/10.2307/j.ctv8xnfjn"
                    },
                    {
                        "relationType": "crm:P46_is_composed_of",
                        "relationTo": "https://thanados.openatlas.eu/api/v01/58775",
                        "label": "Grave 001"
                    }
                ],
                "descriptions": [
                    {"@id": "https://thanados.openatlas.eu/api/v01/50505",
                     "value": "...In the area of Obere Holzwiese 215 inhumation burials were documented in different excavations. There might have been a wooden church in the north-western part of the areal, which might date back to the first half of the 9th century..."
                     }
                ],
                "depictions": [
                    {"@id": "https://thanados.openatlas.eu/display/112760.png",
                     "title": "Map of the cemetery",
                     "license": "cc:by-nc-nd/4.0/",
                     "@context": "https://thanados.openatlas.eu/api/v01/112760"
                     }
                ]
            }
        ],

        "Entity": {'id': entity.id, 'name': entity.name}}
    return json.dumps(data)


@app.route('/api')
@required_group('manager')
def api_index() -> str:
    return render_template('api/index.html')
