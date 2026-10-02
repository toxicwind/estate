//! Android framework layer: JNI entry points, activity lifecycle, and
//! Choreographer-driven frame callbacks.
//!
//! Device-future: the entry points below are the framework contract the
//! Kotlin side (`dev.zed.gpui.GpuiRuntimeController`, `GpuiSurfaceView`)
//! will call once the on-device runtime lands. They are declared here so
//! the contract is visible and linkable; each one names the missing piece.

pub mod ffi;
