import sys
import xml.etree.ElementTree as ET

from .writer_util import write_attribute, write_full_element, write_full_element_with_attributes
from .fields import compound_rows, child_value, singular_value, list_values
from .identifiers import resolve_name_identifier, normalize_pid, split_url_identifier
from .writers import write_entity_elements
from .date import get_publisher_year
from .constants import (
    UNAVAILABLE,
    CONTRIBUTOR_TYPES,
    RESOURCE_TYPE_MAP,
    RELATED_IDENTIFIER_TYPE_MAP,
    LICENSE_SHORT_DESCRIPTIONS,
    XML_NAMESPACE,
    XML_SCHEMA_LOCATION,
    XML_XSI,
)


def safe_write(write_func, *args):
    # Optional DataCite elements shouldn't be able to take down the whole
    # export - log and skip that one element instead of erroring out.
    try:
        return write_func(*args)
    except Exception as exc:
        print(f"Warning: {write_func.__name__} failed, skipping: {exc}", file=sys.stderr)
        return None


def generate_xml(metadata, output_file):
    root = build_xml(metadata)
    write_file(root, output_file)
    return root





def build_xml(metadata) -> ET.Element:
    deaccessioned = False

    version_state = metadata.get("data", {}).get("latestVersion", {}).get("versionState", None)

    if not version_state:
        print("Warning: Cannot find the version_state, treating as not deaccessioned", file=sys.stderr)

    #Note: not sure if this is relevant for us since the API point won't work if the dataset is deaccesioned
    if version_state == "DEACCESSIONED":
        deaccessioned = True

    ET.register_namespace("", XML_NAMESPACE)
    ET.register_namespace("xsi", XML_XSI)
    root = ET.Element(f"{{{XML_NAMESPACE}}}resource")

    root.set(f"{{{XML_XSI}}}schemaLocation", XML_SCHEMA_LOCATION)

    safe_write(write_identifier, root, metadata)

    citation_fields = metadata.get("data", {}).get("latestVersion", {}).get("metadataBlocks", {}).get("citation", {}).get("fields", None)


    safe_write(write_creators, root, citation_fields, deaccessioned)
    safe_write(write_titles, root, metadata, citation_fields, deaccessioned)
    safe_write(write_publisher, root, metadata, deaccessioned)
    safe_write(write_publication_year, root, metadata, deaccessioned)

    if not deaccessioned:
        safe_write(write_subjects, root, citation_fields)
        safe_write(write_contributors, root, citation_fields)
        safe_write(write_dates, root, metadata, citation_fields)

    safe_write(write_resource_type, root, metadata, citation_fields)

    if not deaccessioned:
        safe_write(write_alternate_identifiers, root, citation_fields)
        safe_write(write_related_identifiers, root, citation_fields)
        safe_write(write_sizes, root, metadata)
        safe_write(write_formats, root, metadata)
        safe_write(write_version, root, metadata)
        safe_write(write_access_rights, root, metadata)

    safe_write(write_descriptions, root, citation_fields, deaccessioned)

    if not deaccessioned:
        safe_write(write_geolocations, root, metadata)
        safe_write(write_funding_references, root, citation_fields)

    return root




def write_identifier(parent, metadata):
    data = metadata.get('data', {})
    protocol = data.get('protocol')
    authority = data.get('authority')
    identifier = data.get('identifier')
    separator = data.get('separator', '/')

    if protocol == 'doi':
        identifier_type = 'DOI'
        value = f"{authority}{separator}{identifier}"
    elif protocol == 'hdl':
        identifier_type = 'Handle'
        value = f"{authority}{separator}{identifier}"
    elif protocol == 'perma':
        identifier_type = 'URL'
        value = data.get('persistentUrl')
    else:
        raise ValueError(f"Unrecognized PID protocol: {protocol!r}")

    if not value:
        raise ValueError("Error finding identifier")

    return write_full_element_with_attributes(parent, "identifier", {"identifierType": identifier_type}, value)

def write_creators(parent, citation_fields, deaccessioned):
    creators_element = ET.SubElement(parent, "creators")

    author_rows = [] if deaccessioned else compound_rows(citation_fields, "author")

    wrote_creator = False
    for row in author_rows:
        creator_name = child_value(row, "authorName")
        if not creator_name:
            continue

        affiliation = child_value(row, "authorAffiliation")
        id_value = child_value(row, "authorIdentifier")
        id_scheme = child_value(row, "authorIdentifierScheme")

        name_identifier = None
        if id_value and id_scheme:
            name_identifier = resolve_name_identifier(id_scheme, id_value)
        else:
            id_scheme = None

        write_entity_elements(creators_element, "creator", None, creator_name, affiliation, name_identifier, id_scheme)
        wrote_creator = True

    if not wrote_creator:
        fallback_creator = ET.SubElement(creators_element, "creator")
        write_full_element(fallback_creator, "creatorName", UNAVAILABLE)

    return creators_element

