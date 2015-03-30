class Api:
    def __init__(self, api_name):
        self.name = api_name
        self.resources = {}

    def register_resource(self, resource):
        self.resources[resource._meta.resource_name] = resource

