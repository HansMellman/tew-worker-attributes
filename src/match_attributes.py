import csv
import re

# Load files
with open("Attribute_Names.txt", "r", encoding="utf-8") as f:
    names_data = f.read()

with open("Attribute_definitions.txt", "r", encoding="utf-8") as f:
    defs_data = f.read()

# Parse Names
name_pattern = re.compile(
    r'push [0-9A-F]+h ; "(.*?)"\s+.*?mov var_14, ([0-9A-F]+)h', re.DOTALL
)

# attribute_names = {
#     int(code, 16): name for name, code in name_pattern.findall(names_data)
# }

attribute_names = {}
for name, code in name_pattern.findall(names_data):
    # Handle Chr(37) or similar substitutions (common for "%")
    name = re.sub(r'" *& *Chr\(37\) *& *"', "%", name)
    name = name.strip()
    attribute_names[int(code, 16)] = name

# Patch known special-case names based on Hex ID
manual_name_overrides = {
    0x0136: "100% Babyface",
    0x0139: "100% Heel",
}

attribute_names.update(manual_name_overrides)

# DEBUG: Print a few early entries to confirm correct name parsing
print("🔍 Sample of parsed attribute names:")
for code, name in sorted(attribute_names.items())[:10]:  # Show first 10
    print(f"  Hex ID {code:04X}: {repr(name)}")


# Parse definitions
def_pattern = re.compile(
    r"cmp \[eax\], ([0-9A-F]+)h.*?"
    r'(?:push [0-9A-F]+h ; "(.*?)"\s+)+'
    r"(call .*?__vbaStrCat.*?)?"
    r'(?:push [0-9A-F]+h ; "(.*?)")?'
    r'mov edx, (?:eax|[0-9A-F]+h) ; "(.*?)"',  # final move or concat'd
    re.DOTALL,
)

# Parse definitions (updated multi-line + __vbaStrCat handling)
definition_lines = defs_data.splitlines()
definitions = {}
i = 0
while i < len(definition_lines):
    line = definition_lines[i]
    code_match = re.search(r"cmp \[eax\], ([0-9A-F]+)h", line)
    if code_match:
        code = int(code_match.group(1), 16)
        parts = []
        j = i + 1
        while j < len(definition_lines):
            l = definition_lines[j]
            push_match = re.search(r'push [0-9A-F]+h ; "(.*?)"', l)
            if push_match:
                parts.append(push_match.group(1))
            elif (
                re.search(r'push [0-9A-F]+h ; "(.*?)"', l) is None
                and "call" in l
                and "__vbaStrCat" in l
            ):
                # __vbaStrCat, do nothing and keep going
                pass
            elif "mov edx" in l and ";" in l:
                final = re.search(r'; "(.*?)"', l)
                if final:
                    parts.append(final.group(1))
                break
            elif "jmp" in l:
                break
            j += 1
        combined = " ".join(parts).replace('"' + " & Chr(37) & " + '"', "%")
        definitions[code] = combined
        i = j
    else:
        i += 1


# Merge and track counts
rows = []
missing = 0

for code, name in attribute_names.items():
    desc = definitions.get(code)
    if desc is None:
        desc = "(No definition found)"
        missing += 1
    rows.append((code, name, desc))

# Print count summary
total = len(rows)
print(f"✅ Total attributes: {total}")
print(f"❌ Attributes missing definitions: {missing}")
print(f"✅ Attributes with definitions: {total - missing}")


# with open("attributes_output.html", "w", encoding="utf-8") as f:
#     f.write("""
#     <html>
#     <head>
#     <meta charset='utf-8'>
#     <style>
#         body {
#             font-family: Arial, sans-serif;
#             margin: 40px;
#             background-color: #f9f9f9;
#         }
#         h2 {
#             color: #333;
#         }
#         input[type="text"] {
#             width: 300px;
#             padding: 10px;
#             margin-bottom: 20px;
#             font-size: 16px;
#         }
#         table {
#             border-collapse: collapse;
#             width: 100%;
#             background-color: #fff;
#             box-shadow: 0 2px 8px rgba(0,0,0,0.1);
#         }
#         th, td {
#             padding: 12px 16px;
#             border: 1px solid #ddd;
#             text-align: left;
#             vertical-align: top;
#         }
#         th {
#             background-color: #004466;
#             color: #fff;
#             position: sticky;
#             top: 0;
#             z-index: 1;
#         }
#         tr:nth-child(even) {
#             background-color: #f2f2f2;
#         }
#         tr:hover {
#             background-color: #e6f7ff;
#         }
#         .container {
#             overflow-x: auto;
#         }
#         #backToTopBtn {
#             display: none;
#             position: fixed;
#             bottom: 40px;
#             right: 40px;
#             z-index: 99;
#             font-size: 16px;
#             border: none;
#             outline: none;
#             background-color: #333;
#             color: white;
#             cursor: pointer;
#             padding: 10px 16px;
#             border-radius: 8px;
#             box-shadow: 0px 2px 5px rgba(0,0,0,0.3);
#         }
#         #backToTopBtn:hover {
#             background-color: #555;
#         }
#     </style>
#     <script>
#         function filterTable() {
#             let input = document.getElementById("searchBox").value.toLowerCase();
#             let rows = document.querySelectorAll("table tr:not(:first-child)");
#             rows.forEach(row => {
#                 let text = row.textContent.toLowerCase();
#                 row.style.display = text.includes(input) ? "" : "none";
#             });
#         }

#         window.onscroll = function() { scrollFunction(); };

#         function scrollFunction() {
#             let btn = document.getElementById("backToTopBtn");
#             if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
#                 btn.style.display = "block";
#             } else {
#                 btn.style.display = "none";
#             }
#         }

#         function topFunction() {
#             window.scrollTo({ top: 0, behavior: 'smooth' });
#         }
#     </script>
#     </head>
#     <body>
#     <h2>Attribute Names and Definitions</h2>
#     <input type="text" id="searchBox" onkeyup="filterTable()" placeholder="Search attributes...">
#     <div class="container">
#     <table>
#         <tr>
#             <th>#</th>
#             <th>Name</th>
#             <th>Description</th>
#         </tr>
#     """)

#     for idx, (_, name, desc) in enumerate(rows, 1):  # start at 1
#         f.write(
#             f"<tr><td>{idx}</td><td>{html.escape(name)}</td><td>{html.escape(desc)}</td></tr>\n"
#         )

#     f.write("""
#     </table>
#     </div>
#     <button onclick="topFunction()" id="backToTopBtn" title="Go to top">⬆ Top</button>
#     </body>
#     </html>
#     """)


# Write a more human-friendly CSV with row numbers
with open("attribute_definitions.csv", "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["#", "Name", "Description", "Category"])  # new header
    for idx, (_, name, desc) in enumerate(rows, 1):  # start index at 1
        writer.writerow([idx, name, desc, ""])  # skip Hex ID, add blank Category
