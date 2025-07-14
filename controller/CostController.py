# cost_module/controller.py (Modificaciones clave)
import json
import ifcopenshell
import mysql.connector
from tkinter import messagebox # Para usar en el controlador si se muestran mensajes de error/info directamente
from .model import CostModel, CostItemModel # Asegúrate de la importación relativa correcta
# Asegura que ifc_model_logic contenga get_ifc_quantity
from . import ifc_model_logic # Asumiendo que ifc_model_logic.py está en el mismo paquete o es accesible

class CostController:
    def __init__(self, ifc_model_ref, update_ifc_model_callback):
        self.db_config = {
            'host': 'localhost',
            'user': 'your_user',
            'password': 'your_password',
            'database': 'your_database_name'
        }
        self.model = CostModel(self.db_config)
        self.view = None
        self.model.set_ifc_model(ifc_model_ref)
        self.update_ifc_model_callback = update_ifc_model_callback

    def set_ifc_model(self, ifc_model):
        self.model.set_ifc_model(ifc_model)

    def open_budget_window(self):
        # La vista se crea pasando el controlador a sí misma
        if self.view is None or not self.view.winfo_exists():
            from .view import CostView # Importación tardía para evitar dependencia circular
            self.view = CostView(tk.Toplevel(), self) # Asume master es tk.Toplevel()
            # self.view.update_treeview() # Ya se llama en el __init__ de CostView
        self.view.focus_set()

    def add_cost_item(self, parent_id=None, **kwargs):
        # Asegúrate de que los campos numéricos sean números
        if 'quantity' in kwargs and kwargs['quantity'] == "": kwargs['quantity'] = 0.0
        if 'unit_cost' in kwargs and kwargs['unit_cost'] == "": kwargs['unit_cost'] = 0.0

        new_id = self.model.add_item(parent_id=parent_id, **kwargs)
        self.recalculate_item_cost(new_id) # Recalcular el nuevo ítem y sus padres
        return new_id

    def edit_cost_item(self, item_id, data):
        # Convertir datos si es necesario (ej. strings de la GUI a float)
        if 'quantity' in data:
            try: data['quantity'] = float(data['quantity'])
            except ValueError: data['quantity'] = 0.0 # O manejar error
        if 'unit_cost' in data:
            try: data['unit_cost'] = float(data['unit_cost'])
            except ValueError: data['unit_cost'] = 0.0 # O manejar error

        self.model.update_item(item_id, **data)
        self.recalculate_item_cost(item_id)

    # ... (Otros métodos como delete_cost_item, get_root_items, get_item_by_id son iguales)

    def get_ifc_elements_for_linking(self):
        # Este método es nuevo y es crucial para el selector IFC en la vista.
        # Debe devolver una lista de tuplas: (guid, ifc_type, name)
        if not self.model.ifc_model_data:
            return []

        elements_list = []
        # Puedes filtrar por tipos específicos de interés (IfcWall, IfcSlab, IfcSpace, etc.)
        for product in self.model.ifc_model_data.by_type("IfcProduct"):
            # Excluir IfcProduct genéricos si solo quieres elementos constructivos específicos
            if product.is_a("IfcBuildingElement") or product.is_a("IfcSpace") or product.is_a("IfcDistributionElement"):
                elements_list.append((product.GlobalId, product.is_a(), product.Name))
        
        # Opcional: añadir IfcSpace si los quieres para cuantificar por áreas de habitación
        for space in self.model.ifc_model_data.by_type("IfcSpace"):
             elements_list.append((space.GlobalId, space.is_a(), space.Name))
        
        return elements_list

    def link_to_ifc_object(self, cost_item_id, ifc_guid, ifc_entity_type):
        quantity, unit = self.model.get_ifc_quantity(ifc_guid)
        if quantity is not None:
            self.model.update_item(cost_item_id, 
                                   ifc_guid=ifc_guid, 
                                   ifc_entity_type=ifc_entity_type,
                                   quantity=quantity,
                                   unit_name=unit)
            self.recalculate_item_cost(cost_item_id)
            messagebox.showinfo("Vínculo IFC", f"Cantidad {quantity} {unit} vinculada para {ifc_entity_type}.")
        else:
            messagebox.showwarning("Vínculo IFC", f"No se pudo obtener la cantidad del elemento IFC {ifc_guid}. Por favor, verifique el modelo.")

    def link_to_catalog_price(self, cost_item_id, catalog_price_id):
        prices = self.model.get_catalog_prices()
        selected_price = next((p for p in prices if p['id'] == catalog_price_id), None)
        if selected_price:
            self.model.update_item(cost_item_id,
                                   catalog_price_id=catalog_price_id,
                                   unit_cost=float(selected_price['costo_unitario']),
                                   unit_name=selected_price['unidad'])
            self.recalculate_item_cost(cost_item_id)
            messagebox.showinfo("Vínculo Catálogo", "Costo unitario del catálogo vinculado.")
        else:
            messagebox.showwarning("Vínculo Catálogo", "Precio no encontrado en el catálogo.")

    def recalculate_item_cost(self, item_id):
        self.model.calculate_total_cost(item_id)
        # Recorrer hacia arriba para actualizar los padres
        current_item = self.model.cost_items.get(item_id)
        while current_item and current_item.parent_id is not None:
            current_item = self.model.cost_items.get(current_item.parent_id)
            if current_item:
                self.model.calculate_total_cost(current_item.id) # Recalcular el padre
        if self.view and self.view.winfo_exists():
            self.view.update_treeview() # Refrescar la vista después del cálculo

    def calculate_all_totals(self):
        # Este método se llama para recalcular todo el árbol de costos
        # Es vital que el calculate_total_cost del modelo se llame en un orden
        # que garantice que los hijos se calculan antes que los padres.
        # Una forma es obtener todos los ítems y ordenarlos por "profundidad" descendente
        # o, como ya lo hace calculate_total_cost de forma recursiva, solo llama a los ítems raíz.
        for root_item in self.model.get_root_items():
            self.model.calculate_total_cost(root_item.id)
        if self.view and self.view.winfo_exists():
            self.view.update_treeview()

    def update_quantities_from_ifc(self):
        if not self.model.ifc_model_data:
            messagebox.showwarning("Modelo IFC", "No hay un modelo IFC cargado.")
            return

        updated_count = 0
        for item_id, item_model in list(self.model.cost_items.items()): # Usar list() para evitar errores si el diccionario cambia durante la iteración
            if item_model.ifc_guid:
                quantity, unit = self.model.get_ifc_quantity(item_model.ifc_guid)
                if quantity is not None:
                    self.model.update_item(item_id, quantity=quantity, unit_name=unit)
                    self.recalculate_item_cost(item_id)
                    updated_count += 1
        messagebox.showinfo("Actualización IFC", f"Se actualizaron {updated_count} cantidades de ítems vinculados al IFC.")

    def save_budget(self, file_path):
        # Serializar la EDC a un formato que preserve la jerarquía
        # Por simplicidad, se guarda un diccionario plano con la estructura padre-hijo
        serializable_data = {
            item.id: {
                "parent_id": item.parent_id,
                "name": item.name,
                "description": item.description,
                "cost_type": item.cost_type,
                "unit_cost": item.unit_cost,
                "unit_name": item.unit_name,
                "quantity": item.quantity,
                "total_cost": item.total_cost,
                "ifc_guid": item.ifc_guid,
                "ifc_entity_type": item.ifc_entity_type,
                "catalog_price_id": item.catalog_price_id
            } for item in self.model.cost_items.values()
        }
        with open(file_path, 'w') as f:
            json.dump(serializable_data, f, indent=4)
        messagebox.showinfo("Guardar Presupuesto", f"Presupuesto guardado en {file_path}")


    def load_budget(self, file_path):
        try:
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            
            # Limpiar el modelo actual antes de cargar
            self.model.cost_items = {}
            self.model.next_id = 1

            # Primero cargar todos los items planos para que los IDs existan
            # Luego construir la jerarquía
            temp_items = {}
            max_id = 0
            for item_id_str, item_data in loaded_data.items():
                item_id = int(item_id_str)
                temp_items[item_id] = CostItemModel(id=item_id, **item_data)
                max_id = max(max_id, item_id)
            
            self.model.cost_items = temp_items
            self.model.next_id = max_id + 1

            # Reconstruir los 'children'
            for item in self.model.cost_items.values():
                if item.parent_id is not None and item.parent_id in self.model.cost_items:
                    self.model.cost_items[item.parent_id].children.append(item.id)
            
            self.calculate_all_totals() # Recalcular después de cargar
            if self.view and self.view.winfo_exists():
                self.view.update_treeview()
            messagebox.showinfo("Cargar Presupuesto", f"Presupuesto cargado desde {file_path}")

        except FileNotFoundError:
            messagebox.showerror("Error de Carga", "Archivo no encontrado.")
        except json.JSONDecodeError:
            messagebox.showerror("Error de Carga", "Formato de archivo JSON inválido.")
        except Exception as e:
            messagebox.showerror("Error de Carga", f"Ocurrió un error al cargar el presupuesto: {e}")