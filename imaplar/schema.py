#
# Copyright (C) 2017-2020 Michael Paddon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

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
                                        "login_username",
                                        "login_password"
                                    ]
                                },
                                {
                                    "allowed": ["plain"],
                                    "dependencies": [
                                        "plain_identity",
                                        "plain_password",
                                        "plain_authorization_identity"
                                    ]
                                },
                                {
                                    "allowed": ["oauth2"],
                                    "dependencies": [
                                        "oauth2_user",
                                        "oauth2_access_token",
                                        "oauth2_mech",
                                        "oauth2_vendor"
                                    ]
                                },
                            ]
                        },
                        "login_username": {
                            "type": "string",
                            "empty": False,
                        },
                        "login_password": {
                            "type": "string",
                            "empty": False,
                        },
                        "plain_identity": {
                            "type": "string",
                            "empty": False,
                        },
                        "plain_password": {
                            "type": "string",
                            "empty": False,
                        },
                        "plain_authorization_identity": {
                            "type": "string",
                            "empty": False,
                            "nullable": True,
                            "default": None
                        },
                        "oauth2_user": {
                            "type": "string",
                            "empty": False,
                        },
                        "oauth2_access_token": {
                            "type": "string",
                            "empty": False,
                        },
                        "oauth2_mech": {
                            "type": "string",
                            "empty": False,
                            "default": "XOAUTH2"
                        },
                        "oauth2_vendor": {
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
                    "default": 60
                },
                "idle": {
                    "type": "integer",
                    "min": 0,
                    "default": 900
                },
                "min_backoff": {
                    "type": "integer",
                    "min": 1,
                    "default": 1
                },
                "max_backoff": {
                    "type": "integer",
                    "min": 1,
                    "default": 300
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
                },
                "parameters": {
                    "type": "dict",
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
