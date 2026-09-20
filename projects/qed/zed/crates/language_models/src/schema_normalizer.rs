//! Shared JSON-Schema normalizer for Outlines-backed OpenAI-compatible endpoints.
//!
//! Zed's generic OpenAI-compatible provider emits the OpenAI *subset* of JSON
//! Schema. The subset transform collapses `type: ["string","null"]` to its
//! first entry and rewrites `oneOf` -> `anyOf`. vLLM/Outlines — the tool-call
//! grammar parser behind NVIDIA NIM and many OpenAI-compatible backends —
//! 500s on the result ("Could not translate instance to regex"), which makes
//! Zed retry forever.
//!
//! The providers that target those endpoints
//! (`openai_mcpproxy`, `openai_mcpproxy_nvidia`, `nvidia`) therefore send
//! **full JSON Schema** (draft07) and run every tool schema through
//! [`normalize_tool_schemas`] first. The normalization is non-destructive:
//! no tool-count cap, no description truncation — the mcpproxy compact router
//! is what keeps the *set* small via progressive disclosure
//! (`retrieve_tools` / `describe_tool`); the provider must never drop a tool.
//!
//! Repairs applied (recursively):
//! * missing root `type` -> `"object"`
//! * untyped properties -> `"string"`
//! * bare `"null"` entries stripped from multi-type arrays
//!   (`["string","null"]` -> `["string"]`)
//! * nested object schemas normalized even when `type` is an array containing
//!   `"object"` (e.g. `["object","null"]`), and `items` element schemas of
//!   arrays get the same treatment.

use language_model::{LanguageModelRequestTool, LanguageModelRequestToolInput};

/// Normalize every tool's input schema so Outlines can compile it.
/// Returns every tool unchanged otherwise.
pub fn normalize_tool_schemas(tools: Vec<LanguageModelRequestTool>) -> Vec<LanguageModelRequestTool> {
    tools
        .into_iter()
        .map(|mut tool| {
            if let LanguageModelRequestToolInput::Function { input_schema, .. } = &mut tool.input {
                *input_schema = normalize_schema(input_schema.clone());
            }
            tool
        })
        .collect()
}

/// Repair a single JSON Schema value so Outlines can compile it.
///
/// The value is expected to describe an object (tool input schemas always
/// do); a non-object root is replaced with an empty object schema rather
/// than passed through half-formed.
fn normalize_schema(mut schema: serde_json::Value) -> serde_json::Value {
    if !schema.is_object() {
        return serde_json::json!({ "type": "object" });
    }

    // Ensure an explicit object root. Outlines needs one; a type array that
    // contains "object" (e.g. ["object","null"] with "null" stripped) counts
    // as explicit and keeps its array form, so nullability information
    // survives the recursion from normalize_property. Anything else is
    // replaced with "object" so the grammar compiler never sees ambiguity.
    let is_explicit_object = match schema.get("type") {
        Some(serde_json::Value::String(s)) => s == "object",
        Some(serde_json::Value::Array(a)) => {
            let cleaned: Vec<serde_json::Value> = a
                .iter()
                .filter(|v| {
                    !matches!(v, serde_json::Value::String(s) if s == "null")
                })
                .cloned()
                .collect();
            let has_object = cleaned
                .iter()
                .any(|v| matches!(v, serde_json::Value::String(s) if s == "object"));
            if has_object {
                schema["type"] = serde_json::Value::Array(cleaned);
            }
            has_object
        }
        _ => false,
    };
    if !is_explicit_object {
        schema["type"] = serde_json::json!("object");
    }

    // Recurse into properties, giving each an explicit type when missing.
    if let Some(props) = schema
        .get_mut("properties")
        .and_then(|p| p.as_object_mut())
    {
        for (_name, prop) in props.iter_mut() {
            if prop.is_object() {
                normalize_property(prop);
            }
        }
    }
    schema
}

/// Normalize one property schema in place: explicit type, null-stripping,
/// then recursion into nested objects and array element schemas.
fn normalize_property(prop: &mut serde_json::Value) {
    let t = prop.get("type").cloned();
    let has_type = match &t {
        Some(serde_json::Value::String(s)) => !s.is_empty() && s != "null",
        Some(serde_json::Value::Array(a)) => {
            // Multi-type: keep, but drop bare "null" entries that Outlines
            // cannot translate.
            let cleaned: Vec<_> = a
                .iter()
                .filter(|v| !matches!(v, serde_json::Value::String(s) if s == "null"))
                .cloned()
                .collect();
            let non_empty = !cleaned.is_empty();
            prop["type"] = serde_json::Value::Array(cleaned);
            non_empty
        }
        _ => false,
    };
    if !has_type {
        prop["type"] = serde_json::json!("string");
    }

    // Recurse into nested object schemas — whether `type` is the plain
    // string "object" or an array containing it (e.g. ["object","null"]
    // with "null" stripped above).
    if is_object_schema(prop) {
        *prop = normalize_schema(prop.clone());
    }

    // Recurse into array element schemas so
    // `items: {type: "object", properties: ...}` gets the same treatment.
    // Only object-shaped `items` are descended into; scalar element types
    // are left alone (normalize_schema would otherwise force them to
    // "object").
    if let Some(items) = prop.get_mut("items") {
        if is_object_schema(items) {
            let normalized = normalize_schema(items.clone());
            *items = normalized;
        }
    }
}

