# -*- coding: utf-8 -*-
# Ce script initialise le plugin, le faisant connaître à QGIS.

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    '''Charge la class gedopi à partir du fichier gedopiMenu.

    :param iface: Une instance d'interface QGIS.
    :type iface: QgsInterface
    '''
    from .gedopiMenu import gedopi
    return gedopi(iface)