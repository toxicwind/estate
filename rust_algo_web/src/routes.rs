use axum::{routing::{get,post}, Router, Json, extract::State}; use serde::{Deserialize,Serialize}; use std::{sync::Arc, time::Instant, collections::HashMap};
#[derive(Clone)] pub struct AppState{ pub start:Instant, pub ports:HashMap<String,u16> }
async fn chk(p:u16)->(bool,u128){ let t=Instant::now(); (tokio::net::TcpStream::connect(format!("127.0.0.1:{p}")).await.is_ok(), t.elapsed().as_millis()) }
#[derive(Serialize)] struct LoRA{id:String,name:String,price:f32,ctx:u32,vram:String,quant:String,fork:String}
#[derive(Deserialize)] struct Req{prompt:String}
pub fn api()->Router<Arc<AppState>>{
 Router::new()
 .route("/health",get(||async{ "ok" }))
 .route("/api/health",get(|State(s):State<Arc<AppState>>|async move{ Json(serde_json::json!({"status":"ok","uptime":s.start.elapsed().as_secs()})) }))
 .route("/api/config",get(|State(s):State<Arc<AppState>>|async move{Json(serde_json::json!({"ports":s.ports,"brand":"effusionlabs.com"}))}))
 .route("/api/status",get(|State(s):State<Arc<AppState>>|async move{ let mut m=HashMap::new(); for(k,p) in &s.ports{ let(on,ms)=chk(*p).await; m.insert(k.clone(),serde_json::json!({"port":p,"online":on,"ms":ms})); } Json(m)}))
 .route("/api/loras",get(||async{ Json(vec![LoRA{id:"beellama/gemma-128k".into(),name:"Gemma 128K Beellama".into(),price:7.0,ctx:131072,vram:"~13GB".into(),quant:"IQ4_XS".into(),fork:"beellama".into()},LoRA{id:"turboquant/gemma-96k".into(),name:"Gemma 96K Turbo".into(),price:5.0,ctx:98304,vram:"~11GB".into(),quant:"IQ4_NL".into(),fork:"turboquant".into()},LoRA{id:"ik_llama/gemma-64k".into(),name:"Gemma 64K IK".into(),price:4.0,ctx:65536,vram:"~9GB".into(),quant:"IQ4_XS".into(),fork:"ik_llama".into()}])}))
 .route("/api/route",post(|State(s):State<Arc<AppState>>,Json(r):Json<Req>|async move{ let t=Instant::now(); let sel=if r.prompt.len()<50{"turboquant/gemma-96k"}else{"beellama/gemma-128k"}; Json(serde_json::json!({"selected":sel,"latency_ms":t.elapsed().as_millis(),"uptime":s.start.elapsed().as_secs()}))}))
 .route("/api/fleet/last",get(||async{ let p="/home/toxic/sovereign/tools/fleet/results/bench-forks-latest.json"; if let Ok(s)=tokio::fs::read_to_string(p).await{ if let Ok(v)=serde_json::from_str::<serde_json::Value>(&s){ return Json(v); } } Json(serde_json::json!({"status":"no bench yet","hint":p}))}))
 .route("/api/fleet/forks",get(||async{ let p="/home/toxic/sovereign/tools/fleet/forks.json"; if let Ok(s)=tokio::fs::read_to_string(p).await{ if let Ok(v)=serde_json::from_str::<serde_json::Value>(&s){ return Json(v); } } Json(serde_json::json!({}))}))
}