/// True when this schema node describes an object, so `normalize_schema`'s
/// object-oriented repairs apply: explicit `"object"`, an array containing
/// it, or a typeless node carrying `properties`.
fn is_object_schema(node: &serde_json::Value) -> bool {
    if !node.is_object() {
        return false;
    }
    match node.get("type") {
        Some(serde_json::Value::String(s)) => s == "object",
        Some(serde_json::Value::Array(a)) => a
            .iter()
            .any(|v| matches!(v, serde_json::Value::String(s) if s == "object")),
        _ => node.get("properties").is_some(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn function_tool(name: &str, schema: serde_json::Value) -> LanguageModelRequestTool {
        LanguageModelRequestTool {
            name: name.into(),
            description: "test tool".into(),
            input: LanguageModelRequestToolInput::Function {
                use_input_streaming: false,
                input_schema: schema,
            },
        }
    }

    fn input_schema_of(tool: &LanguageModelRequestTool) -> &serde_json::Value {
        match &tool.input {
            LanguageModelRequestToolInput::Function { input_schema, .. } => input_schema,
            _ => panic!("expected function input"),
        }
    }

    #[test]
    fn repairs_structural_defects_without_dropping_tools() {
        let tools = vec![
            // Untyped root + untyped property -> should become object/string.
            function_tool("a", serde_json::json!({"properties": {"q": {}}})),
            // Nullable property -> bare "null" dropped, keeps "string".
            function_tool(
                "b",
                serde_json::json!({
                    "type": "object",
                    "properties": {"q": {"type": ["string", "null"]}}
                }),
            ),
        ];

        let normalized = normalize_tool_schemas(tools);
        // No tool dropped.
        assert_eq!(normalized.len(), 2);

        let a = input_schema_of(&normalized[0]);
        assert_eq!(a["type"], "object");
        assert_eq!(a["properties"]["q"]["type"], "string");

        let b = input_schema_of(&normalized[1]);
        assert_eq!(b["properties"]["q"]["type"], serde_json::json!(["string"]));
    }

    #[test]
    fn recurses_into_nullable_object_properties() {
        // ["object","null"] with "null" stripped must still recurse: the
        // nested property gets its explicit type.
        let tools = vec![function_tool(
            "c",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "nested": {
                        "type": ["object", "null"],
                        "properties": {"inner": {}}
                    }
                }
            }),
        )];

        let normalized = normalize_tool_schemas(tools);
        let schema = input_schema_of(&normalized[0]);
        assert_eq!(
            schema["properties"]["nested"]["type"],
            serde_json::json!(["object"])
        );
        assert_eq!(
            schema["properties"]["nested"]["properties"]["inner"]["type"],
            "string"
        );
    }

    #[test]
    fn recurses_into_array_items() {
        // items: {type: object, properties: ...} gets normalized too.
        let tools = vec![function_tool(
            "d",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "list": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"name": {}}
                        }
                    }
                }
            }),
        )];

        let normalized = normalize_tool_schemas(tools);
        let schema = input_schema_of(&normalized[0]);
        assert_eq!(
            schema["properties"]["list"]["items"]["properties"]["name"]["type"],
            "string"
        );
    }

    #[test]
    fn leaves_scalar_items_alone() {
        // items: {type: "string"} must NOT be forced to object.
        let tools = vec![function_tool(
            "e",
            serde_json::json!({
                "type": "object",
                "properties": {
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            }),
        )];

        let normalized = normalize_tool_schemas(tools);
        let schema = input_schema_of(&normalized[0]);
        assert_eq!(
            schema["properties"]["tags"]["items"]["type"],
            "string"
        );
    }

    #[test]
    fn preserves_descriptions_verbatim() {
        let mut tool = function_tool("f", serde_json::json!({"type": "object"}));
        tool.description = "x".repeat(5000);
        let normalized = normalize_tool_schemas(vec![tool]);
        assert_eq!(normalized[0].description.chars().count(), 5000);
    }
}
