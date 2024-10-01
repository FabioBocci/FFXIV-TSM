#!/bin/bash

# Aggiorna il repository
echo "Aggiornamento del repository..."
git pull

# Riavvia il servizio Odoo
echo "Riavvio del servizio Odoo..."
sudo systemctl restart odoo

# Aggiorna il database
echo "Aggiornamento del database..."
/opt/odoo/odoo-bin -c /etc/odoo/odoo.conf -d tataru_secret_market -u all

echo "Aggiornamento completato!"
