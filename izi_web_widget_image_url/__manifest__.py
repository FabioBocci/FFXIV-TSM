# -*- coding: utf-8 -*-
# Copyright 2023 IZI PT Solusi Usaha Mudah
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
# noinspection PyUnresolvedReferences,SpellCheckingInspection
{
    "name": """Show Image from URL""",
    "summary": """Show image from URL""",
    "category": "User Interface",
    "version": "16.0.0.1.0",
    "development_status": "Alpha",  # Options: Alpha|Beta|Production/Stable|Mature
    "auto_install": False,
    "installable": True,
    "application": False,
    "author": "IZI PT Solusi Usaha Mudah",
    "support": "apps@iziapp.id",
    # "website": "https://iziapp.id",
    "license": "OPL-1",
    "images": [
        'images/main_screenshot.png'
    ],

    # "price": 10.00,
    # "currency": "USD",

    "depends": [
        # odoo addons
        'base',
        # third party addons

        # developed addons
    ],
    "assets": {
        "web.assets_backend": [
            "/izi_web_widget_image_url/static/src/js/web_widget_image_url.js",
        ],
        "web.assets_qweb": [
            "/izi_web_widget_image_url/static/src/xml/web_widget_image_url.xml"
        ],
    },
    "post_load": None,
    # "pre_init_hook": "pre_init_hook",
    # "post_init_hook": "post_init_hook",
    "uninstall_hook": None,
}
