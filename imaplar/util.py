import importlib

def plugin(config, section, default_class = None):
    classpath = config.get(section, "class", fallback = None)
    if classpath:
        package, dot, name = classpath.rpartition(".")
        if package:
            module = importlib.import_module(package)
            return getattr(module, name)(config, section)
    return default_class(config, section) if default_class else None
