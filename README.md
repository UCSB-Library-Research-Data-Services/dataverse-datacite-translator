## Summary

This is a metadata translation tool designed to translate JSON metadata into Datacite XML in the context of the Dataverse Project.

It reads a Dataverse dataset's native JSON API export and produces a DataCite kernel-4 XML document, mirroring the mapping logic Dataverse itself uses when exporting to DataCite.



## Installation

There are two separate ways to use this tool - installing it as a library only installs the `datacite` package, **not** `main.py` (see below), so pick the path that matches how you intend to use it.

### As a library (in another project)

The `datacite` package itself has no external dependencies (standard library only). Install it directly from this repo without publishing anywhere:

```
pip install git+https://github.com/UCSB-Library-Research-Data-Services/dataverse-datacite-translator
```

or, for local development against another project on your machine:

```
pip install -e /path/to/python_translation_tool
```

Either way, this makes `from datacite import generate_xml` available - see "As a library" under Usage below. `main.py` is **not** part of what gets installed by either command; it's a CLI script that lives in this repo and is only usable if you have the repo itself checked out (next section).

### As a standalone CLI

Clone the Github repository and run `main.py`. The script requires `requests` and `python-dotenv`

## Usage

### As a library

Two functions are available, depending on whether you want a file written to disk:

```python
import json
from datacite import generate_xml, build_xml

with open("metadata.json") as f:
    metadata = json.load(f)

# Writes to a file and also returns the root element
root = generate_xml(metadata, "output.xml")

# Builds the XML in memory only - nothing is written to disk
root = build_xml(metadata)
```

`generate_xml(metadata: dict, output_file: str)` takes the parsed Dataverse JSON export, writes the resulting DataCite XML to `output_file`, and returns the root `xml.etree.ElementTree.Element` of the generated document. It's a thin wrapper around `build_xml` that also handles the file write.

`build_xml(metadata: dict)` does the same translation but only returns the root `xml.etree.ElementTree.Element` - use this if you want the XML in memory (e.g. to serialize it yourself, or hand it to something else) without writing a file at all.

Every element writer fails independently, and logs a warning to the console if an error is encountered. When using `generate_xml`, an output xml file is always produced as a result.


### As a CLI

(requires the repo to be cloned - see "As a standalone CLI" under Installation above)

```
python3 main.py -i metadata.json -o output.xml
```

Or look a dataset up directly from a running Dataverse instance by persistent ID:

```
python3 main.py -p doi:10.5072/FK2/ABCDEF -o output.xml
```

The `-p` lookup requires a `SERVER_URL` environment variable (e.g. in a `.env` file) pointing at the Dataverse instance's base URL.

| Flag | Description |
| --- | --- |
| `-i`, `--input` | Path to a Dataverse JSON metadata export file |
| `-o`, `--output` | Path to write the resulting XML to (default: `out.xml`) |
| `-p`, `--pid` | Persistent ID of a dataset to look up via the Dataverse API, instead of `-i` |

`-i` and `-p` are mutually exclusive; exactly one is required.

## Motivation

The motivation for the tool is to provide a means of obtaining XML Metadata from any given Dataset through a signed URL for externals tools in Dataverse. The Dataverse does in fact have APIs to export XML Metadata, but these are not compatible with signed URLs as they require API tokens.

The specific external tool this was written for is a metadata validator utility: https://github.com/UCSB-Library-Research-Data-Services/metadata-checker 


## Credit and Attributions

This tool was written by [Joshua Gray](https://www.linkedin.com/in/joshuaegray/) for UCSB Library and Research Data Services. 

It is heavily based on the Dataverse source code (which is written in Java) in accordance with the Apache 2.0 license. Thus, the mapping logic mirrors the original java implementation, and in some cases exact code or files are copied into the python tool. The source code can be found at https://github.com/IQSS/dataverse

## Disclaimer

This code is provided "as is," with no warranties or guarantees of any kind. It was developed primarily for internal use; neither UCSB nor Joshua Gray is responsible for any damages resulting from its use.
