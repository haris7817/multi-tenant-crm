"""drf-spectacular extension so API-key auth shows up in the OpenAPI docs (10.6)."""
from drf_spectacular.extensions import OpenApiAuthenticationExtension


class ApiKeyScheme(OpenApiAuthenticationExtension):
    target_class = "apps.apikeys.authentication.ApiKeyAuthentication"
    name = "ApiKeyAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "API key auth. Format: `Api-Key crm_<prefix>_<secret>`",
        }
