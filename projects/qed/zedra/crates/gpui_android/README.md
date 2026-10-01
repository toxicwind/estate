# gpui_android

Android `gpui::Platform` implementation for the Zedra workspace.

## Status

API-complete against `zedra`'s Android entry code (`crates/zedra/src/android/`):
`create_platform`, `with_platform`, display metrics, sheet-window handles, and
all 47 required `Platform` trait methods compile for `aarch64-linux-android`.

The on-device runtime is the next lane: JNI lifecycle wiring
(`NativeActivity` callbacks), Choreographer frame scheduling, input dispatch,
and the wgpu/Vulkan surface are marked `unimplemented!()` and panic if
reached. A passing `cargo check` is a compile contract, not a working app.

## Building

The Android NDK must be visible. `crates/zedra/build.rs` reads
`ANDROID_NDK_HOME` (fallback `NDK_HOME`) and links the newest API sysroot it
finds. Either export it:

```
export ANDROID_NDK_HOME=/opt/android-ndk
```

or drop a `.cargo/config.toml` in the workspace root:

```toml
[env]
ANDROID_NDK_HOME = "/opt/android-ndk"
```

The `.cargo/` directory is machine-specific and intentionally untracked.

## Provenance

`gpui_android` exists in no upstream zed tree: `tanlethanh/zed` (the submodule
zedra pins) ships `gpui_wgpu` but no `gpui_android`, and the community
`Dylanmurzello/zed-android-port` fork exposes a different API. This crate was
written against the API surface zedra's Android code actually calls, as seen in
`tanlethanh/zedra@3e967986`.
