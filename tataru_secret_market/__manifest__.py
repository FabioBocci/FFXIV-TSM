# -*- coding: utf-8 -*-
{
    'name': "Tataru's Secret Market",

    'description': """

    """,

    'author': "TSM",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'application',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        "security/security.xml",
        'security/ir.model.access.csv',
        "views/items/items.xml",
        "views/items/item_recipe.xml",
        "views/items/item_availability.xml",
        "views/items/item_transactions.xml",
        "views/general/data_centers.xml",
        "views/general/worlds.xml",
        "views/opportunity/opportunity.xml",
        "scripts/scheduler.xml",
        "views/main.xml",
    ],

    "asserts": {
        "web.assets_backend": [
            "tataru_secret_market/static/src/img/icon.png"
        ]

    }
}
