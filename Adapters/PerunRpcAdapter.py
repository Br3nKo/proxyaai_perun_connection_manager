import logging
from typing import List
from models import User, Group, Vo, Facility, HasIdAbstract, Resource
from utils import AttributeUtils

from Adapters import AdapterInterface
from perun_openapi.api.attributes_manager_api import AttributesManagerApi
from perun_openapi.api.facilities_manager_api import FacilitiesManagerApi
from perun_openapi.api.groups_manager_api import GroupsManagerApi
from perun_openapi.api.members_manager_api import MembersManagerApi
from perun_openapi.api.resources_manager_api import ResourcesManagerApi
from perun_openapi.api.users_manager_api import UsersManagerApi
from perun_openapi.api.vos_manager_api import VosManagerApi


class PerunRpcAdapter(AdapterInterface):
    def get_perun_user(self, idp_id: str, uids: List[str]) -> User:
        for uid in uids:
            user = UsersManagerApi.get_user_by_ext_source_name_and_ext_login(
                self, uid, idp_id
            )

            name = ""
            if user["titleBefore"]:
                name += user["titleBefore"] + " "
            if user["firstName"]:
                name += user["firstName"] + " "
            if user["middleName"]:
                name += user["middleName"] + " "
            if user["lastName"]:
                name += user["lastName"]
            if user["titleAfter"]:
                name += " " + user["titleAfter"]

            return User(user["id"], name)

    def get_member_groups(self, user: User, vo: Vo) -> List[Group]:
        member = MembersManagerApi.get_member_by_user(self, vo, user)
        member_groups = GroupsManagerApi.get_all_member_groups(
            self, member["id"]
        )

        converted_groups = []
        for group in member_groups:
            attr = AttributesManagerApi.get_attribute(group["id"])
            unique_name = attr["value"] + ":" + group["name"]
            converted_groups.append(
                Group(
                    group["id"],
                    group["vo_id"],
                    group["uuid"],
                    group["name"],
                    unique_name,
                    group["description"],
                )
            )

        return converted_groups

    def get_sp_groups(self, sp_entity_id: str) -> List[Group]:

        facility = self.get_facility_by_rp_identifier(sp_entity_id)
        if facility is None:
            return []

        perun_attrs = FacilitiesManagerApi.get_assigned_resources_for_facility(
            self, facility.id
        )

        resources = []
        for perun_attr in perun_attrs:
            resources.append(
                Resource(
                    perun_attr["id"],
                    perun_attr["vo_id"],
                    perun_attr["facility_id"],
                    perun_attr["name"],
                )
            )

        sp_groups = []
        for resource in resources:
            groups = ResourcesManagerApi.get_assigned_groups(self, resource.id)

            for group in groups:
                attr = AttributesManagerApi.get_attribute(group["id"])
                unique_name = attr["value"] + ":" + attr["name"]
                sp_groups.append(
                    Group(
                        group["id"],
                        group["vo_id"],
                        group["uuid"],
                        group["name"],
                        unique_name,
                        group["description"],
                    )
                )

        return self.remove_duplicate_entities(sp_groups)

    def get_group_by_name(self, vo: Vo, name: str) -> Group:
        group = GroupsManagerApi.get_group_by_name(self, vo, name)
        attr = AttributesManagerApi.get_attribute(group["id"])
        unique_name = attr["value"] + ":" + group["name"]
        return Group(
            group["id"],
            group["vo_id"],
            group["uuid"],
            group["name"],
            unique_name,
            group["description"],
        )

    def get_vo(self, short_name=None, id=None) -> Vo:
        if short_name and id:
            raise ValueError(
                "VO can be obtained either by its short_name or id, not both "
                "at the same time."
            )
        elif id:
            vo = VosManagerApi.get_vo_by_id(self, id)
        elif short_name:
            vo = VosManagerApi.get_vo_by_short_name(self, short_name)
        else:
            raise TypeError(
                "Neither short_name nor id was provided, please specify "
                "exactly one to find VO by."
            )

        return Vo(vo["id"], vo["name"], vo["short_name"])

    def get_facility_by_rp_identifier(
        self, rp_identifier: str, entity_id_attr="perunFacilityAttr_entityID"
    ) -> Facility:
        attr_name = AttributeUtils.get_rpc_attr_name(entity_id_attr)

        if not attr_name:
            attr_name = "urn:perun:facility:attribute-def:def:entityID"
            logging.warning(
                "No attribute configuration in RPC found for attribute "
                + entity_id_attr
                + ", using "
                + attr_name
                + " as fallback value"
            )

        perun_attr = FacilitiesManagerApi.get_facilities_by_attribute(
            self, attr_name, rp_identifier
        )

        if not perun_attr:
            logging.warning(
                "perun:AdapterRpc: No facility with entityID '"
                + rp_identifier
                + "' found."
            )
            return None

        if len(perun_attr) > 1:
            logging.warning(
                "perun:AdapterRpc: There is more than one facility with "
                "entityID '" + rp_identifier + "."
            )
            return None

        return Facility(
            perun_attr[0]["id"],
            perun_attr[0]["name"],
            perun_attr[0]["description"],
            rp_identifier,
        )

    # I think this method could be replaced by calling - list(set(entities))
    # if we provided HasIdAbstract class with __hash__() method
    def remove_duplicate_entities(
        self, entities: List[HasIdAbstract]
    ) -> List[HasIdAbstract]:
        # I'd at least consider renaming - removed - to something like
        # non_duplicate, this name is directly taken form the php
        # implementation
        removed = []
        ids = []

        for entity in entities:
            if entity.id not in ids:
                ids.append(entity.id)
                removed.append(entity)

        return removed
