//! [`AndroidPlatform`]: the GPUI platform backend for Android.
//!
//! Structural implementation: every [`gpui::Platform`] required method is
//! present so the crate compiles for `aarch64-linux-android`; device-only
//! paths are marked `unimplemented!()` and named in the panic message.
//! State that can be tracked without a device (sheet surface handle,
//! keyboard-accessory flag, display metrics) is real.

use std::path::{Path, PathBuf};
use std::rc::Rc;
use std::sync::Arc;
use std::sync::Mutex;

use anyhow::Result;
use futures::channel::oneshot;
use gpui::*;
use ndk::native_window::NativeWindow;

use crate::DEVICE_RUNTIME;

/// The Android GPUI platform.
///
/// Created once via [`crate::create_platform`] and registered for
/// [`crate::with_platform`]. Framework-owned: surface lifecycle, touch /
/// fling / IME / key forwarding, and Choreographer-driven frames funnel
/// through here from [`crate::android::ffi`].
pub struct AndroidPlatform {
    state: Mutex<PlatformState>,
}

#[derive(Default)]
struct PlatformState {
    /// Native window most recently attached for an embedded sheet surface.
    sheet_window: Option<NativeWindow>,
    /// Opaque selection-routing handle for the sheet's GPUI window
    /// (0 is the root window; generated downstream, registered here).
    sheet_window_handle: u64,
    /// Last reported sheet surface size in physical pixels.
    sheet_surface_size: Option<(u32, u32)>,
    /// Whether the keyboard accessory bar is currently active.
    keyboard_accessory_active: bool,
}

impl AndroidPlatform {
    pub fn new() -> Self {
        Self {
            state: Mutex::new(PlatformState::default()),
        }
    }

    fn state(&self) -> std::sync::MutexGuard<'_, PlatformState> {
        self.state.lock().expect("AndroidPlatform state lock poisoned")
    }
}

// ---------------------------------------------------------------------------
// Inherent API used by the downstream app crate
// ---------------------------------------------------------------------------

impl AndroidPlatform {
    /// Opaque selection-routing handle of the sheet's GPUI window.
    pub fn sheet_window_handle(&self) -> u64 {
        self.state().sheet_window_handle
    }

    /// Attach the native window for an embedded sheet surface.
    pub fn attach_sheet_native_window(&self, window: NativeWindow) -> Result<()> {
        self.state().sheet_window = Some(window);
        Ok(())
    }

    /// Detach the sheet's native window (surface destroyed).
    pub fn detach_sheet_native_window(&self) {
        self.state().sheet_window = None;
    }

    /// Register an embedded window handle generated downstream.
    pub fn prepare_window(&self, window_handle: u64) {
        self.state().sheet_window_handle = window_handle;
    }

    /// Prepare for an embedded window; device-future (surface plumbing).
    pub fn prepare_embedded_window(&self) {
        unimplemented!("{DEVICE_RUNTIME}: prepare_embedded_window")
    }

    /// Handle a sheet surface resize; records the size, device-future apply.
    pub fn handle_sheet_surface_resize(&self, width: u32, height: u32) -> Result<()> {
        self.state().sheet_surface_size = Some((width, height));
        Ok(())
    }

    /// Forward a sheet touch event; device-future (input dispatch).
    pub fn handle_sheet_touch(&self, _action: i32, _x: f32, _y: f32) {
        unimplemented!("{DEVICE_RUNTIME}: handle_sheet_touch")
    }

    /// Forward a sheet fling gesture; device-future (input dispatch).
    pub fn handle_sheet_fling(&self, _velocity_x: f32, _velocity_y: f32) {
        unimplemented!("{DEVICE_RUNTIME}: handle_sheet_fling")
    }

    /// Drain pending framework tasks; device-future (main-looper pump).
    pub fn process_pending_tasks(&self) {
        unimplemented!("{DEVICE_RUNTIME}: process_pending_tasks")
    }

    /// Advance in-flight fling physics; device-future (Choreographer tick).
    pub fn process_fling(&self) {
        unimplemented!("{DEVICE_RUNTIME}: process_fling")
    }

