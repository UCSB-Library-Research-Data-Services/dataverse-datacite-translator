"""Constants ported from XmlMetadataTemplate.java, DatasetFieldConstant.java, and
ExternalIdentifier.java.
"""

import json
from pathlib import Path

XML_NAMESPACE = "http://datacite.org/schema/kernel-4"
XML_SCHEMA_LOCATION = "http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4.5/metadata.xsd"
XML_XSI = "http://www.w3.org/2001/XMLSchema-instance"

# AbstractPidProvider.UNAVAILABLE - placeholder used for deaccessioned datasets.
UNAVAILABLE = ":unav"

# writeResourceType's switch on Dataset.getDatasetType().getName() (see
# DatasetType.java's DATASET_TYPE_* constants). Unlisted/unknown types default
# to "Dataset". "review" deliberately omitted - see TODO.md #6 - so it falls
# through to the "Dataset" default rather than the unverified "Other"/"Review"
# special-case the Java source has.
RESOURCE_TYPE_MAP = {
    "dataset": "Dataset",
    "software": "Software",
    "workflow": "Workflow",
}

def _load_license_short_descriptions():
    # writeAccessRights's license.getShortDescription(), keyed by license URI
    # (the field License.java enforces unique via @Column(nullable = false,
    # unique = true) - safer key than rightsIdentifier, which isn't
    # required). Java reads this from the License database table, populated
    # at instance setup from Dataverse's default license seed JSON files -
    # we don't have a database, so we read those same seed files directly
    # (datacite/licenses/license*.json, bundled as package data) rather than
    # hand-copying their values into a second, driftable copy here. Only
    # covers Dataverse's built-in default licenses; a custom/instance-added
    # license not among these files falls back to license.name (see
    # write_access_rights).
    licenses_dir = Path(__file__).resolve().parent / "licenses"
    descriptions = {}

    for license_file in sorted(licenses_dir.glob("license*.json")):
        with open(license_file, "r") as f:
            license_data = json.load(f)

        uri = license_data.get("uri")
        short_description = license_data.get("shortDescription")
        if uri and short_description:
            descriptions[uri] = short_description

    return descriptions


LICENSE_SHORT_DESCRIPTIONS = _load_license_short_descriptions()

# DataCite kernel-4 datacite-contributorType-v4.xsd enum values.
CONTRIBUTOR_TYPES = {
    "ContactPerson", "DataCollector", "DataCurator", "DataManager", "Distributor",
    "Editor", "HostingInstitution", "Other", "Producer", "ProjectLeader",
    "ProjectManager", "ProjectMember", "RegistrationAgency", "RegistrationAuthority",
    "RelatedPerson", "ResearchGroup", "RightsHolder", "Researcher", "Sponsor",
    "Supervisor", "WorkPackageLeader",
}

# relatedIdentifierTypeMap: canonicalizes a publication/PID type string. Java's
# version doesn't lowercase the lookup key, which looks like a bug (see plan) -
# here both keys and lookups are lowercased so e.g. "DOI"/"doi" both resolve.
RELATED_IDENTIFIER_TYPE_MAP = {
    "ark": "ARK", "arxiv": "arXiv", "bibcode": "bibcode", "doi": "DOI",
    "ean13": "EAN13", "eissn": "EISSN", "handle": "Handle", "hdl": "Handle",
    "igsn": "IGSN", "isbn": "ISBN", "issn": "ISSN", "istc": "ISTC",
    "lissn": "LISSN", "lsid": "LSID", "perma": "URL", "pissn": "PISSN",
    "pmid": "PMID", "purl": "PURL", "upc": "UPC", "url": "URL", "urn": "URN",
    "wos": "WOS",
}

# ExternalIdentifier.java enum: scheme name -> ExternalIdentifier(url_template,
# regex). Moved to identifiers.py, which owns the ExternalIdentifier class.