def write_file(root, filename):
    tree = ET.ElementTree(root)
    ET.indent(tree, space = " ")
    tree.write(filename,
            encoding="utf-8",
            xml_declaration=True
            )


def write_titles(parent, metadata, citation_fields, deaccessioned):
    title = None
    sub_title = None
    alt_titles = []

    if not deaccessioned:
        title = singular_value(citation_fields, "title")

        if metadata.get("data",{}).get("datasetType", "") == "dataset":
            sub_title = singular_value(citation_fields, "subtitle")

            alt_titles = list_values(citation_fields, "alternativeTitle")
    else:
        title = UNAVAILABLE


    if title or sub_title or alt_titles:
        new_element = ET.SubElement(parent, "titles")

        if title:
            write_full_element(new_element, "title", title)


        if sub_title:
            attributes = {}
            attributes["titleType"] = "Subtitle"
            write_full_element_with_attributes(new_element, "title", attributes, sub_title)

        if alt_titles:
            attributes = {}
            attributes["titleType"] = "AlternativeTitle"

            for alt_title in alt_titles:
                write_full_element_with_attributes(new_element, "title", attributes, alt_title)

def write_publisher(parent, metadata, deaccessioned):
    if deaccessioned:
        publisher = UNAVAILABLE

    else:
        publisher = metadata.get("data", {}).get("publisher", UNAVAILABLE)

    write_full_element(parent, "publisher", publisher)

def write_publication_year(parent, metadata, deaccessioned):

    pub_year = "9999"

    if not deaccessioned and get_publisher_year(metadata):
        pub_year = get_publisher_year(metadata)

    write_full_element(parent, "publicationYear", pub_year)

def write_subjects(parent, citation_fields):
    subject_entries = []

    for subject in list_values(citation_fields, "subject"):
        if subject:
            subject_entries.append(({}, subject))

    for row in compound_rows(citation_fields, "keyword"):
        keyword = child_value(row, "keywordValue")
        if not keyword:
            continue

        attributes = {}
        scheme = child_value(row, "keywordVocabulary")
        scheme_uri = child_value(row, "keywordVocabularyURI")
        if scheme_uri:
            attributes["schemeURI"] = scheme_uri
        if scheme:
            attributes["subjectScheme"] = scheme

        subject_entries.append((attributes, keyword))

    for row in compound_rows(citation_fields, "topicClassification"):
        topic = child_value(row, "topicClassValue")
        if not topic:
            continue

        attributes = {}
        scheme = child_value(row, "topicClassVocab")
        scheme_uri = child_value(row, "topicClassVocabURI")
        if scheme_uri:
            attributes["schemeURI"] = scheme_uri
        if scheme:
            attributes["subjectScheme"] = scheme

        subject_entries.append((attributes, topic))

    if not subject_entries:
        return None

    subjects_element = ET.SubElement(parent, "subjects")
    for attributes, text in subject_entries:
        write_full_element_with_attributes(subjects_element, "subject", attributes, text)

    return subjects_element

def write_contributors(parent, citation_fields):
    entries = []  # (contributor_type, name, affiliation)

    for row in compound_rows(citation_fields, "producer"):
        name = child_value(row, "producerName")
        if name:
            entries.append(("Producer", name, child_value(row, "producerAffiliation")))

    for row in compound_rows(citation_fields, "distributor"):
        name = child_value(row, "distributorName")
        if name:
            entries.append(("Distributor", name, child_value(row, "distributorAffiliation")))

    for row in compound_rows(citation_fields, "datasetContact"):
        name = child_value(row, "datasetContactName")
        if name:
            entries.append(("ContactPerson", name, child_value(row, "datasetContactAffiliation")))

    for row in compound_rows(citation_fields, "contributor"):
        name = child_value(row, "contributorName")
        if not name:
            continue

        raw_type = child_value(row, "contributorType")
        contributor_type = raw_type.replace(" ", "") if raw_type else raw_type

        if contributor_type and contributor_type.lower() == "funder":
            continue

        if not contributor_type or contributor_type not in CONTRIBUTOR_TYPES:
            contributor_type = "Other"

        entries.append((contributor_type, name, None))

    if not entries:
        return None

    contributors_element = ET.SubElement(parent, "contributors")
    for contributor_type, name, affiliation in entries:
        write_entity_elements(contributors_element, "contributor", contributor_type, name, affiliation, None, None)

    return contributors_element