    /// Request a frame for every live window; device-future (Choreographer).
    pub fn request_frame_for_all_windows(&self) {
        unimplemented!("{DEVICE_RUNTIME}: request_frame_for_all_windows")
    }

    /// Request an immediate frame; device-future (Choreographer).
    pub fn request_frame_forced(&self) {
        unimplemented!("{DEVICE_RUNTIME}: request_frame_forced")
    }

    /// Handle a keyboard accessory bar action; none active without a device.
    pub fn handle_keyboard_accessory_action(&self, _action: &str) -> bool {
        false
    }

    /// Whether the keyboard accessory bar is currently active.
    pub fn has_active_keyboard_accessory(&self) -> bool {
        self.state().keyboard_accessory_active
    }
}

impl Default for AndroidPlatform {
    fn default() -> Self {
        Self::new()
    }
}

// ---------------------------------------------------------------------------
// gpui::Platform
// ---------------------------------------------------------------------------

impl Platform for AndroidPlatform {
    fn background_executor(&self) -> BackgroundExecutor {
        unimplemented!("{DEVICE_RUNTIME}: background_executor")
    }

    fn foreground_executor(&self) -> ForegroundExecutor {
        unimplemented!("{DEVICE_RUNTIME}: foreground_executor")
    }

    fn text_system(&self) -> Arc<dyn PlatformTextSystem> {
        unimplemented!("{DEVICE_RUNTIME}: text_system")
    }

    fn run(&self, _on_finish_launching: Box<dyn 'static + FnOnce()>) {
        unimplemented!("{DEVICE_RUNTIME}: run")
    }

    fn quit(&self) {
        unimplemented!("{DEVICE_RUNTIME}: quit")
    }

    fn restart(&self, _binary_path: Option<PathBuf>) {
        unimplemented!("{DEVICE_RUNTIME}: restart")
    }

    fn activate(&self, _ignoring_other_apps: bool) {
        unimplemented!("{DEVICE_RUNTIME}: activate")
    }

    fn hide(&self) {
        unimplemented!("{DEVICE_RUNTIME}: hide")
    }

    fn hide_other_apps(&self) {
        unimplemented!("{DEVICE_RUNTIME}: hide_other_apps")
    }

    fn unhide_other_apps(&self) {
        unimplemented!("{DEVICE_RUNTIME}: unhide_other_apps")
    }

    fn displays(&self) -> Vec<Rc<dyn PlatformDisplay>> {
        unimplemented!("{DEVICE_RUNTIME}: displays")
    }

    fn primary_display(&self) -> Option<Rc<dyn PlatformDisplay>> {
        unimplemented!("{DEVICE_RUNTIME}: primary_display")
    }

    fn active_window(&self) -> Option<AnyWindowHandle> {
        unimplemented!("{DEVICE_RUNTIME}: active_window")
    }

    fn open_window(
        &self,
        _handle: AnyWindowHandle,
        _options: WindowParams,
    ) -> anyhow::Result<Box<dyn PlatformWindow>> {
        unimplemented!("{DEVICE_RUNTIME}: open_window")
    }

    fn window_appearance(&self) -> WindowAppearance {
        unimplemented!("{DEVICE_RUNTIME}: window_appearance")
    }

    fn open_url(&self, _url: &str) {
        unimplemented!("{DEVICE_RUNTIME}: open_url")
    }

    fn on_open_urls(&self, _callback: Box<dyn FnMut(Vec<String>)>) {
        unimplemented!("{DEVICE_RUNTIME}: on_open_urls")
    }

    fn register_url_scheme(&self, _url: &str) -> Task<Result<()>> {
        unimplemented!("{DEVICE_RUNTIME}: register_url_scheme")
    }

    fn prompt_for_paths(
        &self,
        _options: PathPromptOptions,
    ) -> oneshot::Receiver<Result<Option<Vec<PathBuf>>>> {
        unimplemented!("{DEVICE_RUNTIME}: prompt_for_paths")
    }

    fn prompt_for_new_path(
        &self,
        _directory: &Path,
        _suggested_name: Option<&str>,
    ) -> oneshot::Receiver<Result<Option<PathBuf>>> {
        unimplemented!("{DEVICE_RUNTIME}: prompt_for_new_path")
    }

