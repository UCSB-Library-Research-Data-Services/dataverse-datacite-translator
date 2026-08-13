import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from .writer_util import write_attribute, write_full_element, write_full_element_with_attributes
from .names import parse_person_or_org
from .identifiers import EXTERNAL_IDENTIFIERS

ROR = EXTERNAL_IDENTIFIERS["ROR"]


def write_entity_elements(parent, element_name, contributor_type, name, affiliation, name_identifier, name_identifier_scheme):
    new_element = ET.SubElement(parent, element_name)

    if contributor_type:
        write_attribute(new_element, "contributorType", contributor_type)

    parsed_name = parse_person_or_org(name)

    name_type = "Personal" if parsed_name["is_person"] else "Organizational"
    write_full_element_with_attributes(
        new_element,
        f"{element_name}Name",
        {"nameType": name_type},
        parsed_name["full_name"],
    )

    if parsed_name["given_name"]:
        write_full_element(new_element, "givenName", parsed_name["given_name"])
    if parsed_name["family_name"]:
        write_full_element(new_element, "familyName", parsed_name["family_name"])

    if name_identifier:
        parsed_url = urlparse(name_identifier)
        if parsed_url.scheme and parsed_url.netloc:
            scheme_uri = f"{parsed_url.scheme}://{parsed_url.netloc}"
            write_full_element_with_attributes(
                new_element,
                "nameIdentifier",
                {"schemeURI": scheme_uri, "nameIdentifierScheme": name_identifier_scheme},
                name_identifier,
            )

    if affiliation:
        attribute_map = {}
        if ROR.is_valid_identifier(affiliation):
            attribute_map["schemeURI"] = "https://ror.org"
            attribute_map["affiliationIdentifierScheme"] = "ROR"
            attribute_map["affiliationIdentifier"] = affiliation
        write_full_element_with_attributes(new_element, "affiliation", attribute_map, affiliation)

    return new_element
