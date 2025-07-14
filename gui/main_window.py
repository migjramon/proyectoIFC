import ifcopenshell
import ifcopenshell.util.element

# gui/main_window.py
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QMenu, QMessageBox, QVBoxLayout, QWidget, QStatusBar, QLabel, QFileDialog
from PyQt5.QtWidgets import QTreeView, QTableWidget, QTableWidgetItem, QSplitter
from PyQt5.QtCore import QAbstractItemModel, QModelIndex
from PyQt5.QtWidgets import  QMdiArea, QMdiSubWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from PyQt5.QtCore import Qt
# Importa tus módulos de lógica de negocio

from core.ifc_handler import IfcHandler
from core.ifc_operations import IfcOperations
from core.object_creator import IfcObjectCreator
from core.bim_4d import BIM4D
from core.bim_5d import BIM5D


from collections import defaultdict

class IFCMainWindow(QMainWindow):
    """
    Ventana principal del editor IFC.

    Gestiona la interfaz de usuario, incluyendo menús, barras de herramientas
    y la integración con las funcionalidades de procesamiento IFC.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Editor IFC Avanzado")
        self.setGeometry(100, 100, 1200, 800)

        self.ifc_model = None # Aquí se cargará el modelo IFC



        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)
        
        self.setStatusBar(QStatusBar(self)) # Barra de estado


        self._create_actions()
        self._create_menus()
        self._setup_ui()

        self.ifc_handler = IfcHandler()
        self.ifc_operations = IfcOperations()
        self.object_creator = IfcObjectCreator()
        self.bim_4d = BIM4D()
        self.bim_5d = BIM5D()

        self.status_label = QLabel("Listo.")  # <-- CREA EL QLabel DESPUÉS
        self.statusBar().addWidget(self.status_label)


    def _create_actions(self):
        """Define todas las acciones (QAction) para los menús y barras."""
        # Acciones de Archivo
        self.new_action = QAction("&Nuevo", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Crear un nuevo archivo IFC")
        self.new_action.triggered.connect(self._new_file)

        self.open_action = QAction("&Abrir...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Abrir un archivo IFC existente")
        self.open_action.triggered.connect(self._open_file)

        self.save_action = QAction("&Guardar", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Guardar el archivo IFC actual")
        self.save_action.triggered.connect(self._save_file)
        self.save_action.setEnabled(False) # Deshabilitado hasta que haya un modelo

        self.exit_action = QAction("&Salir", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Cerrar la aplicación")
        self.exit_action.triggered.connect(self.close)

        # Acciones de Edición
        self.undo_action = QAction("&Deshacer", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setEnabled(False) # Deshabilitado por defecto
        # ... más acciones de edición

        # Acciones de Objetos Constructivos (3D)
        self.create_footing_action = QAction("Crear &Zapata", self)
        self.create_footing_action.triggered.connect(self._create_footing)
        # ... más acciones para otros objetos

        # Acciones de Gestión (4D/5D)
        self.schedule_4d_action = QAction("Gestión de &Programación (4D)", self)
        self.schedule_4d_action.triggered.connect(self._manage_4d_bim)

        self.costs_5d_action = QAction("Gestión de &Costos (5D)", self)
        self.costs_5d_action.triggered.connect(self._manage_5d_bim)


    def _create_menus(self):
        """Crea la barra de menú y los menús con sus acciones."""
        menu_bar = self.menuBar()

        # Menú Archivo
        file_menu = menu_bar.addMenu("&Archivo")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addSeparator() # Separador visual
        file_menu.addAction(self.exit_action)

        # Menú Editar
        edit_menu = menu_bar.addMenu("&Editar")
        edit_menu.addAction(self.undo_action)
        # ... añadir más acciones de edición

        # Menú Objetos Constructivos (3D)
        objects_menu = menu_bar.addMenu("&Objetos Constructivos (3D)")
        objects_menu.addAction(self.create_footing_action)
        # ... añadir acciones para otros objetos (muros, ventanas, etc.)

        # Menú Gestión
        management_menu = menu_bar.addMenu("&Gestión")
        management_menu.addAction(self.schedule_4d_action)
        management_menu.addAction(self.costs_5d_action)

    def _setup_ui(self):
        """Configura los widgets principales de la ventana."""
        splitter = QSplitter(self)
        self.setCentralWidget(splitter)

        # Árbol de clases IFC (izquierda)
        self.tree_view = QTreeView()
        splitter.addWidget(self.tree_view)

        # Tabla de atributos (derecha)
        self.attr_table = QTableWidget()
        self.attr_table.setColumnCount(2)
        self.attr_table.setHorizontalHeaderLabels(["Atributo", "Valor"])
        splitter.addWidget(self.attr_table)

        splitter.setSizes([400, 800])

        # Etiqueta de estado (abajo)
        self.status_label = QLabel("Listo.")
        self.statusBar().addWidget(self.status_label)


    # --- Métodos para manejar las acciones (simulados) ---
    def _new_file(self):
        QMessageBox.information(self, "Nuevo Archivo", "Crear nuevo archivo IFC (lógica pendiente).")
        self.ifc_model = self.ifc_handler.create_new_model()
        self.save_action.setEnabled(True)
        self.status_label.setText("Nuevo modelo IFC creado.")

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Abrir archivo IFC", "", "Archivos IFC (*.ifc);;Todos los archivos (*)")
        if file_path:
            try:
                #self.ifc_model = self.ifc_handler.load_model(file_path)
                self.ifc_model = ifcopenshell.open(file_path)
                QMessageBox.information(self, "Abrir Archivo", f"Archivo '{file_path}' cargado exitosamente.")
                self.save_action.setEnabled(True)
                self.status_label.setText(f"Modelo cargado de: {file_path}")
                self._load_ifc_tree()
            except Exception as e:
                QMessageBox.critical(self, "Error al abrir", f"No se pudo cargar el archivo: {e}")
                self.ifc_model = None
                self.save_action.setEnabled(False)

    def _save_file(self):
        if not self.ifc_model:
            QMessageBox.warning(self, "Guardar Archivo", "No hay un modelo IFC cargado para guardar.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar archivo IFC", "", "Archivos IFC (*.ifc);;Todos los archivos (*)")
        if file_path:
            try:
                self.ifc_handler.save_model(self.ifc_model, file_path)
                QMessageBox.information(self, "Guardar Archivo", f"Archivo guardado exitosamente en '{file_path}'.")
                self.status_label.setText(f"Modelo guardado en: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el archivo: {e}")

    def _create_footing(self):
        if not self.ifc_model:
            QMessageBox.warning(self, "Crear Objeto", "Primero abra o cree un modelo IFC.")
            return
        QMessageBox.information(self, "Crear Zapara", "Lógica para crear zapata (usando object_creator.py) pendiente.")
        # Ejemplo: self.object_creator.create_footing(self.ifc_model, params...)
        self.status_label.setText("Acción: Crear Zapata.")

    def _manage_4d_bim(self):
        if not self.ifc_model:
            QMessageBox.warning(self, "Gestión 4D", "Primero abra o cree un modelo IFC.")
            return
        QMessageBox.information(self, "Gestión 4D", "Lógica para gestión de programación 4D (usando bim_4d.py) pendiente.")
        # Ejemplo: self.bim_4d.open_4d_dialog(self.ifc_model)
        self.status_label.setText("Acción: Gestión 4D.")

    def _manage_5d_bim(self):
        if not self.ifc_model:
            QMessageBox.warning(self, "Gestión 5D", "Primero abra o cree un modelo IFC.")
            return
        # Importa tu clase ViewCost
        from gui.CostView import CostView

        # Crea la subventana MDI
        subwindow = QMdiSubWindow()
        subwindow.setWidget(CostView(self.ifc_model))
        subwindow.setWindowTitle("Gestión de Costos 5D")
        self.mdi_area.addSubWindow(subwindow)
        subwindow.show()
        self.status_label.setText("Acción: Gestión 5D (MDI).")

    def _load_ifc_tree(self):
        """
        Carga el árbol de clases IFC a nivel raíz en el QTreeView.
        """
        from collections import defaultdict

        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Clases IFC"])

        if self.ifc_model:
            grouped = defaultdict(list)
            for entity in self.ifc_model:  # Itera sobre todas las entidades
                grouped[entity.is_a()].append(entity)

            for entity_type, entities in sorted(grouped.items()):
                type_item = QStandardItem(f"{entity_type} ({len(entities)})")
                type_item.setEditable(False)
                model.appendRow(type_item)
                # Puedes agregar los hijos aquí si lo deseas:
                for entity in entities:
                    child_item = QStandardItem(f"#{entity.id()} {getattr(entity, 'Name', '')}")
                    child_item.setEditable(False)
                    type_item.appendRow(child_item)

        self.tree_view.setModel(model)
        self.tree_view.expandAll()
        self.tree_view.clicked.connect(self._on_tree_item_clicked)

    def _on_tree_item_clicked(self, index: QModelIndex):
        """
        Muestra los atributos del objeto seleccionado en la tabla de la derecha.
        """
        model = self.tree_view.model()
        item = model.itemFromIndex(index)
        if not item:
            return

        # Intenta obtener el id de entidad guardado en Qt.UserRole
        entity_id = item.data(Qt.UserRole)
        entity = None

        # Si el nodo es un hijo (entidad), busca por id
        if entity_id is not None:
            try:
                entity = self.ifc_model[entity_id]
            except Exception:
                self.attr_table.setRowCount(0)
                self.status_label.setText("Entidad IFC no encontrada.")
                return
        else:
            # Si es un nodo de tipo, no mostrar atributos
            self.attr_table.setRowCount(0)
            self.status_label.setText("Seleccione una entidad IFC para ver sus atributos.")
            return

        # Mostrar los atributos del objeto seleccionado
        attrs = entity.get_info()
        self.attr_table.setRowCount(len(attrs))
        for i, (key, value) in enumerate(attrs.items()):
            self.attr_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.attr_table.setItem(i, 1, QTableWidgetItem(str(value)))

        self.status_label.setText(f"Entidad seleccionada: #{entity.id()} {getattr(entity, 'Name', '')}")



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QLabel, QFileDialog # Importaciones adicionales para el ejemplo

    app = QApplication(sys.argv)
    window = IFCMainWindow()
    window.show()
    sys.exit(app.exec_())