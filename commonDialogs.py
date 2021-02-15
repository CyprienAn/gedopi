# -*- coding: utf-8 -*-
'''
This file is a part from the next plugin :
/******************************************************************
Cadastre - Dialog classes
A QGIS plugin
This plugins helps users to import the french land registry ('cadastre')
into a database. It is meant to ease the use of the data in QGIs
by providing search tools and appropriate layer symbology.
-------------------
begin                                : 2013-06-11
copyright                        : (C) 2013 by 3liz
email                                : info@3liz.com
 ******************************************************************
/******************************************************************
 *
 *     This file is free software; you can redistribute it and/or modify
 *     it under the terms of the GNU General Public License as published by
 *     the Free Software Foundation; either version 2 of the License, or
 *     (at your option) any later version.
 *
 *******************************************************************
Ce script permet l'obtetntion des paramétres de connexion à la base de données PostgreSQL liée au plugin.
'''

# Import des modules Python et QGIS nécessaire à l'exécution de ce fichier
import re
import sys
import os
from qgis.core import (QgsMapLayer)

class Gedopi_common():
    def __init__(self, dialog):
        '''
        Constructeur.

        :param dialog: dialog = Class de formulaire(self.iface, self.formulaire_action)
                ex:dialog = Bail_peche_dialog(self.iface, self.bail_peche_action)
                Une instance d'un des 5 formulaires issue du fichier gedopiMenu
                qui sera passée à cette classe qui fournit le crochet par lequel
                ce scrip comprendra le formulaire concerné et donc les paramétres des méthodes.
        :type dialog: class (ex:<class 'gedopi.bailPecheDialogs.Bail_peche_dialog'>)
        '''
        self.dialog = dialog
        self.iface = dialog.iface
        self.connector = None

    def getLayerFromLegendByTableProps(self, tableName, geomCol='geom', sql=''):
        '''
        Obtenir la couche de la légende QGIS correspondant à un nom de table
        de base de données PostgreSQL.

        :param tableName: nom de la table QGIS,
                paramètre renvoyé par le script concerné (ex:bailPecheDialogs.py)
        :type tableName: str

        :param geomCol: nom de la colonne de la table contenant la géométrie,
                paramètre renvoyé par le script concerné (ex:bailPecheDialogs.py)
        :type geomCol: str

        :param sql: filtre SQL à appliquer à la table donnée,
                paramètre renvoyé par le script concerné (ex:bailPecheDialogs.py)
        :type sql: str
        '''
        layer = None
        try:
            layers = self.dialog.iface.legendInterface().layers()
            for l in layers:
                if l:
                    if not hasattr(l, 'providerType') or not hasattr(l, 'type'):
                        continue
                    if not l.type() == None:
                        if not l.type() == QgsMapLayer.VectorLayer:
                            continue
                    else:
                        continue
                    if not l.providerType() == None:
                        if not l.providerType() == u'postgres':
                            continue
                    else:
                        continue

                    connectionParams = self.getConnectionParameterFromDbLayer(l)

                    reg = r'(\.| )?(%s)' % tableName
                    if connectionParams and \
                        (\
                            connectionParams['table'] == tableName or \
                            (re.findall(reg, '%s' % connectionParams['table']) and re.findall(reg, '%s' % connectionParams['table'])[0]) \
                        ) and \
                        connectionParams['geocol'] == geomCol and \
                        connectionParams['sql'] == sql:
                        return l
            return layer
        except:
            return None

    def getConnectionParameterFromDbLayer(self, layer):
        '''
        Obtenir les paramètres de connexion à partir de la
        source de données de la couche

        :param layer: couche(s) dans la légende QGIS d'où seront obtenus les paramétres de connexion,
                le paramètre provient de la variable " l " créée dans la méthode "getLayerFromLegendByTableProps"
        :type layer: QgsVectorLayer
        '''

        # Obtention des paramètres via regex
        uri = layer.dataProvider().dataSourceUri()
        reg = "dbname='([^']+)' (?:host=([^ ]+) )?(?:port=([0-9]+) )?(?:user='([^ ]+)' )?(?:password='([^ ]+)' )?(?:sslmode=([^ ]+) )?(?:key='([^ ]+)' )?(?:estimatedmetadata=([^ ]+) )?(?:srid=([0-9]+) )?(?:type=([a-zA-Z]+) )?(?:table=\"(.+)\" \()?(?:([^ ]+)\) )?(?:sql=(.*))?"
        result = re.findall(r'%s' % reg, uri)
        if not result:
            return None

        res = result[0]
        if not res:
            return None

        dbname = res[0]
        host = res[1]
        port = res[2]
        user = res[3]
        password = res[4]
        sslmode = res[5]
        key = res[6]
        estimatedmetadata = res[7]
        srid = res[8]
        gtype = res[9]
        table = res[10]
        geocol = res[11]
        sql = res[12]

        schema = ''

        if ' FROM ' not in table:
            if re.search('"\."', table):
                table = '"' + table + '"'
                sp = table.replace('"', '').split('.')
                schema = sp[0]
                table = sp[1]
        else:
            reg = r'\* FROM ([^\)]+)?(\))?'
            f = re.findall(r'%s' % reg, table)

            if f and f[0]:
                sp = f[0][0].replace('"', '').split('.')
                if len(sp) > 1:
                    schema = sp[0].replace('\\', '')
                    table = sp[1]
                else:
                    table = sp[0]
            else:
                return None


        if layer.providerType() == u'postgres':
            dbType = 'postgis'
        else:
            return None

        connectionParams = {
            'dbname' : dbname,
            'host' : host,
            'port': port,
            'user' : user,
            'password': password,
            'sslmode' : sslmode,
            'key': key,
            'estimatedmetadata' : estimatedmetadata,
            'srid' : srid,
            'type': gtype,
            'schema': schema,
            'table' : table,
            'geocol' : geocol,
            'sql' : sql,
            'dbType': dbType
        }

        return connectionParams

