from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton, QHBoxLayout,
    QMessageBox, QMenu, QInputDialog, QFileDialog
)
from PyQt5.QtCore import Qt

class CostView(QWidget):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Estructura de Desglose de Costos (EDC)")
        self.resize(1000, 700)

        self.current_editor = None
        self.editing_item_id = None
        self.editing_column = None

        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        add_root_btn = QPushButton("Añadir Ítem Raíz")
        add_root_btn.clicked.connect(self._add_root_item)
        button_layout.addWidget(add_root_btn)

        calc_btn = QPushButton("Calcular Totales")
        calc_btn.clicked.connect(self._calculate_totals)
        button_layout.addWidget(calc_btn)

        update_ifc_btn = QPushButton("Actualizar Cantidades IFC")
        update_ifc_btn.clicked.connect(self._update_ifc_quantities)
        button_layout.addWidget(update_ifc_btn)

        save_btn = QPushButton("Guardar Presupuesto")
        save_btn.clicked.connect(self._save_budget)
        button_layout.addWidget(save_btn)

        load_btn = QPushButton("Cargar Presupuesto")
        load_btn.clicked.connect(self._load_budget)
        button_layout.addWidget(load_btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "Concepto", "Descripción", "Unidad", "Cantidad", "Precio Unitario", "Importe", "Datos IFC"
        ])
        self.tree.setColumnWidth(0, 250)
        self.tree.setColumnWidth(1, 180)
        self.tree.setColumnWidth(2, 70)
        self.tree.setColumnWidth(3, 90)
        self.tree.setColumnWidth(4, 100)
        self.tree.setColumnWidth(5, 110)
        self.tree.setColumnWidth(6, 150)
        layout.addWidget(self.tree)

        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._start_inline_edit)

        self.update_treeview()

    def update_treeview(self):
        self.tree.clear()
        root_items = self.controller.get_root_items()
        for item_model in root_items:
            self._insert_item_into_tree(item_model, None)

    def _insert_item_into_tree(self, item_model, parent_item):
        values = [
            item_model.name,
            item_model.description,
            item_model.unit_name,
            f"{item_model.quantity:,.2f}" if item_model.quantity is not None else "",
            f"{item_model.unit_cost:,.2f}" if item_model.unit_cost is not None else "",
            f"{item_model.total_cost:,.2f}" if item_model.total_cost is not None else "",
            f"{item_model.ifc_entity_type or ''}: {item_model.ifc_guid[:8]}..." if item_model.ifc_guid else ""
        ]
        item = QTreeWidgetItem(values)
        item.setData(0, Qt.UserRole, item_model.id)
        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree.addTopLevelItem(item)
        for child_id in item_model.children:
            child_model = self.controller.get_item_by_id(child_id)
            if child_model:
                self._insert_item_into_tree(child_model, item)

    def _get_selected_item_id(self):
        selected_item = self.tree.currentItem()
        if not selected_item:
            QMessageBox.warning(self, "Selección", "Por favor, seleccione un ítem.")
            return None
        return selected_item.data(0, Qt.UserRole)

    def _add_root_item(self):
        self._show_add_edit_dialog(parent_id=None)

    def _add_child_item(self):
        parent_id = self._get_selected_item_id()
        if parent_id is not None:
            self._show_add_edit_dialog(parent_id=parent_id)
        else:
            QMessageBox.warning(self, "Error", "Debe seleccionar un ítem padre para añadir un hijo.")

    def _add_sibling_item(self):
        selected_id = self._get_selected_item_id()
        if selected_id is not None:
            item_model = self.controller.get_item_by_id(selected_id)
            self._show_add_edit_dialog(parent_id=item_model.parent_id)
        else:
            QMessageBox.warning(self, "Error", "Seleccione un ítem para añadir un hermano.")

    def _edit_selected_item(self):
        item_id = self._get_selected_item_id()
        if item_id:
            self._show_add_edit_dialog(item_id=item_id)

    def _delete_selected_item(self):
        item_id = self._get_selected_item_id()
        if item_id:
            reply = QMessageBox.question(
                self, "Confirmar Eliminación",
                "¿Está seguro de que desea eliminar este ítem y todos sus hijos?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.controller.delete_cost_item(item_id)
                self.update_treeview()

    def _show_add_edit_dialog(self, item_id=None, parent_id=None):
        # Diálogo simplificado para añadir/editar propiedades básicas
        name, ok = QInputDialog.getText(self, "Nombre", "Nombre del ítem:")
        if not ok or not name:
            return
        description, ok = QInputDialog.getText(self, "Descripción", "Descripción del ítem:")
        if not ok:
            return
        cost_type_options = [
            "PROYECTO", "EDIFICIO", "URBANIZACION", "OBRAS_EXTERIORES", "SERVICIOS", "ZONA", "APARTAMENTO",
            "CONSTRUCCION", "INSTALACION", "ACABADOS", "LIMPIEZA", "SUPERVISION", "LABORATORIOS", "CALIDAD",
            "MATERIAL", "LABOR", "EQUIPMENT", "SUBTOTAL", "TOTAL", "UNIDAD_PRECIO", "OTROS"
        ]
        cost_type, ok = QInputDialog.getItem(self, "Tipo de Costo", "Tipo:", cost_type_options, editable=False)
        if not ok:
            return
        data = {
            "name": name,
            "description": description,
            "cost_type": cost_type
        }
        if item_id:
            self.controller.edit_cost_item(item_id, data)
        else:
            self.controller.add_cost_item(parent_id=parent_id, **data)
        self.update_treeview()

    def _start_inline_edit(self, item, column):
        # Solo permitir edición en columnas específicas
        editable_columns = [0, 1, 3, 4]
        if column not in editable_columns:
            return
        item_id = item.data(0, Qt.UserRole)
        old_value = item.text(column)
        new_value, ok = QInputDialog.getText(self, "Editar valor", f"Nuevo valor para '{self.tree.headerItem().text(column)}':", text=old_value)
        if ok:
            attr_map = {0: "name", 1: "description", 3: "quantity", 4: "unit_cost"}
            attr_name = attr_map.get(column)
            if attr_name:
                try:
                    if attr_name in ["quantity", "unit_cost"]:
                        new_value = float(new_value.replace(",", ""))
                    self.controller.edit_cost_item(item_id, {attr_name: new_value})
                    self.controller.recalculate_item_cost(item_id)
                except ValueError:
                    QMessageBox.warning(self, "Error", "Por favor ingrese un valor numérico válido.")
            self.update_treeview()

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        menu = QMenu(self)
        menu.addAction("Añadir Ítem Hijo", self._add_child_item)
        menu.addAction("Añadir Ítem Hermano", self._add_sibling_item)
        menu.addAction("Editar Ítem", self._edit_selected_item)
        menu.addAction("Eliminar Ítem", self._delete_selected_item)
        menu.addSeparator()
        menu.addAction("Vincular a IFC...", self._link_to_ifc_dialog)
        menu.addAction("Vincular a Catálogo...", self._link_to_catalog_dialog)
        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def _link_to_ifc_dialog(self):
        item_id = self._get_selected_item_id()
        if not item_id:
            return
        ifc_elements = self.controller.get_ifc_elements_for_linking()
        if not ifc_elements:
            QMessageBox.information(self, "Modelo IFC", "No hay un modelo IFC cargado o no contiene elementos vinculables.")
            return
        items = [f"{guid[:8]}... {ifc_type} {name}" for guid, ifc_type, name in ifc_elements]
        selected, ok = QInputDialog.getItem(self, "Vincular a IFC", "Seleccione elemento IFC:", items, editable=False)
        if ok and selected:
            selected_guid = selected.split("...")[0]
            for guid, ifc_type, name in ifc_elements:
                if guid.startswith(selected_guid):
                    self.controller.link_to_ifc_object(item_id, guid, ifc_type)
                    self.update_treeview()
                    break

    def _link_to_catalog_dialog(self):
        QMessageBox.information(self, "Catálogo", "Funcionalidad de vinculación a catálogo no implementada.")

    def _update_ifc_quantities(self):
        QMessageBox.information(self, "Actualizar IFC", "Funcionalidad de actualización de cantidades IFC no implementada.")

    def _calculate_totals(self):
        QMessageBox.information(self, "Calcular Totales", "Funcionalidad de cálculo de totales no implementada.")

    def _save_budget(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Presupuesto", "", "Archivos JSON (*.json)")
        if file_path:
            self.controller.save_budget(file_path)
            QMessageBox.information(self, "Guardar", "Presupuesto guardado exitosamente.")

    def _load_budget(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Cargar Presupuesto", "", "Archivos JSON (*.json);;Archivos IFC (*.ifc)")
        if file_path:
            self.controller.load_budget(file_path)
            self.update_treeview()
            QMessageBox.information(self, "Cargar", "Presupuesto cargado exitosamente.")