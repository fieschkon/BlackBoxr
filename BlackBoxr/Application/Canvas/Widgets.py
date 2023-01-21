from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHeaderView, QLineEdit, QSizePolicy,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)
from pyparsing import Optional
from BlackBoxr.misc import objects
import BBData
from fuzzysearch import find_near_matches

class SearchBox(QWidget):

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setupUi()
        self.SearchBar.setFocus()
        self.populateList()

    def populateList(self):
        for collection in objects.itemCollections:
            collectionwidget = QTreeWidgetItem()
            collectionwidget.setText(0, collection.name)
            collectionwidget.setText(1, "(itself)")
            collectionwidget.setData(2, 0, collection)
            self.Items.addTopLevelItem(collectionwidget)

            for itemtype in collection.getAllItemTypes():
                itemdefrep = QTreeWidgetItem(collectionwidget)
                itemdefrep.setText(0, itemtype.name)
                itemdefrep.setText(1, collection.name)
                itemdefrep.setData(2, 0, collection)
                itemdefrep.setData(3, 0, itemtype)
            
            collectionwidget.setExpanded(True)

    def filter(self, searchtext):
        # Todo make this smarter

        if searchtext != '':
            bestdist = (1000, None)
            for index in range(self.Items.topLevelItemCount()):
                tlitem = self.Items.topLevelItem(index)
                for childindex in range(tlitem.childCount()):
                    item = tlitem.child(childindex)

                    # Get similarity
                    matches = find_near_matches(searchtext, str(item.data(3, 0).toDict()), max_l_dist=2)
                    if matches != []:
                        if matches[0].dist < bestdist[0]:
                            bestdist = (matches[0].dist, item)
                    else:
                        item.setHidden(True)
            if bestdist[1] != None:
                bestdist[1].setSelected(True)
        else:
            for index in range(self.Items.topLevelItemCount()):
                tlitem = self.Items.topLevelItem(index)
                for childindex in range(tlitem.childCount()):
                    item = tlitem.child(childindex)
                    item.setHidden(False)    
        

    def setupUi(self):
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.setMaximumSize(QSize(16777215, 500))
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(2, 2, 2, 2)
        self.SearchBar = QLineEdit(self)
        self.SearchBar.setObjectName(u"SearchBar")

        self.SearchBar.textChanged.connect(lambda : self.filter(self.SearchBar.text()))

        self.verticalLayout.addWidget(self.SearchBar)

        self.Items = QTreeWidget(self)
        self.Items.setColumnCount(2)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Item Name")
        __qtreewidgetitem.setText(1, u"From Collection")
        self.Items.setHeaderItem(__qtreewidgetitem)
        self.Items.setObjectName(u"Items")

        self.verticalLayout.addWidget(self.Items)

        self.setWindowFlags(Qt.FramelessWindowHint)


