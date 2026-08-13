import json
import sys
import argparse
import os

import requests
from dotenv import load_dotenv

from datacite import generate_xml


parser = argparse.ArgumentParser(description="Metadata translation tool")

parser.add_argument("-i", "--input", type=str, help="Input JSON file")
parser.add_argument("-o", "--output", type=str, default="out.xml", help="Name of XML file to output")
parser.add_argument("-p", "--pid", type=str, help="Pid of dataset to look up")


if __name__ == '__main__':
    args = parser.parse_args()

    load_dotenv()

    server_url = os.getenv("SERVER_URL")

    if not args.input and not args.pid:
        print("Error; requires either input or pid")
        sys.exit()

    if args.input and args.pid:
        print("Error; Enter either input or pid, not both")
        sys.exit()

    if args.input:
        with open(args.input, "r") as f:
            generate_xml(json.load(f), args.output)
    else:
        res = requests.get(f"{server_url}/api/v1/datasets/:persistentId/", params={"persistentId":args.pid})
        print(res.json())
        generate_xml(res.json(), args.output)
