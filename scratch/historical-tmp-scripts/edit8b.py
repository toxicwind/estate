p = "/home/toxic/projects/rig-work/crates/openfang-types/src/config.rs"
s = open(p).read()
old = """            skills: HashMap::new(),
        },
            config_path: None,
    }
}"""
assert old in s
new = """            skills: HashMap::new(),
            config_path: None,
        }
    }
}"""
s = s.replace(old, new, 1)
open(p, "w").write(s)
print("fixed")
