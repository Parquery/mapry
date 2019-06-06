"""Define JSON schemas for the validation."""

GRAPH = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "definitions": {
        "Graph": {
            "type": "object",
            "description": "defines a mapry schema of an object graph.",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "gives the name of the object graph.",
                    "pattern": "^[A-Z][A-Za-z0-9]*"
                },
                "description": {
                    "type": "string",
                    "description": "describes the object graph "
                    "(starts with a verb and ends with a dot).",
                    "pattern": "^[a-z]+.*\\.$"
                },
                "cpp": {
                    "$ref": "#/definitions/Cpp"
                },
                "go": {
                    "$ref": "#/definitions/Go"
                },
                "py": {
                    "$ref": "#/definitions/Py"
                },
                "classes": {
                    "type": "array",
                    "description": "defines the classes, "
                    "i.e. referencable data strucures.",
                    "items": {
                        "$ref": "#/definitions/Class"
                    }
                },
                "embeds": {
                    "type": "array",
                    "description": "defines the embeddable data structures.",
                    "items": {
                        "$ref": "#/definitions/Embed"
                    }
                },
                "properties": {
                    "type": "object",
                    "description": "defines the properties of "
                    "the object graph.",
                    "additionalProperties": {
                        "$ref": "#/definitions/Property"
                    }
                }
            },
            "required": ["name", "description"],
            "additionalProperties": False
        },
        "Cpp": {
            "type": "object",
            "description": "specifies parameters for generating C++ code.",
            "properties": {
                "namespace": {
                    "type": "string",
                    "description":
                    "indicates the namespace of the generated code.",
                    "pattern":
                    "^[a-zA-Z][a-zA-Z0-9_]*(::[a-zA-Z][a-zA-Z0-9_]*)*$"
                },
                "path_as": {
                    "type": "string",
                    "description":
                    "defines the type of the paths in the generated code.",
                    "enum":
                    ["std::filesystem::path", "boost::filesystem::path"]
                },
                "optional_as": {
                    "type":
                    "string",
                    "description":
                    "defines the type of the optional properties "
                    "in the generated code.",
                    "enum": [
                        "boost::optional", "std::optional",
                        "std::experimental::optional"
                    ]
                },
                "datetime_library": {
                    "type":
                    "string",
                    "description":
                    "defines the date/time library to use for "
                    "date, datetime, time and time zone "
                    "manipulation.",
                    "enum": ["ctime", "date.h"]
                },
                "indention": {
                    "type": "string",
                    "description":
                    "defines the indention of the generated code."
                    "Defaults to two spaces.",
                    "pattern": "^[ \t]*$"
                }
            },
            "required":
            ["namespace", "path_as", "optional_as", "datetime_library"],
            "additionalProperties": False,
        },
        "Go": {
            "type": "object",
            "description": "specifies parameters for generating Go code.",
            "properties": {
                "package": {
                    "type": "string",
                    "description":
                    "indicates the package of the generated code.",
                    "pattern": "^[a-zA-Z][a-zA-Z0-9_]*"
                }
            },
            "required": ["package"],
            "additionalProperties": False,
        },
        "Py": {
            "type": "object",
            "description": "specifies parameters for generating Python code.",
            "properties": {
                "module_name": {
                    "type":
                    "string",
                    "description":
                    "specifies the fully qualified base module name "
                    "of the generated code.",
                    "pattern":
                    r"^[a-zA-Z][a-zA-Z0-9_]*(\.[a-zA-Z][a-zA-Z0-9_]*)*$"
                },
                "path_as": {
                    "type": "string",
                    "description":
                    "defines the type of the paths in the generated code.",
                    "enum": ["str", "pathlib.Path"]
                },
                "timezone_as": {
                    "type": "string",
                    "description": "defines the type of the time zones "
                    "in the generated code.",
                    "enum": ["str", "pytz.timezone"]
                },
                "indention": {
                    "type": "string",
                    "description":
                    "defines the indention of the generated code. "
                    "Defaults to four spaces.",
                    "pattern": "^[ \t]*$"
                }
            },
            "required": ['module_name', 'path_as', 'timezone_as'],
            "additionalProperties": False
        },
        "Class": {
            "type": "object",
            "description":
            "defines a class, i.e. a referencable data structure.",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "gives the name of the class in Snake_case.",
                    "pattern": "^[A-Z]([a-zA-Z0-9_]*[a-zA-Z0-9])?$"
                },
                "description": {
                    "type": "string",
                    "description": "describes the class "
                    "(starts with a verb and ends with a dot).",
                    "pattern": "^[a-z]+.*\\.$"
                },
                "plural": {
                    "type": "string",
                    "description":
                    "gives the plural of the class in Snake_case. "
                    "If omitted, automatically inferred.",
                    "pattern": "^[A-Z]([a-zA-Z0-9_]*[a-zA-Z0-9])?$"
                },
                "id_pattern": {
                    "type":
                    "string",
                    "description":
                    "defines the regular expression for the identifiers "
                    "of the class instances."
                },
                "properties": {
                    "type": "object",
                    "description": "defines the properties of the class.",
                    "additionalProperties": {
                        "$ref": "#/definitions/Property"
                    }
                }
            },
            "required": ["name", "description"],
            "additionalProperties": False
        },
        "Embed": {
            "type": "object",
            "description": "defines an embeddable data structure.",
            "properties": {
                "name": {
                    "type": "string",
                    "description":
                    "gives the name of the embeddable data structure.",
                    "pattern": "^[A-Z]([A-Za-z0-9_]*[a-zA-Z0-9])?"
                },
                "description": {
                    "description": "describes the embeddable data structure "
                    "(starts with a verb and ends with a dot).",
                    "type": "string",
                    "pattern": "^[a-z]+.*\\.$"
                },
                "properties": {
                    "type": "object",
                    "description":
                    "defines the properties of the embeddable structure.",
                    "additionalProperties": {
                        "$ref": "#/definitions/Property"
                    }
                }
            },
            "required": ["name", "description"],
            "additionalProperties": False
        },
        "Property": {
            "type": "object",
            "description": "defines a property of a data structure.",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "describes the property."
                },
                "type": {
                    "type": "string",
                    "description": "indicates the type of the property.",
                    "pattern": "[A-Za-z][A-Za-z_0-9]*"
                },
                "json": {
                    "type":
                    "string",
                    "description":
                    "defines the property name in the JSONable object."
                },
                "optional": {
                    "type":
                    "boolean",
                    "description":
                    "defines whether the property is optional. "
                    "The default value is false."
                }
            },
            "required": ["description", "type"],
            "additionalProperties": True
        }
    },
    "$ref": "#/definitions/Graph"
}

