cd /home/toxic

# full unified diff (v0.3 → v0.4)
diff -ruN Downloads/yote-v0.3.0/yote sovereign/yote > yote-v0.3-to-v0.4.patch

# view it nicely
code-insiders -r yote-v0.3-to-v0.4.patch
# or: bat yote-v0.3-to-v0.4.patch