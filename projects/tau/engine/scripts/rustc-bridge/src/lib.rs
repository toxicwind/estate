#![feature(rustc_private)]
extern crate rustc_driver;
extern crate rustc_interface;
extern crate rustc_session;
extern crate rustc_errors;
extern crate rustc_span;
extern crate rustc_hir;
extern crate rustc_middle;

use bffi::bffi;
use rustc_driver::{Callbacks, Compilation, RunCompiler};
use rustc_interface::interface;
use std::sync::{Arc, Mutex};

struct BufCallbacks { out: Arc<Mutex<Vec<u8>>> }
impl Callbacks for BufCallbacks {
    fn after_analysis<'tcx>(&mut self, _: &interface::Compiler, _: &'tcx rustc_interface::Queries<'tcx>) -> Compilation {
        Compilation::Continue
    }
}

#[bffi]
pub fn compile_json(args: Vec<String>) -> Result<String, String> {
    let out = Arc::new(Mutex::new(Vec::<u8>::new()));
    let mut cb = BufCallbacks { out: out.clone() };
    let mut full = vec!["bffi-rustc-bridge".to_string()];
    full.extend(args);
    let res = RunCompiler::new(&full, &mut cb).run();
    let text = String::from_utf8(out.lock().map_err(|e| e.to_string())?.clone())
        .map_err(|e| e.to_string())?;
    match res { Ok(()) => Ok(text), Err(_) => Err(text) }
}

#[bffi]
pub fn bridge_version() -> String { "bffi-rustc-bridge 0.1.0".into() }
