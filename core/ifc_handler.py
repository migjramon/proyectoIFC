import ifcopenshell

class IfcHandler:
    """
    Clase principal para gestionar operaciones básicas sobre modelos IFC usando ifcopenshell.
    """

    def __init__(self):
        self.current_model = None

    def create_new_model(self):
        """
        Crea y retorna un nuevo modelo IFC vacío.
        """
        # Crea un modelo IFC vacío usando ifcopenshell
        self.current_model = ifcopenshell.file(schema="IFC4")
        return self.current_model

    def load_model(self, file_path):
        """
        Carga un modelo IFC desde el archivo especificado.
        """
        self.current_model = ifcopenshell.open(file_path)
        return self.current_model

    def save_model(self, file_path):
        """
        Guarda el modelo IFC actual en el archivo especificado.
        """
        if self.current_model:
            self.current_model.write(file_path)
            return True
        return False

    def get_entities(self, ifc_type=None):
        """
        Devuelve la lista de entidades del modelo actual.
        Si se especifica ifc_type, filtra por ese tipo (ejemplo: 'IfcWall').
        """
        if self.current_model:
            if ifc_type:
                return self.current_model.by_type(ifc_type)
            else:
                return self.current_model.entities
        return []

    def get_metadata(self):
        """
        Devuelve información básica del modelo actual.
        """
        if self.current_model:
            return {
                "schema": self.current_model.schema,
                "filename": getattr(self.current_model, "filename", None),
                "entity_count": len(self.current_model.entities)
            }
        return {}

# Nota: ifcopenshell debe estar instalado en tu entorno (pip install ifcopenshell).