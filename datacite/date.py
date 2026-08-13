from datetime import datetime
def get_publisher_year(metadata):
    publisher_year = metadata.get("data", {}).get("publicationDate", None)
    create_year = metadata.get("data", {}).get("latestVersion", {}).get("createTime", None)

    if publisher_year:
        pub_year = publisher_year
        pub_year = pub_year.partition("-")[0]
    elif create_year:
        pub_year = create_year
        pub_year = pub_year.partition("-")[0]
    else:
        pub_year = datetime.now().strftime("%Y")

    return pub_year


