#!/usr/bin/env bun
/**
 * arrival-classifier — event-driven classifier for Syncthing incoming/
 * 
 * Watches /mnt/8TB/phone-archive/incoming/ with inotify.
 * When files arrive via Syncthing, classifies and routes:
 *   repos/    <- git checkouts (.git/ present)
 *   archives/ <- zip/tar/gz/7z/apk/rar
 *   code/     <- py/sh/js/ts/go/rs
 *   docs/     <- md/txt/pdf/html (credential-screened)
 * 
 * Photos (DCIM/Pictures patterns) and credential-shaped content are
 * left in incoming/ for manual review — never auto-sorted.
 * 
 * Event-driven, never timers. Uses inotify via bun:ffi or fs.watch.
 */

import { watch } from "fs";
import { join, dirname, basename, extname } from "path";
import { existsSync, mkdirSync, renameSync, statSync, readFileSync } from "fs";
import { $ } from "bun";

const INCOMING = "/mnt/8TB/phone-archive/incoming";
const ARCHIVE = "/mnt/8TB/phone-archive";

const ROUTES: Record<string, string> = {
  ".zip": "archives",
  ".tar": "archives",
  ".gz": "archives",
  ".tgz": "archives",
  ".7z": "archives",
  ".rar": "archives",
  ".apk": "archives",
  ".py": "code",
  ".sh": "code",
  ".js": "code",
  ".ts": "code",
  ".go": "code",
  ".rs": "code",
  ".md": "docs",
  ".txt": "docs",
  ".pdf": "docs",
  ".html": "docs",
  ".json": "docs",
};

// Photos explicitly out of scope — never auto-route
const PHOTO_PATTERNS = [/dcim/i, /pictures/i, /\.(jpg|jpeg|png|gif|webp|heic)$/i, /\.(mp4|mkv|avi|mov)$/i];

// Credential-shaped content — quarantine, don't route
const CREDENTIAL_PATTERNS = [/api[_-]?key/i, /password/i, /secret/i, /token/i, /BEGIN.*PRIVATE KEY/i];

function isPhoto(path: string): boolean {
  return PHOTO_PATTERNS.some(p => p.test(path));
}

function hasCredentials(path: string): boolean {
  try {
    const content = readFileSync(path, "utf-8").slice(0, 10000); // First 10KB
    return CREDENTIAL_PATTERNS.some(p => p.test(content));
  } catch {
    return false; // Binary or unreadable — let MIME handle it
  }
}

function isGitRepo(path: string): boolean {
  try {
    return statSync(path).isDirectory() && existsSync(join(path, ".git"));
  } catch {
    return false;
  }
}

async function getMimeType(path: string): Promise<string> {
  try {
    const result = await $`file -b --mime-type ${path}`.text();
    return result.trim();
  } catch {
    return "unknown";
  }
}

async function classifyAndRoute(filePath: string): Promise<void> {
  const name = basename(filePath);
  
  // Skip hidden/temp files
  if (name.startsWith(".") || name.endsWith("~") || name.endsWith(".tmp")) {
    return;
  }
  
  // Photos stay — never auto-route
  if (isPhoto(filePath)) {
    console.log(`PHOTO-SKIP: ${name} (left in incoming/)`);
    return;
  }
  
  // Git repos go to repos/
  if (isGitRepo(filePath)) {
    const dest = join(ARCHIVE, "repos", name);
    mkdirSync(dirname(dest), { recursive: true });
    renameSync(filePath, dest);
    console.log(`ROUTED repos/: ${name}`);
    return;
  }
  
  // Check extension
  const ext = extname(name).toLowerCase();
  const route = ROUTES[ext];
  
  if (route) {
    // Credential screen for docs
    if (route === "docs" && hasCredentials(filePath)) {
      console.log(`CREDENTIAL-QUARANTINE: ${name} (left in incoming/)`);
      return;
    }
    
    const dest = join(ARCHIVE, route, name);
    mkdirSync(dirname(dest), { recursive: true });
    
    // Avoid collisions
    let finalDest = dest;
    let counter = 1;
    while (existsSync(finalDest)) {
      const base = basename(name, ext);
      finalDest = join(ARCHIVE, route, `${base}-${counter}${ext}`);
      counter++;
    }
    
    renameSync(filePath, finalDest);
    console.log(`ROUTED ${route}/: ${name}`);
    return;
  }
  
  // MIME fallback for extensionless files
  const mime = await getMimeType(filePath);
  let mimeRoute: string | null = null;
  
  if (mime.startsWith("application/zip") || mime.includes("tar") || mime.includes("gzip")) {
    mimeRoute = "archives";
  } else if (mime.startsWith("text/x-python") || mime.startsWith("text/x-shellscript")) {
    mimeRoute = "code";
  } else if (mime.startsWith("text/")) {
    if (hasCredentials(filePath)) {
      console.log(`CREDENTIAL-QUARANTINE: ${name} (left in incoming/)`);
      return;
    }
    mimeRoute = "docs";
  }
  
  if (mimeRoute) {
    const dest = join(ARCHIVE, mimeRoute, name);
    mkdirSync(dirname(dest), { recursive: true });
    renameSync(filePath, dest);
    console.log(`ROUTED ${mimeRoute}/ (mime:${mime}): ${name}`);
  } else {
    console.log(`UNCLASSIFIED: ${name} (mime:${mime}, left in incoming/)`);
  }
}

function main() {
  if (!existsSync(INCOMING)) {
    mkdirSync(INCOMING, { recursive: true });
  }
  
  console.log(`Watching ${INCOMING} for arrivals...`);
  
  // Debounce: wait for file to settle before classifying
  const pending = new Map<string, Timer>();
  
  const watcher = watch(INCOMING, { recursive: true }, (eventType, filename) => {
    if (!filename) return;
    
    const fullPath = join(INCOMING, filename);
    
    // Clear existing timer
    const existing = pending.get(fullPath);
    if (existing) clearTimeout(existing);
    
    // Debounce 5s — wait for Syncthing to finish writing
    const timer = setTimeout(async () => {
      pending.delete(fullPath);
      if (existsSync(fullPath)) {
        try {
          await classifyAndRoute(fullPath);
        } catch (e) {
          console.error(`Failed to classify ${filename}: ${e}`);
        }
      }
    }, 5000);
    
    pending.set(fullPath, timer);
  });
  
  // Handle shutdown
  process.on("SIGINT", () => {
    console.log("\nShutting down classifier...");
    watcher.close();
    process.exit(0);
  });
  
  process.on("SIGTERM", () => {
    watcher.close();
    process.exit(0);
  });
}

main();
