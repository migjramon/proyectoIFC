import ifcopenshell

class IfcOperations:
    """
    Operaciones generales sobre modelos IFC usando ifcopenshell.
    """

    def get_entity_count(self, ifc_model):
        """
        Devuelve el número total de entidades en el modelo IFC.
        """
        if ifc_model:
            return len(ifc_model.entities)
        return 0

    def get_entities_by_type(self, ifc_model, ifc_type):
        """
        Devuelve todas las entidades de un tipo específico (ejemplo: 'IfcWall').
        """
        if ifc_model:
            return ifc_model.by_type(ifc_type)
        return []

    def get_schema(self, ifc_model):
        """
        Devuelve el esquema IFC del modelo (ejemplo: 'IFC2X3', 'IFC4').
        """
        if ifc_model:
            return getattr(ifc_model, "schema", None)
        return None

    def get_filename(self, ifc_model):
        """
        Devuelve el nombre de archivo del modelo IFC si está disponible.
        """
        if ifc_model:
            return getattr(ifc_model, "filename", None)
        return None

    def find_entity_by_id(self, ifc_model, entity_id):
        """
        Busca una entidad por su id interna en el modelo IFC.
        """
        if ifc_model:
            return ifc_model[entity_id]
        return None

    def remove_entity(self, ifc_model, entity):
        """
        Elimina una entidad del modelo IFC.
        """
        if ifc_model and entity:
            ifcopenshell.api.run("entity.delete", ifc_model, id=entity.id())
            return True
        return False

    # Puedes agregar más métodos según las necesidades de tu aplicación.