def write_dates(parent, metadata, citation_fields):
    latest_version = metadata.get("data", {}).get("latestVersion", {})

    date_entries = []  # (date_type, value, extra_attributes)

    date_of_distribution = singular_value(citation_fields, "distributionDate")
    if date_of_distribution:
        date_entries.append(("Issued", date_of_distribution, {}))

    date_of_production = singular_value(citation_fields, "productionDate")
    if date_of_production:
        date_entries.append(("Created", date_of_production, {}))

    date_of_deposit = singular_value(citation_fields, "dateOfDeposit")
    if date_of_deposit:
        date_entries.append(("Submitted", date_of_deposit, {}))

    publication_date = metadata.get("data", {}).get("publicationDate")
    if publication_date:
        date_entries.append(("Available", publication_date, {}))

    version_number = latest_version.get("versionNumber")
    version_minor_number = latest_version.get("versionMinorNumber")
    is_an_update = version_number is not None and not (version_number == 1 and version_minor_number == 0)
    if is_an_update:
        release_time = latest_version.get("releaseTime")
        if release_time:
            date_entries.append(("Updated", release_time.split("T")[0], {}))

    for row in compound_rows(citation_fields, "dateOfCollection"):
        start = child_value(row, "dateOfCollectionStart") or ""
        end = child_value(row, "dateOfCollectionEnd") or ""
        if start or end:
            date_entries.append(("Collected", f"{start}/{end}".strip(), {}))

    for row in compound_rows(citation_fields, "timePeriodCovered"):
        start = child_value(row, "timePeriodCoveredStart") or ""
        end = child_value(row, "timePeriodCoveredEnd") or ""
        if start or end:
            date_entries.append(("Other", f"{start}/{end}".strip(), {"dateInformation": "Time period covered by the data"}))

    if not date_entries:
        return None

    dates_element = ET.SubElement(parent, "dates")
    for date_type, value, extra_attributes in date_entries:
        attributes = {"dateType": date_type}
        attributes.update(extra_attributes)
        write_full_element_with_attributes(dates_element, "date", attributes, value)

    return dates_element

def write_resource_type(parent, metadata, citation_fields):
    dataset_type_name = metadata.get("data", {}).get("datasetType")
    resource_type = RESOURCE_TYPE_MAP.get(dataset_type_name, "Dataset")

    attributes = {"resourceTypeGeneral": resource_type}

    kind_of_data_values = [value for value in list_values(citation_fields, "kindOfData") if value]

    if kind_of_data_values:
        return write_full_element_with_attributes(parent, "resourceType", attributes, ";".join(kind_of_data_values))

    new_element = ET.SubElement(parent, "resourceType")
    write_attribute(new_element, "resourceTypeGeneral", resource_type)
    return new_element

def write_related_identifiers(parent, citation_fields):
    entries = []  # (attributes, text)

    for row in compound_rows(citation_fields, "publication"):
        relation_type = child_value(row, "publicationRelationType") or "IsSupplementTo"

        raw_pub_id_type = child_value(row, "publicationIDType") or ""
        pub_id_type = RELATED_IDENTIFIER_TYPE_MAP.get(raw_pub_id_type.lower())

        related_identifier = child_value(row, "publicationIDNumber") or child_value(row, "publicationURL")

        attributes = {}
        if related_identifier:
            if pub_id_type == "DOI":
                related_identifier = normalize_pid("doi", related_identifier)
            elif pub_id_type == "Handle":
                related_identifier = normalize_pid("hdl", related_identifier)
            elif pub_id_type == "URL":
                related_identifier, scheme_uri = split_url_identifier(related_identifier)
                if scheme_uri:
                    attributes["schemeURI"] = scheme_uri
            elif pub_id_type is None:
                doi_form = normalize_pid("doi", related_identifier, allow_bare=False)
                hdl_form = normalize_pid("hdl", related_identifier, allow_bare=False)

                if doi_form:
                    related_identifier, pub_id_type = doi_form, "DOI"
                elif hdl_form:
                    related_identifier, pub_id_type = hdl_form, "Handle"

                body, scheme_uri = split_url_identifier(related_identifier) if related_identifier else (None, None)
                if scheme_uri:
                    related_identifier, pub_id_type = body, "URL"
                    attributes["schemeURI"] = scheme_uri

        if related_identifier and pub_id_type:
            attributes["relationType"] = relation_type
            attributes["relatedIdentifierType"] = pub_id_type
            entries.append((attributes, related_identifier))

    if not entries:
        return None

    related_identifiers_element = ET.SubElement(parent, "relatedIdentifiers")
    for attributes, text in entries:
        write_full_element_with_attributes(related_identifiers_element, "relatedIdentifier", attributes, text)

    return related_identifiers_element

