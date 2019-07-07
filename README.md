# pickysettings
Python Project Configuration Manager for System and User Overridable Configuration

## Story

`pickysettings` is a Django inspired object oriented settings manager for Python projects that allows a developer to specify project settings and control how they are overridden by users of the project.

The project is currently in development and should not be used.

## Use Cases

For a simple example of the idea, consider a `settings.dev.py` file with the following contents:

```python
CONNECTION = fields.SetField(
    name='CONNECTION',
    LIMIT_PER_HOST=fields.PositiveIntField(
        max=10,
        default=5,
        help="Need to retrieve from aiohttp docs."
    ),
    CONNECTION_TIMEOUT=fields.PositiveIntField(
        max=20,
        default=5,
        help="Need to retrieve from aiohttp docs."
    ),
    CONNECTION_LIMIT=fields.PositiveIntField(
        max=100,
        default=0,
        help="Need to retrieve from aiohttp docs."
        configurable=False,
    ),
    configurable=True
)
```

This defines a project setting `CONNECTION` who attributes are set when the settings are accessed.  Currently, `pickysettings` only has the optionality for lazy initialization and access of the settings:

```python
from pickysettings import settings

# Attributes Not Accessed Yet, Settings Not Loaded
>>> settings
>>> {}

# Attributes Accessed, Settings Loaded
>>> settings.connection
>>> {
      'LIMIT_PER_HOST': <pickysettings.fields.PositiveIntField object at 0x10f3faf60>,
      'CONNECTION_TIMEOUT': <pickysettings.fields.PositiveIntField object at 0x10f3fafd0>,
      'CONNECTION_LIMIT': <pickysettings.fields.PositiveIntField object at 0x10f4080f0>
    }
```

### Internal Package Access

Accessing a specific settings attribute is done without case sensitivity, and for fields that are meant for collecting a group of settings together, the attribute access can also be by key:

```python
>>> settings.connection.limit_per_host
>>> 5
>>> settings.connection.LIMIT_PER_HOST
>>> 5
>>> settings.connection['limit_per_host']
>>> 5
```

### External Package User Configuration

`pickysettings` is really intended for packages developed with the intention of allowing users to configure certain settings before use.  The manner in which users can configure specific settings is flexible, and can be done at multiple levels of the nested settings tree:

```python
from pickysettings import settings

>>> settings.configure({'connection': {'limit_per_host':9}})
>>> settings.connection.as_dict()
>>> {
      'LIMIT_PER_HOST': 9,
      'CONNECTION_TIMEOUT': 5,
      'CONNECTION_LIMIT': 0,
    }

>>> settings.connection.configure(limit_per_host=9)
>>> settings.connection.as_dict()
>>> {
      'LIMIT_PER_HOST': 9,
      'CONNECTION_TIMEOUT': 5,
      'CONNECTION_LIMIT': 0,
    }
```

Furthermore, certain collection fields allow non-destructive configuration.  In other words, single fields can be configured in the set indepeendently of other fields, without having to configure the entire field at once.

```python
>>> settings.configure({'connection': {'connection_limit': 1}}
>>> settings.connection.as_dict()
>>> {
      'LIMIT_PER_HOST': 9,
      'CONNECTION_TIMEOUT': 5,
      'CONNECTION_LIMIT': 0,
    }
```

The validation rules built into `pickysettings` and configuration settings of individual fields give the developer control over exactly what fields the user can configure, and which fields are non-configurable and must be kept constant for package users.  This allows the developer to introduce settings and configurations that they want the ability to control, without allowing package users to change those configuration settings themselves.

This project is a WIP, but additional validation and customization of how and when fields can be configured will continue to be incorporated as the project progresses.

