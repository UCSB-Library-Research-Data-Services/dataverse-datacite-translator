"""Python port of PersonOrOrgUtil.java's getPersonOrOrganization().

The real Java algorithm leans on two external lookup tables we don't have
access to (Organizations.isOrganization() and FirstNames.getFirstName() -
both large, real dictionaries, not simple heuristics - see TODO.md #5), so
this is a comma/space-based approximation rather than a literal port:

- No comma, exactly one space -> treated as a person in "Given Family" order,
  split on the space. Quick-and-dirty stand-in for FirstNames.getFirstName()
  matching a leading given name and taking the rest as the family name
  (PersonOrOrgUtil.java lines 99-118) - see TODO.md #5 for the known
  false-positive this causes on space-separated org names.
- No comma, zero or 2+ spaces -> treated as an organization name, unsplit.
- Exactly one comma -> treated as a person, "Family, Given" order, split into
  given_name/family_name (mirrors PersonOrOrgUtil.java lines 88-93).
- More than one comma -> treated as a person, but left unsplit, matching
  Java's own behavior: it only splits when removing the first comma leaves no
  further commas (PersonOrOrgUtil.java's guard,
  `!name.replaceFirst(",", "").contains(",")`, lines 88 and 121).
"""


def parse_person_or_org(name: str) -> dict:
    name = name.strip()

    comma_count = name.count(",")

    if comma_count == 0:
        if name.count(" ") == 1:
            given_name, family_name = name.split(" ", 1)
            return {
                "full_name": name,
                "given_name": given_name,
                "family_name": family_name,
                "is_person": True,
            }

        return {
            "full_name": name,
            "given_name": None,
            "family_name": None,
            "is_person": False,
        }

    if comma_count == 1:
        family_name, given_name = name.split(", ", 1)
        return {
            "full_name": name,
            "given_name": given_name,
            "family_name": family_name,
            "is_person": True,
        }

    return {
        "full_name": name,
        "given_name": None,
        "family_name": None,
        "is_person": True,
    }