    fn can_select_mixed_files_and_dirs(&self) -> bool {
        unimplemented!("{DEVICE_RUNTIME}: can_select_mixed_files_and_dirs")
    }

    fn reveal_path(&self, _path: &Path) {
        unimplemented!("{DEVICE_RUNTIME}: reveal_path")
    }

    fn open_with_system(&self, _path: &Path) {
        unimplemented!("{DEVICE_RUNTIME}: open_with_system")
    }

    fn on_quit(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_quit")
    }

    fn on_reopen(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_reopen")
    }

    fn on_system_wake(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_system_wake")
    }

    fn set_menus(&self, _menus: Vec<Menu>, _keymap: &Keymap) {
        unimplemented!("{DEVICE_RUNTIME}: set_menus")
    }

    fn set_dock_menu(&self, _menu: Vec<MenuItem>, _keymap: &Keymap) {
        unimplemented!("{DEVICE_RUNTIME}: set_dock_menu")
    }

    fn on_app_menu_action(&self, _callback: Box<dyn FnMut(&dyn Action)>) {
        unimplemented!("{DEVICE_RUNTIME}: on_app_menu_action")
    }

    fn on_will_open_app_menu(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_will_open_app_menu")
    }

    fn on_validate_app_menu_command(&self, _callback: Box<dyn FnMut(&dyn Action) -> bool>) {
        unimplemented!("{DEVICE_RUNTIME}: on_validate_app_menu_command")
    }

    fn thermal_state(&self) -> ThermalState {
        unimplemented!("{DEVICE_RUNTIME}: thermal_state")
    }

    fn on_thermal_state_change(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_thermal_state_change")
    }

    fn app_path(&self) -> Result<PathBuf> {
        unimplemented!("{DEVICE_RUNTIME}: app_path")
    }

    fn path_for_auxiliary_executable(&self, _name: &str) -> Result<PathBuf> {
        unimplemented!("{DEVICE_RUNTIME}: path_for_auxiliary_executable")
    }

    fn set_cursor_style(&self, _style: CursorStyle) {
        unimplemented!("{DEVICE_RUNTIME}: set_cursor_style")
    }

    fn hide_cursor_until_mouse_moves(&self) {
        unimplemented!("{DEVICE_RUNTIME}: hide_cursor_until_mouse_moves")
    }

    fn is_cursor_visible(&self) -> bool {
        unimplemented!("{DEVICE_RUNTIME}: is_cursor_visible")
    }

    fn should_auto_hide_scrollbars(&self) -> bool {
        unimplemented!("{DEVICE_RUNTIME}: should_auto_hide_scrollbars")
    }

    fn read_from_clipboard(&self) -> Option<ClipboardItem> {
        unimplemented!("{DEVICE_RUNTIME}: read_from_clipboard")
    }

    fn write_to_clipboard(&self, _item: ClipboardItem) {
        unimplemented!("{DEVICE_RUNTIME}: write_to_clipboard")
    }

    fn write_credentials(&self, _url: &str, _username: &str, _password: &[u8]) -> Task<Result<()>> {
        unimplemented!("{DEVICE_RUNTIME}: write_credentials")
    }

    fn read_credentials(&self, _url: &str) -> Task<Result<Option<(String, Vec<u8>)>>> {
        unimplemented!("{DEVICE_RUNTIME}: read_credentials")
    }

    fn delete_credentials(&self, _url: &str) -> Task<Result<()>> {
        unimplemented!("{DEVICE_RUNTIME}: delete_credentials")
    }

    fn keyboard_layout(&self) -> Box<dyn PlatformKeyboardLayout> {
        unimplemented!("{DEVICE_RUNTIME}: keyboard_layout")
    }

    fn keyboard_mapper(&self) -> Rc<dyn PlatformKeyboardMapper> {
        unimplemented!("{DEVICE_RUNTIME}: keyboard_mapper")
    }

    fn on_keyboard_layout_change(&self, _callback: Box<dyn FnMut()>) {
        unimplemented!("{DEVICE_RUNTIME}: on_keyboard_layout_change")
    }
}