def write_sizes(parent, metadata):
    files = metadata.get("data", {}).get("latestVersion", {}).get("files", [])

    sizes = []
    for file_entry in files:
        filesize = file_entry.get("dataFile", {}).get("filesize")
        if filesize is None or filesize == -1:
            continue
        sizes.append(str(filesize))

    if not sizes:
        return None

    sizes_element = ET.SubElement(parent, "sizes")
    for size in sizes:
        write_full_element(sizes_element, "size", size)

    return sizes_element

def write_formats(parent, metadata):
    files = metadata.get("data", {}).get("latestVersion", {}).get("files", [])

    formats = []
    for file_entry in files:
        content_type = file_entry.get("dataFile", {}).get("contentType")
        if content_type:
            formats.append(content_type)

    if not formats:
        return None

    formats_element = ET.SubElement(parent, "formats")
    for content_type in formats:
        write_full_element(formats_element, "format", content_type)

    return formats_element

def write_version(parent, metadata):
    latest_version = metadata.get("data", {}).get("latestVersion", {})

    if latest_version.get("versionState") == "DRAFT":
        version = "DRAFT"
    else:
        version_number = latest_version.get("versionNumber")
        version_minor_number = latest_version.get("versionMinorNumber")
        if version_number is None or version_minor_number is None:
            return None
        version = f"{version_number}.{version_minor_number}"

    return write_full_element(parent, "version", version)

def write_access_rights(parent, metadata):
    latest_version = metadata.get("data", {}).get("latestVersion", {})
    files = latest_version.get("files", [])

    requests_allowed = latest_version.get("fileAccessRequest", False)
    closed = any(file_entry.get("restricted") for file_entry in files)

    if requests_allowed and closed:
        access_uri = "info:eu-repo/semantics/restrictedAccess"
    elif not requests_allowed and closed:
        access_uri = "info:eu-repo/semantics/closedAccess"
    else:
        access_uri = "info:eu-repo/semantics/openAccess"

    rights_list_element = ET.SubElement(parent, "rightsList")

    license = latest_version.get("license")
    if license:
        uri = license.get("uri")

        attributes = {"rightsURI": uri}

        rights_identifier = license.get("rightsIdentifier")
        if rights_identifier:
            attributes["rightsIdentifier"] = rights_identifier

        rights_identifier_scheme = license.get("rightsIdentifierScheme")
        if rights_identifier_scheme:
            attributes["rightsIdentifierScheme"] = rights_identifier_scheme

        scheme_uri = license.get("schemeUri")
        if scheme_uri:
            attributes["schemeURI"] = scheme_uri

        attributes["xml:lang"] = license.get("languageCode") or "en"

        description = LICENSE_SHORT_DESCRIPTIONS.get(uri) or license.get("name")

        write_full_element_with_attributes(rights_list_element, "rights", attributes, description)

    access_rights_element = ET.SubElement(rights_list_element, "rights")
    write_attribute(access_rights_element, "rightsURI", access_uri)

    return rights_list_element

def write_descriptions(parent, citation_fields, deaccessioned):
    entries = []  # (attributes, text)

    if deaccessioned:
        entries.append(({"descriptionType": "Abstract"}, UNAVAILABLE))
    else:
        for row in compound_rows(citation_fields, "dsDescription"):
            description = child_value(row, "dsDescriptionValue")
            if description:
                entries.append(({"descriptionType": "Abstract"}, description))

        for row in compound_rows(citation_fields, "software"):
            software_name = child_value(row, "softwareName")
            if software_name:
                software_version = child_value(row, "softwareVersion")
                if software_version:
                    software_name = f"{software_name}, {software_version}"
                entries.append(({"descriptionType": "TechnicalInfo"}, software_name))

        for row in compound_rows(citation_fields, "series"):
            series_name = child_value(row, "seriesName")
            if series_name:
                entries.append(({"descriptionType": "SeriesInformation"}, series_name))

        for type_name in ("originOfSources", "characteristicOfSources", "accessToSources"):
            method = singular_value(citation_fields, type_name)
            if method:
                entries.append(({"descriptionType": "Methods"}, method))

        notes_text = singular_value(citation_fields, "notesText")
        if notes_text:
            entries.append(({"descriptionType": "Other"}, notes_text))

    if not entries:
        return None

    descriptions_element = ET.SubElement(parent, "descriptions")
    for attributes, text in entries:
        write_full_element_with_attributes(descriptions_element, "description", attributes, text)

    return descriptions_element

