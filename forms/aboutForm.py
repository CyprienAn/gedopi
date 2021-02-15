# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'forms\aboutForm.ui'
#
# Created by: PyQt5 UI code generator 5.9
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_aboutForm(object):
    def setupUi(self, aboutForm):
        aboutForm.setObjectName("aboutForm")
        aboutForm.resize(409, 338)
        self.verticalLayout = QtWidgets.QVBoxLayout(aboutForm)
        self.verticalLayout.setObjectName("verticalLayout")
        self.scrollArea = QtWidgets.QScrollArea(aboutForm)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 389, 289))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.groupBox = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setWordWrap(True)
        self.label_5.setObjectName("label_5")
        self.verticalLayout_3.addWidget(self.label_5)
        self.verticalLayout_2.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.groupBox_2)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_10 = QtWidgets.QLabel(self.groupBox_2)
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setWordWrap(True)
        self.label_10.setObjectName("label_10")
        self.verticalLayout_4.addWidget(self.label_10)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.groupBox_3 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label = QtWidgets.QLabel(self.groupBox_3)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setObjectName("label")
        self.verticalLayout_5.addWidget(self.label)
        self.verticalLayout_2.addWidget(self.groupBox_3)
        self.groupBox_4 = QtWidgets.QGroupBox(self.scrollAreaWidgetContents)
        self.groupBox_4.setObjectName("groupBox_4")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox_4)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_15 = QtWidgets.QLabel(self.groupBox_4)
        self.label_15.setAlignment(QtCore.Qt.AlignCenter)
        self.label_15.setWordWrap(True)
        self.label_15.setOpenExternalLinks(True)
        self.label_15.setObjectName("label_15")
        self.verticalLayout_6.addWidget(self.label_15)
        self.verticalLayout_2.addWidget(self.groupBox_4)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtWidgets.QDialogButtonBox(aboutForm)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(aboutForm)
        QtCore.QMetaObject.connectSlotsByName(aboutForm)

    def retranslateUi(self, aboutForm):
        _translate = QtCore.QCoreApplication.translate
        aboutForm.setWindowTitle(_translate("aboutForm", "Gedopi - A propos"))
        self.groupBox.setTitle(_translate("aboutForm", "Financeurs"))
        self.label_5.setText(_translate("aboutForm", "La réalisation du plugin Gedopi a été financée par la Fédération de Pêche du Cantal ainsi que l\'Agence de l\'Eau Adour-Garonne."))
        self.groupBox_2.setTitle(_translate("aboutForm", "Conception"))
        self.label_10.setText(_translate("aboutForm", "Le plugin Gedopi a été conçu et développé par Cyprien Antignac, employé à la FDPPMA du Cantal en 2016-2017."))
        self.groupBox_3.setTitle(_translate("aboutForm", "Auteurs"))
        self.label.setText(_translate("aboutForm", "Cyprien Antignac (antignac.cyprien@laposte.net) avec l\'aide d\'Alain Layec (professeur à la LPSIG de La Rochelle) et des responsables techniques de la fédération (Romain Max et Agnès Tronche)."))
        self.groupBox_4.setTitle(_translate("aboutForm", "Licence"))
        self.label_15.setText(_translate("aboutForm", "<html><head/><body><p>Ce plugin est sous licence GNU GPLv3. Pour plus d\'information : <a href=\"https://www.gnu.org/licenses/quick-guide-gplv3.htm\"><span style=\" text-decoration: underline; color:#0000ff;\">https://www.gnu.org/licenses/quick-guide-gplv3.html</span></a></p></body></html>"))

