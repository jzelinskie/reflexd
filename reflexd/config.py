import yaml
from jsonschema import ValidationError, validate


class SchemaValidationError(ValidationError):
    pass


SCHEMA = """
type: object
required: [ reflexd ]
properties:
  reflexd:
    type: object
    required: [ v1 ]
    properties:
      v1:
        type: object
        required: [ directories ]
        additionalProperties: false
        properties:
          directories:
            type: array
            items:
              type: object
              required: [ path, recursive, options ]
              additionalProperties: false
              properties:
                path:
                  type: string
                recursive:
                  type: boolean
                options:
                  type: object
                  additionalProperties: false
                  properties:
                    add_paused:
                      type: boolean
                    auto_managed:
                      type: boolean
                    download_location:
                      type: string
                    max_connections:
                      type: integer
                    max_download_speed:
                      type: number
                    max_upload_slots:
                      type: integer
                    max_upload_speed:
                      type: number
                    move_completed:
                      type: boolean
                    move_completed_path:
                      type: string
                    pre_allocate_storage:
                      type: boolean
                    prioritize_first_last_pieces:
                      type: boolean
                    remove_at_ratio:
                      type: boolean
                    sequential_download:
                      type: boolean
                    shared:
                      type: boolean
                    stop_at_ratio:
                      type: boolean
                    stop_ratio:
                      type: number
                    super_seeding:
                      type: boolean
"""

FILENAME = "config.yaml"


def validate_dict(config_dict: dict):
    try:
        validate(config_dict, yaml.load(SCHEMA, Loader=yaml.SafeLoader))
    except ValidationError as e:
        raise SchemaValidationError(e)
