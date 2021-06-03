#!/usr/bin/env python3

import os
import re
import glob

COMMENT_LINE = re.compile(r"^\s*#")

# Define the regexes to substitute Shotgun to something else for each file type.
regexes = {
    "py": re.compile(r"(\".*)Shotgun(.*\")"),
    "ui": re.compile(r"(<string>.*)Shotgun(.*</string>)"),
    "yml": re.compile(r"(.*)Shotgun(.*)"),
    "yaml": re.compile(r"(.*)Shotgun(.*)"),
    "md": re.compile(r"(.*)Shotgun(.*)"),
}

# Substitution function for the regexes above. It takes the text on both side
# of the word "Shotgun" and updates it to "ShotGrid"
def to_shotgrid(match):
    return match[1] + "ShotGrid" + match[2]


def scan_files_for_re(extension, regex, substitutor):
    # For every file with the given extension
    for filename in glob.iglob(
        "{}/**/*.{}".format(os.getcwd(), extension), recursive=True
    ):
        # Skip resource files, which are giant binary strings. There's nothing to do there and
        # it slows down everything.
        if "resources_rc" in filename:
            continue
        # Skip this file
        if os.path.abspath(filename) == os.path.abspath(__file__):
            continue
        result = []
        # Go over each line
        for line in open(filename, "rt"):
            # If the line is a comment, skip it.
            if not COMMENT_LINE.match(line):
                previous_line = None
                # While we can substitute Shotgun, keep going.
                while previous_line != line:
                    previous_line = line
                    line = regex.sub(substitutor, previous_line)

            result.append(line)
        # We're done, rewrite the file.
        with open(filename, "wt") as f:
            f.write("".join(result))


# First update the ShotGrid url for the developer site and for toolkit
for extension in list(regexes.keys()) + ["rst"]:
    print("Fixing developer.shotgunsoftware.com for .{}".format(extension))
    scan_files_for_re(
        extension,
        re.compile(r"(.*)developer.shotgunsoftware.com(.*)"),
        lambda x: x[1] + "developer.shotgridsoftware.com" + x[2],
    )
    scan_files_for_re(
        extension,
        re.compile(r"(.*)http://www.shotgunsoftware.com/toolkit(.*)"),
        lambda x: x[1] + "https://help.autodesk.com/view/SGSUB/ENU" + x[2],
    )

# Fix all file types
for extension, regex in regexes.items():
    print("Fixing Shotgun for .{}".format(extension))
    scan_files_for_re(extension, regex, to_shotgrid)