# Schemas for type definitions
BOOLEAN = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        }
    }
}

INTEGER = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "minimum": {
            "type": "integer",
            "description": "indicates the minimum allowed value."
        },
        "exclusive_minimum": {
            "type":
            "boolean",
            "description":
            "indicates whether the minimum is exclusive; "
            "if unspecified, defaults to false."
        },
        "maximum": {
            "type": "integer",
            "description": "indicates the maximum allowed value."
        },
        "exclusive_maximum": {
            "type":
            "boolean",
            "description":
            "indicates whether the maximum is exclusive; "
            "if unspecified, defaults to false."
        }
    }
}

FLOAT = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "minimum": {
            "type": "number",
            "description": "indicates the minimum allowed value."
        },
        "exclusive_minimum": {
            "type": "boolean",
            "description": "indicates whether the minimum is exclusive."
        },
        "maximum": {
            "type": "number",
            "description": "indicates the maximum allowed value."
        },
        "exclusive_maximum": {
            "type": "boolean",
            "description": "indicates whether the maximum is exclusive."
        }
    }
}

STRING = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "pattern": {
            "type": "string",
            "description": "gives the expected string pattern."
        }
    }
}

PATH = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "pattern": {
            "type": "string",
            "description": "gives the expected path pattern."
        }
    }
}

DATE = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "format": {
            "type": "string",
            "description": "gives the expected date format."
        }
    }
}

TIME = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "format": {
            "type": "string",
            "description": "gives the expected time format."
        }
    }
}

DATETIME = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "format": {
            "type": "string",
            "description": "gives the expected date-time format."
        }
    }
}

TIME_ZONE = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        }
    }
}

DURATION = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        }
    }
}

ARRAY = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "values": {
            "type": "object",
            "description": "gives the type of the array values."
        },
        "minimum_size": {
            "type": "integer",
            "description": "indicates the inclusive minimum size of the array.",
            "minimum": 0
        },
        "maximum_size": {
            "type": "integer",
            "description": "indicates the inclusive maximum size of the array.",
            "minimum": 0
        }
    },
    "required": ["values"]
}

MAP = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "description": "indicates the type of the value."
        },
        "description": {
            "type": "string",
            "description": "describes the value."
        },
        "values": {
            "type": "object",
            "description": "gives the type of the map values."
        },
    },
    "required": ["values"]
}

TYPE_TO_SCHEMA = {
    'boolean': BOOLEAN,
    'integer': INTEGER,
    'float': FLOAT,
    'string': STRING,
    'path': PATH,
    'date': DATE,
    'time': TIME,
    'datetime': DATETIME,
    'time_zone': TIME_ZONE,
    'duration': DURATION,
    'array': ARRAY,
    'map': MAP
}
