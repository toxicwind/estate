import sys

P = "/home/toxic/merge-swap-1219/herd/internal/config/config.go"
with open(P) as f:
    src = f.read()

dup = (
    '\tRouting              RoutingConfig            `yaml:"routing"`\n'
    '\tGroups               map[string]GroupConfig   `yaml:"groups"`\n'
    '\tMatrix               *MatrixConfig            `yaml:"matrix"`\n'
    '\tMacros               MacroList                `yaml:"macros"`\n'
)
count = src.count(dup)
print("dup block occurrences:", count)
if count != 1:
    sys.exit("unexpected dup count, aborting")

replacement = '\tSelectors            map[string]SelectorConfig `yaml:"selectors"`\n'
src = src.replace(dup, replacement)

with open(P, "w") as f:
    f.write(src)
print("fixed: dup block replaced with Selectors field")
