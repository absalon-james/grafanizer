from query_dsl import validate_query

metric = {
    'type': {
        'type': 'string',
        'allowed': ['simple', 'complex'],
        'required': True
    },
    'query': {
        'type': 'string',
        'validator': validate_query,
        'dependencies': {
            'type': ['simple']
        }
    },
    'named-metrics': {
        'type': 'dict',
        'keyschema': {
            "type": "dict",
            "schema": {
                "query": {
                    'type': 'string',
                    'validator': validate_query,
                    'required': True
                },
                "target": {
                    'type': 'string',
                    'required': True
                }
            }
        },
        'dependencies': {
            'type': ['complex']
        }
    },
    'multi-entity': {
        'type': 'boolean',
        'dependencies': {
            'type': ['complex']
        }
    },
    'target': {
        'required': True,
        'type': 'string'
    }
}

target = {
    'type': 'dict',
    'nullable': False,
    'schema': {
        'target': {
            'type': 'string',
            'required': True,
            'nullable': False
        },
        'hide': {
            'type': 'boolean',
            'required': False,
            'nullable': False
        }
    }
}

grid = {
    # Assuming integer
    'leftMax': {
        'type': 'integer',
        'nullable': True
    },

    # Assuming integer
    'rightMax': {
        'type': 'integer',
        'nullable': True
    },

    # Assuming integer
    'leftMin': {
        'type': 'integer',
        'nullable': True
    },

    # Assuming integer
    'rightMin': {
        'type': 'integer',
        'nullable': True
    },

    # Assuming integer
    'threshold1': {
        'type': 'integer',
        'nullable': True
    },

    # Assuming integer
    'threshold2': {
        'type': 'integer',
        'nullable': True
    },

    # Color for threshold 1. Defaults to 'rgba(216, 200, 27, 0.27)'
    'threshold1Color': {
        'type': 'string',
        'nullable': False
    },

    # Color for threshold 2. Defaults to 'rgba(234, 112, 112, 0.22)'
    'threshold2Color': {
        'type': 'string',
        'nullable': False
    }
}

# This is currently not used. There are more fields in play than are
# listed here.
legend = {
    # Show/hide legend - Defaults to true
    'show': {
        'type': 'boolean',
        'nullable': False
    },

    # Show legend values - Defaults to false
    'values': {
        'type': 'boolean',
        'nullable': False
    },

    # Show min value - Defaults to false
    'min': {
        'type': 'boolean',
        'nullable': False
    },

    # Show max value - Defaults to false
    'max': {
        'type': 'boolean',
        'nullable': False
    },

    # Show current value - Defaults to false
    'current': {
        'type': 'boolean',
        'nullable': False
    },

    # Show total value - Defaults to false
    'total': {
        'type': 'boolean',
        'nullable': False
    },

    # Show average value - Defaults to false
    'avg': {
        'type': 'boolean',
        'nullable': False
    }
}

