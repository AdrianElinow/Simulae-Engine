import json, sys, os
from math import e
from pprint import pprint
from .ngin_console_log import log, logError, logWarning, logDebug, logInfo, logAll

def normalize_str(value: str | None) -> str:
    if not value:
        return ""
    
    norm = str(value).strip()

    return norm if norm else ""

def get_unique_strs(values: list[str] | None) -> list[str]:
    uniques = []

    if values:
        [uniques.append(s.strip()) for s in values if s not in uniques if s.strip()]
    
    return uniques    

def save_json_to_file( filename: str, data:dict, filepath : str | None =None, pretty: bool =False):
    if not filename:
        raise ValueError("filename cannot be null/empty")

    if not filepath:
        filepath = os.getcwd()

    absolute_path = f"{filepath}/{filename}"

    try:

        with open(absolute_path,'w') as open_file:

            json.dump( data, open_file, indent=( 4 if pretty else None ) )

    except TypeError as te:
        print(f"Error while writing to file | Unable to serialize data\n{te}")
    except Exception as e:
        print(f"Error while writing to file [{absolute_path}]\n{e}")


def load_json_from_file( filename: str, filepath : str | None = None ):
    logAll(f"load_json_from_file( filename: {filename}, filepath: {filepath} )")

    if not filename:
        raise ValueError("filename cannot be null/empty")

    if not filepath:
        filepath = os.getcwd()

    absolute_path = f"{filepath}/{filename}"

    if os.path.exists(absolute_path):

        try:

            with open(absolute_path,'r') as open_file:

                data = json.load( open_file )

                if data:
                    logAll(f"loaded [{absolute_path}]")

                    return data

        except json.JSONDecodeError as e:
            logError(f"Error while parsing file [{absolute_path}]\n{e}")

    else:
        logWarning(f"No file found at {absolute_path}")

    return None

