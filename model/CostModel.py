# cost_module/model.py
import mysql.connector # O SQLAlchemy
import ifcopenshell

class CostItemModel:
    def __init__(self, id, name, parent_id=None, description="", cost_type="", 
                 unit_cost=0.0, unit_name="", quantity=0.0, total_cost=0.0,
                 ifc_guid=None, ifc_entity_type=None, catalog_price_id=None):
        self.id = id
        self.parent_id = parent_id
        self.name = name
        self.description = description
        self.cost_type = cost_type
        self.unit_cost = unit_cost
        self.unit_name = unit_name
        self.quantity = quantity
        self.total_cost = total_cost
        self.ifc_guid = ifc_guid
        self.ifc_entity_type = ifc_entity_type
        self.catalog_price_id = catalog_price_id
        self.children = [] # Para construir la jerarquía en memoria

class CostModel:
    def __init__(self, db_config):
        self.cost_items = {} # Dict para acceso rápido por ID
        self.next_id = 1
        self.db_config = db_config
        self.ifc_model_data = None # Almacenará el modelo IFC

    def set_ifc_model(self, ifc_model):
        self.ifc_model_data = ifc_model

    def add_item(self, **kwargs):
        item = CostItemModel(id=self.next_id, **kwargs)
        self.cost_items[self.next_id] = item
        self.next_id += 1
        if item.parent_id and item.parent_id in self.cost_items:
            self.cost_items[item.parent_id].children.append(item.id)
        return item.id

    def update_item(self, item_id, **kwargs):
        item = self.cost_items.get(item_id)
        if item:
            for key, value in kwargs.items():
                setattr(item, key, value)
        return item

    def delete_item(self, item_id):
        item = self.cost_items.pop(item_id, None)
        if item and item.parent_id and item.parent_id in self.cost_items:
            self.cost_items[item.parent_id].children.remove(item.id)
        # Recursivamente eliminar hijos
        for child_id in list(item.children): # Usar list para modificar mientras iteras
            self.delete_item(child_id)
        return item

    def get_root_items(self):
        return [item for item in self.cost_items.values() if item.parent_id is None]

    def get_catalog_prices(self):
        # Conexión a la DB MySQL y recuperación de precios
        try:
            cnx = mysql.connector.connect(**self.db_config)
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT id, concepto, unidad, costo_unitario, categoria FROM precios_catalogo")
            prices = cursor.fetchall()
            cursor.close()
            cnx.close()
            return prices
        except mysql.connector.Error as err:
            print(f"Error al conectar/consultar MySQL: {err}")
            return []

    def get_ifc_quantity(self, ifc_guid):
        # Lógica de IfcOpenShell para obtener cantidad del modelo IFC cargado
        # (Implementa la función get_ifc_quantity descrita anteriormente)
        return ifc_model_logic.get_ifc_quantity(self.ifc_model_data, ifc_guid) # ifc_model_logic es un módulo helper

    def calculate_total_cost(self, item_id):
        item = self.cost_items.get(item_id)
        if not item:
            return 0.0

        if item.children: # Es un ítem padre, sumar hijos
            total = sum(self.calculate_total_cost(child_id) for child_id in item.children)
            item.total_cost = total
        elif item.quantity is not None and item.unit_cost is not None: # Es un ítem hoja con cantidad y costo unitario
            item.total_cost = item.quantity * item.unit_cost
        else: # Ítem hoja sin suficiente información para cálculo directo (ej. costo fijo)
            # Asume que total_cost ya fue asignado manualmente o es 0
            pass 
        return item.total_cost

    def calculate_all_totals(self):
        # Asegúrate de calcular desde los hijos hacia los padres
        # Podrías necesitar un algoritmo que recorra los ítems de abajo hacia arriba
        # Para simplificar, podrías recalcular todos los ítems cada vez.
        for item_id in self.cost_items:
            self.calculate_total_cost(item_id)