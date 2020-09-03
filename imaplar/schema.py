# configuration schema
config = {
    "servers": {
        "type": "dict",
        "required": True,
        "keysrules": {
            "type": "string",
            "empty": False
        },
        "valuesrules": {
            "type": "dict",
            "schema": {
                "tls": {
                    "type": "dict",
                    "schema": {
                        "mode": {
                            "type": "string",
                            "allowed": ["disabled", "enabled", "starttls"],
                            "default": "enabled"
                        },
                        "verify_mode": {
                            "type": "string",
                            "allowed": ["none", "optional", "required"]
                        },
                        "check_hostname": {
                            "type": "boolean"
                        },
                        "cafile": {
                            "type": "string",
                            "empty": False
                        },
                        "capath": {
                            "type": "string",
                            "empty": False
                        },
                        "cadata": {
                            "type": "string",
                            "empty": False
                        },
                    }
                },
                "authentication": {
                    "type": "dict",
                    "schema": {
                        "method": {
                            "type": "string",
                            "required": True,
                            "oneof": [
                                {
                                    "allowed": ["login"],
                                    "dependencies": [
                                        "username",
                                        "password"
                                    ]
                                },
                                {
                                    "allowed": ["plain"],
                                    "dependencies": [
                                        "identity",
                                        "password",
                                        "authorization_identity"
                                    ]
                                },
                                {
                                    "allowed": ["oauth2"],
                                    "dependencies": [
                                        "user",
                                        "access_token",
                                        "mech",
                                        "vendor"
                                    ]
                                },
                            ]
                        },
                        "username": {
                            "type": "string",
                            "empty": False,
                        },
                        "password": {
                            "type": "string",
                            "empty": False,
                        },
                        "identity": {
                            "type": "string",
                            "empty": False,
                        },
                        "authorization_identity": {
                            "type": "string",
                            "empty": False,
                            "nullable": True,
                            "default": None
                        },
                        "user": {
                            "type": "string",
                            "empty": False,
                        },
                        "access_token": {
                            "type": "string",
                            "empty": False,
                        },
                        "mech": {
                            "type": "string",
                            "empty": False,
                            "default": "XOAUTH2"
                        },
                        "vendor": {
                            "type": "string",
                            "empty": False,
                            "nullable": True,
                            "default": None
                        }
                    }
                },
                "default": {
                    "type": "boolean",
                    "default": False
                },
                "port": {
                    "type": "integer",
                    "min": 1,
                    "max": 65535,
                },
                "poll": {
                    "type": "integer",
                    "min": 0,
                    "default": 0
                },
                "mailboxes": {
                    "type": "dict",
                    "keysrules": {
                        "type": "string",
                        "empty": False
                    },
                    "valuesrules": {
                        "type": "string",
                        "empty": False
                    }
                }
            }
        }
    },
    "policies": {
        "type": "dict",
        "required": True,
        "keysrules": {
            "type": "string",
            "empty": False
        },
        "valuesrules": {
            "type": "string",
        }
    },
    "logging": {
        "type": "dict",
    }
}
