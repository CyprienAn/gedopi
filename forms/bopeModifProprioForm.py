# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\bopeModifProprioForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_dlgBopeModifProprioForm(object):
    def setupUi(self, dlgBopeModifProprioForm):
        dlgBopeModifProprioForm.setObjectName("dlgBopeModifProprioForm")
        dlgBopeModifProprioForm.resize(489, 162)
        self.verticalLayout = QtWidgets.QVBoxLayout(dlgBopeModifProprioForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.grp_proprio = QtWidgets.QGroupBox(dlgBopeModifProprioForm)
        self.grp_proprio.setObjectName("grp_proprio")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.grp_proprio)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.lbl_nom = QtWidgets.QLabel(self.grp_proprio)
        self.lbl_nom.setObjectName("lbl_nom")
        self.horizontalLayout_12.addWidget(self.lbl_nom)
        self.leNom = QtWidgets.QLineEdit(self.grp_proprio)
        self.leNom.setAlignment(QtCore.Qt.AlignCenter)
        self.leNom.setObjectName("leNom")
        self.horizontalLayout_12.addWidget(self.leNom)
        self.verticalLayout_6.addLayout(self.horizontalLayout_12)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.lbl_mail = QtWidgets.QLabel(self.grp_proprio)
        self.lbl_mail.setObjectName("lbl_mail")
        self.horizontalLayout_14.addWidget(self.lbl_mail)
        self.leMail = QtWidgets.QLineEdit(self.grp_proprio)
        self.leMail.setAlignment(QtCore.Qt.AlignCenter)
        self.leMail.setObjectName("leMail")
        self.horizontalLayout_14.addWidget(self.leMail)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.lbl_tel = QtWidgets.QLabel(self.grp_proprio)
        self.lbl_tel.setMinimumSize(QtCore.QSize(50, 0))
        self.lbl_tel.setObjectName("lbl_tel")
        self.horizontalLayout_13.addWidget(self.lbl_tel)
        self.leTel = QtWidgets.QLineEdit(self.grp_proprio)
        self.leTel.setMinimumSize(QtCore.QSize(0, 0))
        self.leTel.setMaximumSize(QtCore.QSize(100, 16777215))
        self.leTel.setAlignment(QtCore.Qt.AlignCenter)
        self.leTel.setObjectName("leTel")
        self.horizontalLayout_13.addWidget(self.leTel)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_13.addItem(spacerItem)
        self.horizontalLayout_14.addLayout(self.horizontalLayout_13)
        self.verticalLayout_6.addLayout(self.horizontalLayout_14)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_3 = QtWidgets.QLabel(self.grp_proprio)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        self.leAdresse = QtWidgets.QLineEdit(self.grp_proprio)
        self.leAdresse.setAlignment(QtCore.Qt.AlignCenter)
        self.leAdresse.setObjectName("leAdresse")
        self.horizontalLayout_3.addWidget(self.leAdresse)
        self.verticalLayout_6.addLayout(self.horizontalLayout_3)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.grp_proprio)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_6.addWidget(self.buttonBox)
        self.verticalLayout.addWidget(self.grp_proprio)

        self.retranslateUi(dlgBopeModifProprioForm)
        QtCore.QMetaObject.connectSlotsByName(dlgBopeModifProprioForm)

    def retranslateUi(self, dlgBopeModifProprioForm):
        _translate = QtCore.QCoreApplication.translate
        dlgBopeModifProprioForm.setWindowTitle(_translate("dlgBopeModifProprioForm", "Modification du propriétaire"))
        self.grp_proprio.setTitle(_translate("dlgBopeModifProprioForm", "Propriétaire "))
        self.lbl_nom.setText(_translate("dlgBopeModifProprioForm", "Nom :"))
        self.lbl_mail.setText(_translate("dlgBopeModifProprioForm", "E-mail :"))
        self.lbl_tel.setText(_translate("dlgBopeModifProprioForm", "Téléphone :"))
        self.label_3.setText(_translate("dlgBopeModifProprioForm", "Adresse :"))

