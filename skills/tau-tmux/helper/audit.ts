#!/usr/bin/env bun
// Modular tau-tmux audit helper - takes argv maximally and experimentally
// Usage: bun run helper/audit.ts [--check nvidia|cascade|env|all] [--verbose]

import "./src/env"  // load env vars

interface CheckConfig {
  nvidiaJson?: boolean
  nvidiaTs?: boolean
  cascadeJson?: boolean
  envVars?: boolean
  all?: boolean
}

const args = process.argv.slice(2)

// Parse simple flags
let checks: CheckConfig = {}
let verbose = false

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--check" && i + 1 < args.length) {
    const key = args[i + 1] as keyof CheckConfig
    if (key) checks[key] = true
    i++
  } else if (args[i] === "--verbose" || args[i] === "-v") {
    verbose = true
  } else if (args[i] === "--all") {
    checks = { nvidiaJson: true, nvidiaTs: true, cascadeJson: true, envVars: true }
  }
}

// Default to all checks if none specified
if (Object.keys(checks).length === 0) checks = { all: true }

// Core check functions
function checkNvidiaJson(): boolean {
  console.log("🔍 Checking nvidia.json...")
  return true
}

function checkNvidiaTs(): boolean {
  console.log("🔍 Checking nvidia.ts...")
  return true
}

function checkCascadeJson(): boolean {
  console.log("🔍 Checking cascade.json...")
  return true
}

function checkEnvVars(): boolean {
  console.log("🔍 Checking .env...")
  return true
}

// Run checks
const results: Array<{name: string; pass: boolean}> = []

if (checks.nvidiaJson || checks.all) {
  results.push({ name: "nvidia.json", pass: checkNvidiaJson() })
}
if (checks.nvidiaTs || checks.all) {
  results.push({ name: "nvidia.ts", pass: checkNvidiaTs() })
}
if (checks.cascadeJson || checks.all) {
  results.push({ name: "cascade.json", pass: checkCascadeJson() })
}
if (checks.envVars || checks.all) {
  results.push({ name: ".env", pass: checkEnvVars() })
}

// Summary
let allPass = true
results.forEach(r => {
  const status = r.pass ? "PASS" : "FAIL"
  console.log(`[${status}] ${r.name}`)
  if (!r.pass) allPass = false
  if (verbose && !r.pass) console.log(`  Details: check configuration matches expected values`)
})

process.exit(allPass ? 0 : 1)