panel = {
    # Unsure about defaults
    'span': {
        'type': 'integer',
        'nullable': False,
        'required': True
    },

    # Defaults to true
    'editable': {
        'type': 'boolean',
        'nullable': False
    },

    # Type of panel. either text or graph
    'type': {
        'type': 'string',
        'allowed': ['graph', 'text'],
        'required': True
    },

    # Unsure about defaults
    'id': {
        'type': 'integer',
        'nullable': False,
        'required': True
    },

    # Unsure about defaults
    'error': {
        'type': 'boolean'
    },

    # Text panel #############################################################

    # Defaults to 'default title'
    'title': {
        'type': 'string',
        'nullable': False
    },

    # Mode - defaults to 'markdown'
    'mode': {
        'type': 'string',
        'nullable': False,
        'allowed': ['markdown', 'html', 'text']
    },

    # Content - defaults to ""
    'content': {
        'type': 'string',
        'nullable': False
    },

    # Style - defaults to {}
    'style': {
        'type': 'dict',
        'nullable': False
    },

    'height': {},

    # Graph panel ############################################################

    # leftYAxisLabel
    'leftYAxisLabel': {},

    # Datasource - defaults to null. Uses default datasource if null
    'datasource': {
        'type': 'string',
        'nullable': True
    },

    # Sets client side flot or native graphite renderer. Defaults to 'flot'
    'renderer': {
        'type': 'string',
        'nullable': False
    },

    # Show/hide x-axis. Defaults to true
    'x-axis': {
        'type': 'boolean',
        'nullable': False
    },

    # Show/hide y-axis. Defaults to true
    'y-axis': {
        'type': 'boolean',
        'nullable': False
    },

    # Defaults to ['short', 'short']
    'y_formats': {
        'type': 'list',
        'nullable': False,
        'items': [
            {'type': 'string'},
            {'type': 'string'}
        ]
    },

    # Grid options
    'grid': {
        'type': 'dict',
        'nullable': False,
        'schema': grid
    },

    # Show/hide lines - defaults to true
    'lines': {
        'type': 'boolean',
        'nullable': False
    },

    # Fill factor - Defaults to 0
    'fill': {
        'type': 'integer',
        'nullable': False
    },

    # Line width in pixels. Defaults to 1
    'linewidth': {
        'type': 'integer',
        'nullable': False
    },

    # Show/hide points Defaults to false
    'points': {
        'type': 'boolean',
        'nullable': False
    },

    # Point radius in pixels. Defaults to 5
    'pointradius': {
        'type': 'integer',
        'nullable': False
    },

    # Show/hide bars. Defaults to false
    'bars': {
        'type': 'boolean',
        'nullable': False
    },


    # Enable/disable stacking. Defaults to false
    'stack': {
        'type': 'boolean',
        'nullable': False
    },

    # Stack percentage mode. Defaults to false
    'percentage': {
        'type': 'boolean',
        'nullable': False
    },


    # Legend options
    'legend': {
        'type': 'dict',
        'nullable': False
    },

    # How null points are handled. Defaults to 'connected'
    'nullPointMode': {
        'type': 'string',
        'nullable': False
    },

    # Enable/disable staircase line mode
    'steppedLine': {
        'type': 'boolean',
        'nullable': False
    },

    # Tool tip options - Defaults to
    # {'value_type': 'cumulative', 'shared': False}
    'tooltip': {
        'type': 'dict',
        'nullable': False
    },

    # Metrics - Not used by grafana - used by template to
    # produce metric queries
    'metrics': {
        'type': 'list',
        'nullable': False,
        'schema': {
            'type': 'dict',
            'nullable': False,
            'schema': metric
        }
    },

    # Metric queries - Defaults to [{}]
    'targets': {
        'type': 'list',
        'schema': target
    },

    # Alias colors. Defaults to {}
    'aliasColors': {
        'type': 'dict',
        'nullable': False
    },

    # Other style overrides. Defaults to []
    'seriesOverrides': {
        'type': 'list',
        'nullable': False
    },

    # Unsure of default
    'annotate': {
        'type': 'dict',
        'nullable': False
    },

    # Resolution. related to number of datapoints. unsure of default
    'resolution': {
        'type': 'integer',
        'nullable': False
    },

    # Unsure of default
    'scale': {
        'type': 'float',
        'nullable': False
    },

    # Zero fill - unsure of meaning and default
    'zerofill': {
        'type': 'boolean',
        'nullable': False
    }
}

row = {
    # Defaults to 'Row' in grafana
    'title': {
        'type': 'string',
        'nullable': False
    },

    # Defaults to '150px' in grafana
    'height': {
        'type': 'string',
        'nullable': False
    },

    # Defaults to True in grafana
    'editable': {
        'type': 'boolean',
        'nullable': False
    },

    # Default to False in grafana
    'collapse': {
        'type': 'boolean',
        'nullable': False
    },

    # Defaults to empty list in grafana
    'panels': {
        'type': 'list',
        'nullable': False,
        'schema': {
            'type': 'dict',
            'schema': panel
        }
    }
}

dashboard = {
    # Set to null by default in grafana
    'id': {
        'type': 'string',
        'nullable': True,
    },

    # Set to "No Title" by default in grafana
    'title': {
        'type': 'string',
        'nullable': False
    },

    # Is set to original title by default in grafana
    'originalTitle': {
        'type': 'string',
        'nullable': False
    },

    # Set to 'dark' by default in grafana
    'style': {
        'type': 'string',
        'nullable': False
    },

    # Set to 'browser' by default in grafana
    'timezone': {
        'type': 'string',
        'nullable': False,
    },

    # Set to True by default in grafana
    'editable': {
        'type': 'boolean',
        'nullable': False
    },

    # Set to False by default in grafana
    'hideControls': {
        'type': 'boolean',
        'nullable': False
    },

    # Set to Empty list by default in grafana
    'rows': {
        'type': 'list',
        'nullable': False,
        'schema': {
            'type': 'dict',
            'schema': row
        }
    },

    # Set to Empty list by default
    'nav': {
        'type': 'list',
        'nullable': False
    },

    # Set to {'from':'now-6h', 'to': 'now'} by default
    'time': {
        'type': 'dict',
        'nullable': False,
    },

    # Set to empty list by default
    'templating': {
        'type': 'dict',
        'nullable': False,
    },

    # Set to empty list by default
    'annotations': {
        'type': 'dict',
        'nullable': False
    },

    # No default yet
    'refresh': {},

    # Set to 0 by default
    'version': {
        'type': 'integer'
    },

    'tags': {}
}

template = {
    'type': {
        'required': True,
        'type': 'string',
        'allowed': ['SingleEntity', 'MultiEntity']
    },
    'user': {
        'type': 'string'
    },
    'group': {
        'type': 'string'
    },
    'dashboard': {
        'required': True,
        'type': 'dict',
        'schema': dashboard
    },

    # Set to empty list by default in grafana
    'tags': {
        'type': 'list',
        'schema': {
            'type': 'string'
        }
    },
}

entity_types = {
    'types': {
        'type': 'dict',
        'keyschema': {
            'type': 'string',
            'validator': validate_query
        }
    }
}
