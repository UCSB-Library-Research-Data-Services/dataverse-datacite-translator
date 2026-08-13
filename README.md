## Summary

This is a metadata translation tool designed to translate JSON metadata into Datacite XML in the context of the Dataverse Project.

It reads a Dataverse dataset's native JSON API export and produces a DataCite kernel-4 XML document, mirroring the mapping logic Dataverse itself uses when exporting to DataCite.



## Installation

The `datacite` package itself has no external dependencies (standard library only). It can be installed directly from this repo without publishing anywhere:

```
pip install git+<this-repo-url>
```

or, for local development against another project on your machine:

```
pip install -e /path/to/python_translation_tool
```

Running `main.py` as a standalone CLI additionally requires `requests` and `python-dotenv`:

```
pip install requests python-dotenv
```

## Usage

### As a library

```python
import json
from datacite import generate_xml

with open("metadata.json") as f:
    metadata = json.load(f)

generate_xml(metadata, "output.xml")
```

`generate_xml(metadata: dict, output_file: str)` takes the parsed Dataverse JSON export and writes the resulting DataCite XML to `output_file`. It doesn't return the XML directly; read `output_file` back if you need the contents in memory. 

Every element writer fails independently, and logs a warning to the console if an error is encountered. An output xml file is always produced as a result.


### As a CLI

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

The specific external tool this was written for is a metadata validator utility:https://github.com/UCSB-Library-Research-Data-Services/metadata-checker 


## Credit and Attributions

This tool was written by [Joshua Gray](https://www.linkedin.com/in/joshuaegray/) for UCSB Library and Research Data Services. 

It is heavily based on the Dataverse source code (which is written in Java) in accordance with the Apache 2.0 license. Thus, the mapping logic mirrors the original java implementation, and in some cases exact code or files are copied into the python tool. The source code can be found at https://github.com/IQSS/dataverse

