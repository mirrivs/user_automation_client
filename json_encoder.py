import json


class EnumEncoder(json.JSONEncoder):
    """
    A custom JSON encoder that handles SerializableEnum objects.
    """

    def default(self, obj):
        if isinstance(obj, EnumEncoder):
            return obj.value
        return super().default(obj)
