
from typing import Optional
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox, QLineEdit, QSpacerItem,
    QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QFrame, QListView, QListWidget, QListWidgetItem,
    QWidget)

from BBData import BBData
from BBData.BBData import ItemDefinition, ItemTypeCollection

class ItemDictionary(QDialog):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setupUi()
        self.collections = []

        checkoptions = [(0, 'TestA', False), (1, 'TestB', True)]
        basicfield = BBData.Checks(checkoptions)

        itemdef = BBData.ItemDefinition(fields=[basicfield])

        col = BBData.ItemTypeCollection()
        col.addRequirement(itemdef)

        self.addToExplorer(col)

    def addToExplorer(self, collection : ItemTypeCollection):
        titleitem = QTreeWidgetItem()
        titleitem.setText(0, collection.name)
        titleitem.setData(1, 0, collection)
        self.CollectionExplorer.addTopLevelItem(titleitem)

        for itemType in collection.getAllItemTypes():
            typeItemWidget = QTreeWidgetItem(titleitem)
            typeItemWidget.setText(0, itemType.name)
            typeItemWidget.setData(1, 0, itemType)
        
    def setupUi(self):
        self.resize(812, 441)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.widget_2 = QWidget(self)
        self.widget_2.setObjectName(u"widget_2")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
        self.widget_2.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.widget_2)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.widget_3 = QWidget(self.widget_2)
        self.widget_3.setObjectName(u"widget_3")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_3)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(4, 0, 4, 4)
        self.NewCollectionButton = QPushButton(self.widget_3)
        self.NewCollectionButton.setObjectName(u"NewCollectionButton")

        self.horizontalLayout_2.addWidget(self.NewCollectionButton)


        self.verticalLayout_2.addWidget(self.widget_3)

        self.CollectionExplorer = QTreeWidget(self.widget_2)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1")
        self.CollectionExplorer.setHeaderItem(__qtreewidgetitem)
        self.CollectionExplorer.setObjectName(u"CollectionExplorer")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.CollectionExplorer.sizePolicy().hasHeightForWidth())
        self.CollectionExplorer.setSizePolicy(sizePolicy1)

        self.verticalLayout_2.addWidget(self.CollectionExplorer)


        self.horizontalLayout.addWidget(self.widget_2)

        self.widget = QWidget(self)
        self.widget.setObjectName(u"widget")
        self.verticalLayout_3 = QVBoxLayout(self.widget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 5, 0, 0)


        self.ItemDefinitionPanel = QWidget(self.widget)
        self.ItemDefinitionPanel.setObjectName(u"widget_4")

        self.verticalLayout_3.addWidget(self.ItemDefinitionPanel)


        self.horizontalLayout.addWidget(self.widget)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply|QDialogButtonBox.Cancel)

        self.verticalLayout.addWidget(self.buttonBox)

        self.setWindowTitle('Item Definition Manager')
        self.NewCollectionButton.setText('Add')

        self.CollectionExplorer.itemClicked.connect(self.onNewExplorerSelection)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def onNewExplorerSelection(self, item : QTreeWidgetItem, col):
        print(item, col)
        try:
            self.ItemDefinitionPanel.deleteLater()
        except RuntimeError : pass
        
        for index in range(self.CollectionExplorer.topLevelItemCount()):
            if self.CollectionExplorer.topLevelItem(index) == item:
                return

        self.ItemDefinitionPanel = DefinitionEditView(item.data(1, 0), self.widget)
        self.ItemDefinitionPanel.setDefinitionName(item.text(0))
        self.verticalLayout_3.addWidget(self.ItemDefinitionPanel)

class DefinitionEditView(QWidget):
    def __init__(self, itemdef : BBData.ItemDefinition, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setupUi()
        self.setDefinitionName(itemdef.name)
        self.itemdef = itemdef
        self.populateFields()

    def populateFields(self):
        print('populating')
        for field in self.itemdef.fields:
            print(field)
            itemreppr = QListWidgetItem()
            editor = GenericFieldEdit(field)
            self.FieldEditWidgets.addItem(itemreppr)
            self.FieldEditWidgets.setItemWidget(itemreppr, editor)
            itemreppr.setSizeHint(editor.sizeHint())

    def setDefinitionName(self, name):
        self.TypeName.setText(name)

    def setupUi(self):
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, 0, -1)
        self.label = QLabel(self)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.label)

        self.TypeName = QLineEdit(self)
        self.TypeName.setObjectName(u"TypeName")
        self.TypeName.setMaximumSize(QSize(400, 16777215))

        self.horizontalLayout.addWidget(self.TypeName)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.FieldEditWidgets = QListWidget(self)
        self.FieldEditWidgets.setObjectName(u"FieldEditWidgets")
        self.FieldEditWidgets.setFrameShape(QFrame.NoFrame)
        self.FieldEditWidgets.setFrameShadow(QFrame.Plain)
        self.FieldEditWidgets.setResizeMode(QListView.Adjust)

        self.verticalLayout.addWidget(self.FieldEditWidgets)

        self.AddFieldButton = QPushButton(self)
        self.AddFieldButton.setObjectName(u"AddFieldButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.AddFieldButton.sizePolicy().hasHeightForWidth())
        self.AddFieldButton.setSizePolicy(sizePolicy1)
        self.AddFieldButton.setLayoutDirection(Qt.LeftToRight)

        self.verticalLayout.addWidget(self.AddFieldButton, 0, Qt.AlignRight)



        self.label.setText(u"Item Type Name:")
        self.AddFieldButton.setText(u"Add Field")



class GenericFieldEdit(QWidget):
    def __init__(self, field : BBData.Field, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.field = field
        self.setupUi()

    def setupUi(self):
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        self.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(self)
        self.widget.setObjectName(u"widget")
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, 0)
        self.FieldNameEdit = QLineEdit(self.widget)
        self.FieldNameEdit.setObjectName(u"FieldNameEdit")

        self.horizontalLayout.addWidget(self.FieldNameEdit)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)


        self.verticalLayout.addWidget(self.widget)

        self.widget_2 = QWidget(self)
        self.widget_2.setObjectName(u"widget_2")

        self.verticalLayout.addWidget(self.widget_2)

        self.AddOptionButton = QPushButton(self)
        self.AddOptionButton.setObjectName(u"AddOptionButton")
        sizePolicy1 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.AddOptionButton.sizePolicy().hasHeightForWidth())
        self.AddOptionButton.setSizePolicy(sizePolicy1)

        self.verticalLayout.addWidget(self.AddOptionButton, 0, Qt.AlignRight)

        self.FieldNameEdit.setText(self.field.name)
        self.AddOptionButton.setText(u"Add Option")

