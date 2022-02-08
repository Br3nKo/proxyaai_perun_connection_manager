from typing import List
import logging
import yaml


class AttributeUtils:

    CONFIG_FILE_NAME = "config.yaml"
    INTERNAL_ATTR_NAME = "internal_attr_name"
    LDAP = "ldap"
    RPC = "rpc"
    TYPE = "type"

    @staticmethod
    def parse_config_yaml(input_file_path: str) -> dict[str, dict[str, str]]:
        with open(input_file_path, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as error:
                logging.warning(error, "occurred while parsing config file")

    config = parse_config_yaml.__func__(CONFIG_FILE_NAME)

    @classmethod
    def get_ldap_attr_name(cls, internal_attr_name: str) -> str:
        return cls.get_attr_name(internal_attr_name, cls.LDAP)

    @classmethod
    def get_rpc_attr_name(cls, internal_attr_name: str) -> str:
        return cls.get_attr_name(internal_attr_name, cls.RPC)

    @classmethod
    def get_attr_name(cls, internal_attr_name: str, interface: str) -> str:
        try:
            attr_names = cls.config[internal_attr_name]
            if interface in attr_names:
                return attr_names[interface]
        except KeyError:
            logging.warning(
                "perun:AttributeUtils: missing",
                internal_attr_name,
                "attribute in config.yaml file",
            )

    @classmethod
    def create_ldap_attr_name_type_map(
        cls, internal_attr_names: List[str]
    ) -> dict[str, dict[str, str]]:
        return cls.create_attr_name_type_map(internal_attr_names, cls.LDAP)

    @classmethod
    def create_rpc_attr_name_type_map(
        cls, internal_attr_names: List[str]
    ) -> dict[str, dict[str, str]]:
        return cls.create_attr_name_type_map(internal_attr_names, cls.RPC)

    @classmethod
    def create_attr_name_type_map(
        cls, internal_attr_names: List[str], interface: str
    ) -> dict[str, dict[str, str]]:
        result = {}

        for internal_attr_name in internal_attr_names:
            try:
                attr_names = cls.config[internal_attr_name]
                if interface in attr_names:
                    result[attr_names[interface]] = {
                        cls.INTERNAL_ATTR_NAME: internal_attr_name,
                        cls.TYPE: attr_names[cls.TYPE],
                    }
            except KeyError:
                logging.warning(
                    "perun:AttributeUtils: missing",
                    internal_attr_name,
                    "attribute in config.yaml file",
                )
        return result

    @classmethod
    def get_ldap_attr_names(
        cls, internal_attr_names: List[str]
    ) -> dict[str, str]:
        return cls.get_attr_names(internal_attr_names, cls.LDAP)

    @classmethod
    def get_rpc_attr_names(
        cls, internal_attr_names: List[str]
    ) -> dict[str, str]:
        return cls.get_attr_names(internal_attr_names, cls.RPC)

    @classmethod
    def get_attr_names(
        cls, internal_attr_names: List[str], interface: str
    ) -> dict[str, str]:
        result = {}

        for internal_attr_name in internal_attr_names:
            try:
                attr_names = cls.config[internal_attr_name]
                if interface in attr_names:
                    result[attr_names[interface]] = internal_attr_name
            except KeyError:
                logging.warning(
                    "perun:AttributeUtils: missing",
                    internal_attr_name,
                    "attribute in config.yaml file",
                )

        return result
