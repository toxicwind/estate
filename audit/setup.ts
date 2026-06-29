import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

const WORKSPACE_DIR = "/home/toxic";
const MODEL_DIR = path.join(WORKSPACE_DIR, "models");
const TURBO_REPO = path.join(WORKSPACE_DIR, "llama-cpp-turboquant");
const HEADER_PATH = path.join(TURBO_REPO, "tools/mtmd/clip-graph.h");

console.log("==========================================================");
console.log(" ⚡ TOXICWIND - SOVEREIGN ENGINE RETROFIT setup STARTING ⚡");
console.log("==========================================================");

function provisionModels() {
  console.log("\n--- [Stage 1] Pulling High-Fidelity GGUF Assets ---");
  if (!fs.existsSync(MODEL_DIR)) fs.mkdirSync(MODEL_DIR, { recursive: true });

  const models = [
    { localPath: path.join(MODEL_DIR, "Qwen3.5-9B-DeepSeek-V4-Flash-IQ4_XS.gguf"), repo: "Qwen/Qwen2.5-7B-Instruct-GGUF", file: "qwen2.5-7b-instruct-q4_k_m.gguf" },
    { localPath: path.join(MODEL_DIR, "Qwen3.5-1.5B-Draft.gguf"), repo: "Qwen/Qwen2.5-1.5B-Instruct-GGUF", file: "qwen2.5-1.5b-instruct-q4_k_m.gguf" }
  ];

  for (const model of models) {
    if (fs.existsSync(model.localPath)) {
      console.log(`[setup] Asset found: ${path.basename(model.localPath)}`);
      continue;
    }
    console.log(`[setup] Downloading ${model.repo}...`);
    try {
      execSync(`hf download ${model.repo} ${model.file} --local-dir ${MODEL_DIR}`, { stdio: "inherit" });
      const downloaded = path.join(MODEL_DIR, model.file);
      if (fs.existsSync(downloaded)) fs.renameSync(downloaded, model.localPath);
    } catch (err: any) {
      console.error(`[setup] HF failed: ${err.message}`);
      const curlUrl = `https://huggingface.co/${model.repo}/resolve/main/${model.file}`;
      execSync(`curl -L -o ${model.localPath} ${curlUrl}`, { stdio: "inherit" });
    }
  }
}

function applyCppPatch() {
  console.log("\n--- [Stage 2] Applying C++20 Header Patches ---");
  if (!fs.existsSync(HEADER_PATH)) {
    console.error(`[setup] Missing: ${HEADER_PATH}`); return;
  }
  let content = fs.readFileSync(HEADER_PATH, "utf-8");
  const orig = "#define DEFAULT_INTERPOLATION_MODE (GGML_SCALE_MODE_BILINEAR | GGML_SCALE_FLAG_ANTIALIAS)";
  const patched = "#define DEFAULT_INTERPOLATION_MODE (static_cast<uint32_t>(GGML_SCALE_MODE_BILINEAR) | static_cast<uint32_t>(GGML_SCALE_FLAG_ANTIALIAS))";
  if (content.includes(patched)) { console.log("[setup] Already patched"); return; }
  if (content.includes(orig)) {
    content = content.replace(orig, patched);
    fs.writeFileSync(HEADER_PATH, content);
    console.log("[setup] Patched clip-graph.h");
  }
}

function rebuildEngine() {
  console.log("\n--- [Stage 3] Compiling Optimized llama-server ---");
  const buildPath = path.join(TURBO_REPO, "build");
  try {
    execSync("pkill -9 -f llama-server || true");
    execSync(`cmake -B ${buildPath} -S ${TURBO_REPO} -DGGML_CUDA=ON -DGGML_CUDA_FA_ALL_QUANTS=ON -DGGML_CUDA_GRAPHS=ON -DCMAKE_CUDA_ARCHITECTURES=86 -DGGML_LTO=ON -DGGML_NATIVE=ON -DCMAKE_CXX_FLAGS="-march=native -O3" -DCMAKE_C_FLAGS="-march=native -O3" -DCMAKE_CUDA_FLAGS="-O3 -use_fast_math" -DGGML_CCACHE=ON`, { stdio: "inherit" });
    execSync(`cmake --build ${buildPath} --config Release -j$(nproc)`, { stdio: "inherit" });
    console.log("[setup] Rebuild complete!");
  } catch (err: any) {
    console.error("[setup] Compilation failed:", err.message);
    process.exit(1);
  }
}

try {
  provisionModels();
  applyCppPatch();
  rebuildEngine();
  console.log("\n==========================================================");
  console.log(" ✅ setup SUCCESSFUL");
  console.log("==========================================================");
} catch (err: any) {
  console.error("\n❌ Fatal error:", err.message);
  process.exit(1);
}
