import io

P = "README.md"
t = io.open(P, encoding="utf-8").read()

# 1. Badges + MANIFESTO pointer directly under the H1
old_h1 = "# \u7d50\u3073\u306e\u7e04 (Musubi no Nawa)\n"
assert t.count(old_h1) == 1, "h1 anchor not unique"
t = t.replace(old_h1, old_h1 + "\n" + io.open("/home/toxic/.fleet-bus/readme-op/work/dunlin/.xfer/musubi_badges.md", encoding="utf-8").read(), 1)

# 2. Broken relative links to repos/ -> canonical external corpus repo
t = t.replace("](repos/deepfield-public-research/", "](https://github.com/deepfield/public-research/blob/main/")

# 3. Replace the stale Submodules section (VI) with the verified source layout
start = t.index("## VI. Submodules")
end = t.index("## VII. The Vision")
sec6 = io.open("/home/toxic/.fleet-bus/readme-op/work/dunlin/.xfer/musubi_sec6.md", encoding="utf-8").read()
t = t[:start] + sec6 + "\n\n" + t[end:]

io.open(P, "w", encoding="utf-8").write(t)
print("spliced OK, new size:", len(t))