def format_geo_location_place(country, state, city, other):
    # Empirically reverse-engineered from real confirmed DataCite export
    # output - see TODO.md for why this doesn't match writeGeoLocations'
    # actual code in our java/ reference files. country/state always
    # contribute their own slot (blank or not); city/other each contribute
    # an extra blank spacer slot immediately before their own slot, but only
    # when actually present.
    parts = [country or "", f" {state}" if state else ""]

    if city:
        parts.append("")
        parts.append(f" {city}")

    if other:
        parts.append("")
        parts.append(f" {other}")

    return ",".join(parts) + ","

def write_geolocations(parent, metadata):
    geospatial_fields = metadata.get("data", {}).get("latestVersion", {}).get("metadataBlocks", {}).get("geospatial", {}).get("fields", None)

    entries = []  # (kind, data)

    for row in compound_rows(geospatial_fields, "geographicCoverage"):
        country = child_value(row, "country")
        state = child_value(row, "state")
        city = child_value(row, "city")
        other = child_value(row, "otherGeographicCoverage")
        if country or state or city or other:
            entries.append(("place", format_geo_location_place(country, state, city, other)))

    for row in compound_rows(geospatial_fields, "geographicBoundingBox"):
        west = child_value(row, "westLongitude")
        east = child_value(row, "eastLongitude")
        north = child_value(row, "northLatitude")
        south = child_value(row, "southLatitude")

        if west and east and north and south:
            if west == east and north == south:
                entries.append(("point", (east, south)))
            else:
                entries.append(("box", (west, east, south, north)))

    if not entries:
        return None

    geolocations_element = ET.SubElement(parent, "geoLocations")
    for kind, data in entries:
        geolocation_element = ET.SubElement(geolocations_element, "geoLocation")
        if kind == "place":
            write_full_element(geolocation_element, "geoLocationPlace", data)
        elif kind == "point":
            longitude, latitude = data
            point_element = ET.SubElement(geolocation_element, "geoLocationPoint")
            write_full_element(point_element, "pointLongitude", longitude)
            write_full_element(point_element, "pointLatitude", latitude)
        elif kind == "box":
            west, east, south, north = data
            box_element = ET.SubElement(geolocation_element, "geoLocationBox")
            write_full_element(box_element, "westBoundLongitude", west)
            write_full_element(box_element, "eastBoundLongitude", east)
            write_full_element(box_element, "southBoundLatitude", south)
            write_full_element(box_element, "northBoundLatitude", north)

    return geolocations_element

def write_funding_references(parent, citation_fields):
    entries = []  # (funder_name, award_number)

    for row in compound_rows(citation_fields, "contributor"):
        contributor_type = child_value(row, "contributorType")
        if contributor_type == "Funder":
            funder_name = child_value(row, "contributorName")
            if funder_name:
                entries.append((funder_name, None))

    for row in compound_rows(citation_fields, "grantNumber"):
        funder_name = child_value(row, "grantNumberAgency")
        if funder_name:
            award_number = child_value(row, "grantNumberValue")
            entries.append((funder_name, award_number))

    if not entries:
        return None

    funding_references_element = ET.SubElement(parent, "fundingReferences")
    for funder_name, award_number in entries:
        funding_reference_element = ET.SubElement(funding_references_element, "fundingReference")
        write_full_element(funding_reference_element, "funderName", funder_name)
        if award_number:
            write_full_element(funding_reference_element, "awardNumber", award_number)

    return funding_references_element

def write_alternate_identifiers(parent, citation_fields):
    entries = []  # (attributes, text)

    for row in compound_rows(citation_fields, "otherId"):
        identifier = child_value(row, "otherIdValue")
        if not identifier:
            continue

        identifier_type = child_value(row, "otherIdAgency") or UNAVAILABLE
        entries.append(({"alternateIdentifierType": identifier_type}, identifier))

    if not entries:
        return None

    alternate_identifiers_element = ET.SubElement(parent, "alternateIdentifiers")
    for attributes, text in entries:
        write_full_element_with_attributes(alternate_identifiers_element, "alternateIdentifier", attributes, text)

    return alternate_identifiers_element
