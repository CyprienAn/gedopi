# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\espePecheElecForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_espePecheElecForm(object):
    def setupUi(self, espePecheElecForm):
        espePecheElecForm.setObjectName(_fromUtf8("espePecheElecForm"))
        espePecheElecForm.resize(371, 86)
        self.verticalLayout = QtGui.QVBoxLayout(espePecheElecForm)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(espePecheElecForm)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.cmbEspece = QtGui.QComboBox(espePecheElecForm)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbEspece.sizePolicy().hasHeightForWidth())
        self.cmbEspece.setSizePolicy(sizePolicy)
        self.cmbEspece.setObjectName(_fromUtf8("cmbEspece"))
        self.horizontalLayout.addWidget(self.cmbEspece)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnEnregistrer = QtGui.QPushButton(espePecheElecForm)
        self.btnEnregistrer.setObjectName(_fromUtf8("btnEnregistrer"))
        self.horizontalLayout_2.addWidget(self.btnEnregistrer)
        self.btnAnnuler = QtGui.QPushButton(espePecheElecForm)
        self.btnAnnuler.setObjectName(_fromUtf8("btnAnnuler"))
        self.horizontalLayout_2.addWidget(self.btnAnnuler)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(espePecheElecForm)
        QtCore.QMetaObject.connectSlotsByName(espePecheElecForm)

    def retranslateUi(self, espePecheElecForm):
        espePecheElecForm.setWindowTitle(_translate("espePecheElecForm", "Export des pêches électriques pour une espèce", None))
        self.label.setText(_translate("espePecheElecForm", "Choix de l\'espèce :", None))
        self.btnEnregistrer.setText(_translate("espePecheElecForm", "Enregistrer", None))
        self.btnAnnuler.setText(_translate("espePecheElecForm", "Annuler", None))
