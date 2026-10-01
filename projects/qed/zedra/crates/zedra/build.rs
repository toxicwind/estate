use std::env;

fn main() {
    let target = env::var("TARGET").unwrap_or_default();

    if target.contains("android") {
        // Android-specific build configuration
        println!("cargo:rustc-link-lib=log");

        // Set up paths for Android NDK (r25+ sysroot layout:
        // toolchains/llvm/prebuilt/<host>/sysroot/usr/lib/<triple>/<api>/)
        let ndk_home = env::var("ANDROID_NDK_HOME")
            .or_else(|_| env::var("NDK_HOME"))
            .expect("ANDROID_NDK_HOME or NDK_HOME must be set");

        let target_triple = if target.contains("aarch64") {
            "aarch64-linux-android"
        } else if target.contains("armv7") {
            "arm-linux-androideabi"
        } else if target.contains("i686") {
            "i686-linux-android"
        } else {
            "x86_64-linux-android"
        };

        let lib_base = format!(
            "{}/toolchains/llvm/prebuilt/linux-x86_64/sysroot/usr/lib/{}",
            ndk_home, target_triple
        );
        // Pick the highest API level the NDK ships for this triple so the
        // link search keeps working across NDK upgrades.
        let api: u32 = std::fs::read_dir(&lib_base)
            .unwrap_or_else(|e| panic!("read NDK sysroot lib dir {lib_base}: {e}"))
            .filter_map(|e| e.ok())
            .filter_map(|e| {
                e.file_type()
                    .ok()
                    .filter(|t| t.is_dir())
                    .and_then(|_| e.file_name().into_string().ok())
            })
            .filter_map(|n| n.parse::<u32>().ok())
            .max()
            .expect("no API level dirs in NDK sysroot lib dir");

        println!("cargo:rustc-link-search=native={lib_base}/{api}");
        println!("cargo:rerun-if-env-changed=ANDROID_NDK_HOME");
        println!("cargo:rerun-if-env-changed=NDK_HOME");
    }

    if target.contains("apple-ios") {
        // Weak stub for Rust->iOS — lets the cdylib link succeed.
        // The real native implementation overrides this at Xcode link time.
        println!("cargo:rerun-if-changed=src/ios_stub.c");
        cc::Build::new()
            .file("src/ios_stub.c")
            .flag("-Wno-unused-parameter")
            .compile("ios_stub");

        // NSLog bridge — routes Rust log output through NSLog so it appears
        // in idevicesyslog (os_log goes to the unified log, not ASL relay).
        println!("cargo:rerun-if-changed=src/ios/nslog_bridge.m");
        cc::Build::new()
            .file("src/ios/nslog_bridge.m")
            .flag("-fobjc-arc")
            .compile("nslog_bridge");

        let crate_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
        let config = cbindgen::Config::from_file(format!("{crate_dir}/cbindgen.toml"))
            .expect("read cbindgen.toml");
        cbindgen::Builder::new()
            .with_crate(crate_dir)
            .with_config(config)
            .generate()
            .expect("Unable to generate bindings")
            .write_to_file("../../include/zedra_ios.h");
    }
}
