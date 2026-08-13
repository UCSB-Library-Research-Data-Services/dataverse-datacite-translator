import re
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class ExternalIdentifier:
    """Mirrors one enum constant of ExternalIdentifier.java: a name/affiliation
    identifier scheme's URL template plus its validation regex."""

    url_template: str
    pattern: str

    def is_valid_identifier(self, value: str) -> bool:
        # ExternalIdentifier.java's isValidIdentifier(userInput): matches the
        # whole value against the compiled pattern.
        if value is None:
            return False
        return re.match(self.pattern, value) is not None

    def build_url(self, value: str) -> str:
        # ExternalIdentifier.java's format(idValue): don't double-prefix a
        # value that's already given in full-URL form.
        prefix = self.url_template.split("{}")[0]
        if value.startswith(prefix):
            return value
        return self.url_template.format(value)


EXTERNAL_IDENTIFIERS = {
    "ORCID": ExternalIdentifier(
        "https://orcid.org/{}",
        r"^(https://orcid\.org/)?\d{4}-\d{4}-\d{4}-(\d{4}|\d{3}X)$",
    ),
    "ISNI": ExternalIdentifier(
        "http://www.isni.org/isni/{}",
        r"^(http://www\.isni\.org/isni/)?(\d{16}|\d{15}X)$",
    ),
    "LCNA": ExternalIdentifier(
        "http://id.loc.gov/authorities/names/{}",
        r"^(http://id\.loc\.gov/authorities/names/)?[a-z]+\d+$",
    ),
    "VIAF": ExternalIdentifier(
        "https://viaf.org/viaf/{}",
        r"^(https://viaf\.org/viaf/)?\d*$",
    ),
    "GND": ExternalIdentifier(
        "https://d-nb.info/gnd/{}",
        r"^(https://d-nb\.info/gnd/)?(1[01]?\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X])$",
    ),
    "ResearcherID": ExternalIdentifier(
        "https://publons.com/researcher/{}/",
        r"^([A-Z\d][A-Z\d-]+[A-Z\d]|(https://publons\.com/researcher/)?[A-Z\d][A-Z\d-]+[A-Z\d]/)$",
    ),
    "ScopusID": ExternalIdentifier(
        "https://www.scopus.com/authid/detail.uri?authorId={}",
        r"^(https://www\.scopus\.com/authid/detail\.uri\?authorId=)?\d*$",
    ),
    "ROR": ExternalIdentifier(
        "https://ror.org/{}",
        r"^(https://ror\.org/)?0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$",
    ),
    "DAI": ExternalIdentifier(
        "info:eu-repo/dai/nl/{}",
        r"^(info:eu-repo/dai/nl/)?[\d]?\d{8}[0-9X]$",
    ),
}


def resolve_name_identifier(scheme: str, value: str) -> str | None:
    # Mirrors DatasetAuthor.getIdentifierAsUrl(idType, idValue): look up the
    # scheme, validate the raw value against it, then build the full URL -
    # but only return it if it's actually a resolvable http(s) URL (this is
    # what excludes DAI, whose "URL" is an info: URI, not a link).
    if not scheme or not value:
        return None

    external_identifier = EXTERNAL_IDENTIFIERS.get(scheme)
    if external_identifier is None:
        return None

    if not external_identifier.is_valid_identifier(value):
        return None

    url = external_identifier.build_url(value)
    if url.startswith("http"):
        return url

    return None


# writeRelatedIdentifiers's DOI/Handle normalization, ported from the real
# parsing algorithm - not a guess - confirmed by reading
# AbstractPidProvider.parsePersistentId (protocol:authority/identifier split)
# plus HandlePidProvider's and (commented-out but constant-confirmed)
# AbstractDoiProvider's resolver-URL-to-prefix overrides.
DOI_RESOLVER_PREFIXES = [
    "https://doi.org/", "http://doi.org/",
    "https://dx.doi.org/", "http://dx.doi.org/",
]
HANDLE_RESOLVER_PREFIXES = ["https://hdl.handle.net/", "http://hdl.handle.net/"]


def normalize_pid(protocol: str, identifier: str, allow_bare: bool = True) -> str | None:
    """Mirrors AbstractPidProvider.parsePersistentId + GlobalId.asRawIdentifier
    for the DOI ("doi") / Handle ("hdl") cases: swap a known resolver-URL
    prefix for "{protocol}:" (or, if allow_bare, add the bare "{protocol}:"
    prefix when neither it nor any "http" prefix is present), then split
    what follows the protocol on the first "/" into authority/identifier and
    rejoin as the raw "{authority}/{identifier}" form.

    allow_bare=False mirrors the "none"/auto-detect switch case in
    writeRelatedIdentifiers, which never blindly prepends a protocol prefix -
    it only succeeds if the value already unambiguously looks like this
    protocol's PID (explicit prefix or a recognized resolver URL).

    Returns None if the value doesn't parse as this protocol's PID.
    """
    if not identifier:
        return None

    if protocol == "doi":
        resolver_prefixes = DOI_RESOLVER_PREFIXES
    elif protocol == "hdl":
        resolver_prefixes = HANDLE_RESOLVER_PREFIXES
    else:
        return None

    prefix = f"{protocol}:"

    for resolver_prefix in resolver_prefixes:
        if identifier.startswith(resolver_prefix):
            identifier = prefix + identifier[len(resolver_prefix):]
            break
    else:
        if identifier.startswith(prefix):
            pass
        elif identifier.startswith("http"):
            return None
        elif allow_bare:
            identifier = prefix + identifier
        else:
            return None

    rest = identifier[len(prefix):]
    authority, separator, id_part = rest.partition("/")
    if not separator or not authority or not id_part:
        return None

    return f"{authority}/{id_part}"


def split_url_identifier(value: str) -> tuple[str | None, str | None]:
    """Mirrors writeRelatedIdentifiers's "URL" case: split a URL into its
    "{scheme}://{authority}" site (returned as schemeURI) and the remaining
    path (returned as the element body). Returns (None, None) if value isn't
    a parseable absolute URL.
    """
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        return None, None

    site = f"{parts.scheme}://{parts.netloc}"
    return value[len(site):], site
