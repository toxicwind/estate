p = "/home/toxic/projects/rig-work/crates/openfang-kernel/src/kernel.rs"
s = open(p).read()
old = """                                        // Compare key fields to detect changes.
                                        // IMPORTANT: keep this list in sync with AgentManifest
                                        // fields that users may legitimately edit in agent.toml.
                                        // Missing a field here means changes to it are silently
                                        // ignored until the agent is deleted and recreated.
"""
assert old in s, "anchor not found"
new = """                                        // Whole-manifest comparison: every AgentManifest
                                        // field participates (see disk_manifest_differs),
                                        // so edits to fields like model.base_url or
                                        // model.api_key_env are no longer silently
                                        // ignored until the agent is deleted and
                                        // recreated. Kernel-derived fields the TOML
                                        // legitimately omits (workspace, state_dir)
                                        // are normalized from the DB row (#1097).
"""
s = s.replace(old, new, 1)
# Now remove the old `let changed = ...` chain, keeping only the call.
start_marker = "                                        let changed = disk_manifest.name != entry.manifest.name"
end_marker = "                                                != entry.manifest.exec_policy;"
i = s.index(start_marker)
j = s.index(end_marker) + len(end_marker)
old_chain = s[i:j]
replacement = ("                                        let changed =\n"
               "                                            disk_manifest_differs(&disk_manifest, &entry.manifest);")
s = s[:i] + replacement + s[j:]
open(p, "w").write(s)
print("sync loop predicate replaced")
