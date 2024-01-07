#!/usr/bin/env python3

#--------------------------------------------------------------------------------
# Console client for AbletonOSC.
# Takes OSC commands and parameters, and prints the return value.
#--------------------------------------------------------------------------------

import re
import sys
import argparse
import json

try:
    import readline
except:
    if sys.platform == "win32":
        print("On Windows, run-command.py requires pyreadline3: pip install pyreadline3")
    else:
        raise

from client import AbletonOSCClient


def main(args):
    client = AbletonOSCClient(args.hostname, args.port)
    # client = AbletonOSCClient("127.0.0.1", 11000)
    client.send_message("/live/api/reload")

    # readline.parse_and_bind('tab: complete')
    # print("AbletonOSC command console")
    # print("Usage: /live/osc/command [params]")

    command_str = args.path

    command, *params_str = command_str.split(" ")
    params = []
    for part in params_str:
        try:
            part = int(part)
        except ValueError:
            try:
                part = float(part)
            except ValueError:
                pass
        params.append(part)
    try:        
        if args.json:
            print(json.dumps(client.query(command, params)))
        else:
            print(client.query(command, params))

    except RuntimeError as e:
        print(f"error: {e}")
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Console client for AbletonOSC. Takes OSC commands and parameters, and prints the return value.")
    parser.add_argument("--hostname", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=str, default=11000)
    parser.add_argument("--verbose", "-v", action="store_true", help="verbose mode: prints all OSC messages")
    parser.add_argument("--json", "-j", action="store_true", help="json output mode")
    parser.add_argument("path", type=str)
    args = parser.parse_args()
    main(args)
