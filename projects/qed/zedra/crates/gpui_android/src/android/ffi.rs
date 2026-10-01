//! Framework JNI contract for `dev.zed.gpui`.
//!
//! Called from Kotlin (`GpuiRuntimeController`, `GpuiSurfaceView`) once the
//! on-device runtime lands:
//!
//! * `gpuiInit` — store the JVM and activity, before the downstream app's
//!   launch entry point runs.
//! * `gpuiDidFinishLaunching` — the OS handed us a live activity; fire the
//!   finish-launching callback registered by the downstream app.
//! * `gpuiOnResume` / `gpuiOnPause` / `gpuiOnDestroy` — activity lifecycle.
//! * `gpuiGetDisplayDensity` — logical density for the framework.
//! * `GpuiSurfaceView_native*` — surface lifecycle, touch / fling / IME /
//!   key forwarding, and Choreographer frame callbacks.
//!
//! Every entry point below is device-future and names the missing runtime
//! piece in its panic message.

use std::ffi::c_void;

use crate::DEVICE_RUNTIME;

/// Store the JVM and activity. Runs before the downstream launch entry.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiInit(
    _env: *mut c_void,
    _class: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: gpuiInit (JVM/activity capture)")
}

/// The OS handed us a live activity; fire the finish-launching callback.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiDidFinishLaunching(
    _env: *mut c_void,
    _class: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: gpuiDidFinishLaunching")
}

/// Activity moved to the foreground.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiOnResume(
    _env: *mut c_void,
    _class: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: gpuiOnResume")
}

/// Activity moved to the background.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiOnPause(
    _env: *mut c_void,
    _class: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: gpuiOnPause")
}

/// Activity is being destroyed.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiOnDestroy(
    _env: *mut c_void,
    _class: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: gpuiOnDestroy")
}

/// Logical display density of the default display.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiRuntimeController_gpuiGetDisplayDensity(
    _env: *mut c_void,
    _class: *mut c_void,
) -> f32 {
    unimplemented!("{DEVICE_RUNTIME}: gpuiGetDisplayDensity")
}

/// A native surface was created for the root `GpuiSurfaceView`.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiSurfaceView_nativeSurfaceCreated(
    _env: *mut c_void,
    _this: *mut c_void,
    _surface: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: nativeSurfaceCreated (ANativeWindow attach)")
}

/// The root surface changed size.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiSurfaceView_nativeSurfaceChanged(
    _env: *mut c_void,
    _this: *mut c_void,
    _width: i32,
    _height: i32,
) {
    unimplemented!("{DEVICE_RUNTIME}: nativeSurfaceChanged")
}

/// The root surface was destroyed.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiSurfaceView_nativeSurfaceDestroyed(
    _env: *mut c_void,
    _this: *mut c_void,
) {
    unimplemented!("{DEVICE_RUNTIME}: nativeSurfaceDestroyed")
}

/// Choreographer frame callback: drive one GPUI frame.
#[unsafe(no_mangle)]
pub extern "system" fn Java_dev_zed_gpui_GpuiSurfaceView_nativeFrameCallback(
    _env: *mut c_void,
    _this: *mut c_void,
    _frame_time_nanos: i64,
) {
    unimplemented!("{DEVICE_RUNTIME}: nativeFrameCallback (Choreographer)")
}
