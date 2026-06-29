// src/llm.rs — final sovereign version (chat + tools with fallback)
use serde::{Serialize, Deserialize};
use reqwest::Client;
use std::collections::HashMap;
use tokio::sync::RwLock;
use lazy_static::lazy_static;
use serde_json::json;

use crate::algo::Weights;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct AdvisorRequest {
    pub prompt: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AdvisorResponse {
    pub weights: Weights,
    pub explanation: String,
}

#[derive(Deserialize)]
struct ModelList {
    data: Vec<ModelInfo>,
}

#[derive(Deserialize)]
struct ModelInfo {
    id: String,
}

// Tool schema
#[derive(Serialize)]
struct Tool {
    r#type: String,
    function: FunctionDef,
}

#[derive(Serialize)]
struct FunctionDef {
    name: String,
    description: String,
    parameters: serde_json::Value,
}

#[derive(Serialize)]
struct ChatMessage {
    role: String,
    content: String,
}

#[derive(Serialize)]
struct ChatRequest {
    model: String,
    messages: Vec<ChatMessage>,
    tools: Vec<Tool>,
    tool_choice: serde_json::Value,
}

#[derive(Deserialize)]
struct ChatResponse {
    choices: Vec<ChatChoice>,
}

#[derive(Deserialize)]
struct ChatChoice {
    message: Option<AssistantMessage>,
}

#[derive(Deserialize)]
struct AssistantMessage {
    tool_calls: Option<Vec<ToolCall>>,
    content: Option<String>,
}

#[derive(Deserialize)]
struct ToolCall {
    function: FunctionCall,
}

#[derive(Deserialize)]
struct FunctionCall {
    arguments: String,
}

lazy_static! {
    static ref ADVISOR_CACHE: RwLock<HashMap<String, AdvisorResponse>> =
        RwLock::new(HashMap::new());
}

pub async fn consult_advisor(req: AdvisorRequest) -> Result<AdvisorResponse, String> {
    if let Some(cached) = ADVISOR_CACHE.read().await.get(&req.prompt) {
        return Ok(cached.clone());
    }

    let model = get_active_model().await?;
    let intent = extract_intent(&model, &req.prompt).await?;
    let weights_json = infer_weights(&model, &intent).await?;
    let advisor_response = format_output_with_tool(&model, &intent, &weights_json).await?;

    ADVISOR_CACHE.write().await.insert(req.prompt.clone(), advisor_response.clone());
    Ok(advisor_response)
}

async fn get_active_model() -> Result<String, String> {
    let base = std::env::var("LLM_PROXY_URL")
        .unwrap_or_else(|_| "http://127.0.0.1:25008".to_string());

    let client = Client::new();
    let resp = client.get(format!("{}/v1/models", base))
        .send().await.map_err(|e| format!("Failed to query /v1/models: {}", e))?;

    let parsed = resp.json::<ModelList>().await
        .map_err(|e| format!("Failed to parse /v1/models: {}", e))?;

    parsed.data.first().map(|m| m.id.clone())
        .ok_or_else(|| "No models returned from server".to_string())
}

async fn extract_intent(model: &str, user_prompt: &str) -> Result<String, String> {
    let base = std::env::var("LLM_PROXY_URL").unwrap_or_else(|_| "http://127.0.0.1:25008".to_string());
    let system = "Extract the user's DevOps priorities and constraints. Think step by step. Output ONLY a single valid JSON object. No markdown, no prose outside the JSON.\n{ \"intent\": { ... } }";
    let prompt = format!("{}\n\nUser:\n{}", system, user_prompt);

    let body = json!({ "model": model, "prompt": prompt });
    let client = Client::new();
    let resp = client.post(format!("{}/v1/completions", base)).json(&body)
        .send().await.map_err(|e| format!("LLM request failed: {}", e))?;

    let parsed: serde_json::Value = resp.json().await.map_err(|e| format!("Failed to parse: {}", e))?;
    parsed["choices"][0]["text"].as_str().map(|s| s.to_string())
        .ok_or_else(|| "No text in response".to_string())
}

async fn infer_weights(model: &str, intent_json: &str) -> Result<String, String> {
    let base = std::env::var("LLM_PROXY_URL").unwrap_or_else(|_| "http://127.0.0.1:25008".to_string());
    let system = "Convert the intent JSON into numeric weights between 0.0 and 1.0 for:\nnix_overhead, tui_gui_polish, performance, setup_speed, orchestration, portability.\nThink step by step. Output ONLY a single valid JSON object. No markdown, no prose outside the JSON.\n{ \"weights\": { ... } }";
    let prompt = format!("{}\n\nIntent:\n{}", system, intent_json);

    let body = json!({ "model": model, "prompt": prompt });
    let client = Client::new();
    let resp = client.post(format!("{}/v1/completions", base)).json(&body)
        .send().await.map_err(|e| format!("LLM request failed: {}", e))?;

    let parsed: serde_json::Value = resp.json().await.map_err(|e| format!("Failed to parse: {}", e))?;
    parsed["choices"][0]["text"].as_str().map(|s| s.to_string())
        .ok_or_else(|| "No text in response".to_string())
}

async fn format_output_with_tool(
    model: &str,
    intent_json: &str,
    weights_json: &str,
) -> Result<AdvisorResponse, String> {
    let base = std::env::var("LLM_PROXY_URL").unwrap_or_else(|_| "http://127.0.0.1:25008".to_string());

    let system = "You are a precise DevOps trade-off advisor. Use the provided tool to return the final structured recommendation.";

    let user_content = format!(
        "Intent JSON:\n{}\n\nWeights JSON:\n{}\n\nCall the return_devops_advice tool with the combined result.",
        intent_json, weights_json
    );

    let tool = Tool {
        r#type: "function".to_string(),
        function: FunctionDef {
            name: "return_devops_advice".to_string(),
            description: "Return the final advisor output with numeric weights and concise explanation referencing tradeoffs.".to_string(),
            parameters: json!({
                "type": "object",
                "properties": {
                    "weights": { "type": "object" },
                    "explanation": { "type": "string" }
                },
                "required": ["weights", "explanation"]
            }),
        },
    };

    let body = ChatRequest {
        model: model.to_string(),
        messages: vec![
            ChatMessage { role: "system".to_string(), content: system.to_string() },
            ChatMessage { role: "user".to_string(), content: user_content },
        ],
        tools: vec![tool],
        tool_choice: json!({"type": "function", "function": {"name": "return_devops_advice"}}),
    };

    let client = Client::new();
    let resp = client.post(format!("{}/v1/chat/completions", base)).json(&body)
        .send().await.map_err(|e| format!("Chat tool request failed: {}", e))?;

    let parsed: ChatResponse = resp.json().await
        .map_err(|e| format!("Failed to parse chat response: {}", e))?;

    if let Some(msg) = parsed.choices.first().and_then(|c| c.message.as_ref()) {
        // Primary: tool_calls
        if let Some(tool_calls) = &msg.tool_calls {
            if let Some(tc) = tool_calls.first() {
                if let Ok(resp) = serde_json::from_str::<AdvisorResponse>(&tc.function.arguments) {
                    return Ok(resp);
                }
            }
        }

        // Fallback 1: direct content as JSON
        if let Some(content) = &msg.content {
            let trimmed = content.trim();
            if let Ok(resp) = serde_json::from_str::<AdvisorResponse>(trimmed) {
                return Ok(resp);
            }
            // Fallback 2: legacy brace parser
            if let Ok(resp) = parse_llm_json(trimmed) {
                return Ok(resp);
            }
        }
    }

    Err("No valid tool call or parsable content in response".to_string())
}

fn parse_llm_json(content: &str) -> Result<AdvisorResponse, String> {
    let Some(start) = content.find('{') else {
        return Err("No JSON object found".into());
    };

    let mut depth = 0;
    let mut in_string = false;
    let mut escape = false;

    for (i, c) in content[start..].char_indices() {
        let idx = start + i;
        if escape { escape = false; continue; }
        match c {
            '\\' if in_string => escape = true,
            '"' => in_string = !in_string,
            '{' if !in_string => depth += 1,
            '}' if !in_string => {
                depth -= 1;
                if depth == 0 {
                    let json_str = &content[start..=idx];
                    return serde_json::from_str::<AdvisorResponse>(json_str)
                        .map_err(|e| format!("JSON parse error: {}", e));
                }
            }
            _ => {}
        }
    }
    Err("Unclosed JSON object".into())
}