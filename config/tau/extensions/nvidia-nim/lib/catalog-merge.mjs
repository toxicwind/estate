/** Chat-model filter and additive catalog merge (curated ∪ live IDs). */

export function isLLMModel(id) {
	const lower = String(id ?? "").toLowerCase();
	return (
		!/embed|rerank|asr|tts|whisper|parakeet|conformer|transcribe|voice/i.test(lower) &&
		!/^baai\/bge(?:-|$)/i.test(lower) &&
		!/guard|safety|jailbreak|pii|content-safety/i.test(lower) &&
		!/fuyu|kosmos|deplot|neva|nvclip/i.test(lower) &&
		!/reward|arctic-embed/i.test(lower) &&
		!/boltz|diffdock|genmol|molmim|esm|alphafold|rdfusion/i.test(lower) &&
		!/cuopt|usdcode|usdvalidate/i.test(lower) &&
		!/starcoder|codegemma|recurrentgemma/i.test(lower) &&
		!/riva-translate|nemotron-parse|nemoretriever/i.test(lower) &&
		!/synthetic-video|cosmos-reason|lip-sync|eyecontact/i.test(lower) &&
		!/ising|fourcastnet|vista-3d/i.test(lower) &&
		!/gliner-pii|embed-qa/i.test(lower) &&
		!/nvidia\/llama3-chatqa|granite-.*-code/i.test(lower)
	);
}

/** Live IDs that are chat models and not already in the curated list. */
export function collectLiveStubIds(staticIds, liveIds) {
	const staticSet = new Set(staticIds);
	const stubs = [];
	for (const id of liveIds) {
		if (!id || staticSet.has(id)) continue;
		if (!isLLMModel(id)) continue;
		stubs.push(id);
	}
	return stubs;
}

/** Curated IDs first (including nvidia-router), then new live chat IDs. */
export function mergeCatalogIds(staticIds, liveIds) {
	return [...staticIds, ...collectLiveStubIds(staticIds, liveIds)];
}
