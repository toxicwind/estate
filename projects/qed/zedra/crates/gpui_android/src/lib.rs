//! `gpui_android` — the GPUI [`Platform`](gpui::Platform) backend for Android.
//!
//! ## Architecture
//!
//! ```text
//! Android app (Kotlin) -> gpui_android -> gpui_wgpu -> wgpu/Vulkan
//! ```
//!
//! The downstream app crate (`zedra`) owns app-specific JNI (sheets,
//! deeplinks, QR scanner, alerts, native selection, text input, floating
//! button, dictation preview, notifications, app metadata). Everything
//! framework-level — surface lifecycle, touch / fling / IME / key forwarding,
//! Choreographer-driven frames, `AndroidPlatform` lifecycle — lives here,
//! mirroring the iOS pattern where `gpui_ios` owns the platform view and the
//! downstream app is a thin shell.
//!
//! ## Status: structural crate
//!
//! This crate is API-complete against the interface the downstream app was
//! written against (`create_platform`, `with_platform`, the display-metric
//! accessors, and the `AndroidPlatform` inherent API), and it compiles for
//! `aarch64-linux-android`. The on-device runtime — JNI lifecycle wiring,
//! `Choreographer` frame callbacks, and the `wgpu`/Vulkan surface — is the
//! next lane and is marked `unimplemented!()` at each device-only path.
//!
//! ## Entry points
//!
//! * [`create_platform`] — build the `Rc<dyn Platform>` the app boots from.
//! * [`with_platform`] — run a closure against the registered platform, if any.
//! * [`display_scale`], [`keyboard_height`], [`system_inset_top`],
//!   [`system_inset_bottom`] — display metrics, updated from the framework
//!   JNI layer via [`set_display_metrics`].
//! * [`android::ffi`] — the framework JNI contract (`dev.zed.gpui`).

pub use gpui;

pub mod android;
mod platform;

pub use platform::AndroidPlatform;

use std::rc::Rc;
use std::sync::atomic::{AtomicPtr, AtomicU32, Ordering};

use gpui::Platform;

const DEVICE_RUNTIME: &str =
    "AndroidPlatform: requires the on-device runtime (JNI lifecycle + wgpu/Vulkan surface)";

/// The platform instance registered by [`create_platform`].
///
/// The `Rc` is intentionally leaked: the platform lives for the process
/// lifetime, created once at launch. The raw pointer makes the registry
/// `Sync` so JNI callbacks on any thread can reach it; validity is
/// guaranteed because the leaked `Rc` is never dropped.
static PLATFORM: AtomicPtr<AndroidPlatform> = AtomicPtr::new(std::ptr::null_mut());

/// Build the Android platform and register it for [`with_platform`].
///
/// Called once from the downstream app's launch entry point, before the
/// framework's `gpui_android_did_finish_launching` fires.
pub fn create_platform() -> Rc<dyn Platform> {
    let concrete = Rc::new(AndroidPlatform::new());
    // Hold one refcount for the registry; the platform is never unregistered.
    let raw = Rc::into_raw(concrete.clone()) as *mut AndroidPlatform;
    PLATFORM.store(raw, Ordering::SeqCst);
    concrete
}

/// Run `f` against the registered platform, or return `None` when
/// [`create_platform`] has not run yet on this process.
pub fn with_platform<R>(f: impl FnOnce(&AndroidPlatform) -> R) -> Option<R> {
    let raw = PLATFORM.load(Ordering::SeqCst);
    if raw.is_null() {
        None
    } else {
        // SAFETY: `raw` is either null or points at the leaked `Rc` from
        // `create_platform`, which lives for the process lifetime.
        Some(f(unsafe { &*raw }))
    }
}

// ---------------------------------------------------------------------------
// Display metrics
// ---------------------------------------------------------------------------
//
// Written from the framework JNI layer when the activity reports new
// metrics; read from any thread by the downstream app.

static DISPLAY_SCALE_BITS: AtomicU32 = AtomicU32::new(0x40000000); // 2.0f32
static KEYBOARD_HEIGHT_PX: AtomicU32 = AtomicU32::new(0);
static SYSTEM_INSET_TOP_PX: AtomicU32 = AtomicU32::new(0);
static SYSTEM_INSET_BOTTOM_PX: AtomicU32 = AtomicU32::new(0);

/// Logical display density (e.g. 2.0 on xhdpi).
pub fn display_scale() -> f32 {
    f32::from_bits(DISPLAY_SCALE_BITS.load(Ordering::Relaxed))
}

/// Visible keyboard height in physical pixels, 0 when hidden.
pub fn keyboard_height() -> u32 {
    KEYBOARD_HEIGHT_PX.load(Ordering::Relaxed)
}

/// System inset at the top (status bar / cutout) in physical pixels.
pub fn system_inset_top() -> u32 {
    SYSTEM_INSET_TOP_PX.load(Ordering::Relaxed)
}

/// System inset at the bottom (navigation bar) in physical pixels.
pub fn system_inset_bottom() -> u32 {
    SYSTEM_INSET_BOTTOM_PX.load(Ordering::Relaxed)
}

/// Publish fresh display metrics from the framework JNI layer.
pub fn set_display_metrics(scale: f32, inset_top: u32, inset_bottom: u32, keyboard_height_px: u32) {
    DISPLAY_SCALE_BITS.store(scale.to_bits(), Ordering::Relaxed);
    SYSTEM_INSET_TOP_PX.store(inset_top, Ordering::Relaxed);
    SYSTEM_INSET_BOTTOM_PX.store(inset_bottom, Ordering::Relaxed);
    KEYBOARD_HEIGHT_PX.store(keyboard_height_px, Ordering::Relaxed);
}
