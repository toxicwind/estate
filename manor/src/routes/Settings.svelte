<script lang="ts">
  import { onMount } from "svelte";
  import { connectionState, themeName, themeMode, themes, type ThemeMode } from "../stores/theme";
  import { versionInfo } from "../stores/api";
  import { showCapabilityTags } from "../stores/modelDisplay";
  import { showGenerationStats } from "../stores/generationStats";
  import * as Select from "$lib/components/ui/select/index.js";
  import * as Switch from "$lib/components/ui/switch/index.js";
  import * as Label from "$lib/components/ui/label/index.js";
  import * as ToggleGroup from "$lib/components/ui/toggle-group/index.js";
  import { Input } from "$lib/components/ui/input/index.js";
  import { Button } from "$lib/components/ui/button/index.js";
  import { copyText } from "$lib/clipboard";
  import { Copy, Check, RefreshCw, Plus, X } from "@lucide/svelte";
  import {
    defaultCorsConfig,
    KNOWN_HTTP_METHODS,
    validateCorsConfig,
    corsConfigToYaml,
    probeCorsPolicy,
    describeEffectivePolicy,
    type CorsConfig,
    type CorsProbeResult,
  } from "$lib/cors";

  const modes: { value: ThemeMode; label: string }[] = [
    { value: "light", label: "Light" },
    { value: "dark", label: "Dark" },
    { value: "system", label: "System" },
  ];

  let themeLabel = $derived(themes.find((t) => t.value === $themeName)?.label ?? "Default");
  let modeLabel = $derived(modes.find((m) => m.value === $themeMode)?.label ?? "System");

  // --- CORS policy panel ---
  // herd exposes no config API, so the active security.cors block can neither
  // be read nor written from here. This panel probes the effective policy (a
  // same-origin OPTIONS carries the page's Origin automatically and herd
  // answers with the Access-Control-* headers it would send a browser) and
  // builds the YAML snippet to paste into herd.yaml.
  let corsCfg = $state<CorsConfig>(defaultCorsConfig());
  let maxAgeText = $state("");
  let probe = $state<CorsProbeResult | null>(null);
  let probing = $state(false);
  let copied = $state(false);

  let yamlPreview = $derived(corsConfigToYaml(corsCfg));
  let corsProblems = $derived(validateCorsConfig(corsCfg));

  onMount(() => {
    void runProbe();
  });

  async function runProbe(): Promise<void> {
    probing = true;
    try {
      probe = await probeCorsPolicy();
    } finally {
      probing = false;
    }
  }

  function syncMaxAge(): void {
    const text = maxAgeText.trim();
    corsCfg.maxAge = text === "" ? null : Number(text);
  }

  function addOrigin(): void {
    corsCfg.allowedOrigins = [...corsCfg.allowedOrigins, ""];
  }

  function removeOrigin(index: number): void {
    corsCfg.allowedOrigins = corsCfg.allowedOrigins.filter((_, i) => i !== index);
  }

  function addHeader(list: "allowedHeaders" | "exposedHeaders"): void {
    corsCfg[list] = [...corsCfg[list], ""];
  }

  function removeHeader(list: "allowedHeaders" | "exposedHeaders", index: number): void {
    corsCfg[list] = corsCfg[list].filter((_, i) => i !== index);
  }

  async function copyYaml(): Promise<void> {
    copied = await copyText(yamlPreview);
    if (copied) setTimeout(() => (copied = false), 2000);
  }
</script>

{#snippet probeRow(label: string, value: string | null)}
  <div class="flex justify-between gap-4">
    <dt class="text-muted-foreground">{label}</dt>
    <dd class="font-mono font-medium break-all text-right">{value ?? "—"}</dd>
  </div>
{/snippet}

{#snippet headerList(
  title: string,
  list: "allowedHeaders" | "exposedHeaders",
  description: string,
  placeholder: string,
)}
  <div class="space-y-2">
    <div class="flex items-center justify-between gap-4">
      <div>
        <span class="text-sm">{title}</span>
        <p class="text-muted-foreground text-xs">{description}</p>
      </div>
      <Button variant="outline" size="sm" onclick={() => addHeader(list)}>
        <Plus class="size-3.5" /> Add
      </Button>
    </div>
    {#each corsCfg[list] as _, i (i)}
      <div class="flex gap-2">
        <Input
          bind:value={corsCfg[list][i]}
          {placeholder}
          class="font-mono text-xs"
          aria-label={`${title} ${i + 1}`}
        />
        <Button
          variant="ghost"
          size="sm"
          onclick={() => removeHeader(list, i)}
          aria-label={`Remove ${title} ${i + 1}`}
        >
          <X class="size-3.5" />
        </Button>
      </div>
    {:else}
      <p class="text-muted-foreground text-xs">Empty — herd default applies.</p>
    {/each}
  </div>
{/snippet}

<div class="p-2">
  <div class="mt-4 mb-4">
    <h3 class="text-lg font-semibold">Settings</h3>
  </div>

  <div class="rounded-lg border p-4 space-y-3 max-w-md mb-4">
    <h4 class="text-sm font-semibold text-muted-foreground">Appearance</h4>
    <div class="flex items-center justify-between gap-4">
      <span class="text-sm">Theme</span>
      <Select.Root
        type="single"
        value={$themeName}
        onValueChange={(v) => v && themeName.set(v as typeof $themeName)}
      >
        <Select.Trigger class="w-40">{themeLabel}</Select.Trigger>
        <Select.Content>
          {#each themes as theme (theme.value)}
            <Select.Item value={theme.value}>{theme.label}</Select.Item>
          {/each}
        </Select.Content>
      </Select.Root>
    </div>
    <div class="flex items-center justify-between gap-4">
      <span class="text-sm">Mode</span>
      <Select.Root
        type="single"
        value={$themeMode}
        onValueChange={(v) => v && themeMode.set(v as ThemeMode)}
      >
        <Select.Trigger class="w-40">{modeLabel}</Select.Trigger>
        <Select.Content>
          {#each modes as mode (mode.value)}
            <Select.Item value={mode.value}>{mode.label}</Select.Item>
          {/each}
        </Select.Content>
      </Select.Root>
    </div>
  </div>

  <div class="rounded-lg border p-4 space-y-3 max-w-md mb-4">
    <h4 class="text-sm font-semibold text-muted-foreground">Models page</h4>
    <div class="flex items-start justify-between gap-4">
      <div>
        <Label.Root for="show-capability-tags" class="text-sm">Show capability tags</Label.Root>
        <p class="text-muted-foreground text-xs">
          Show all capability badges next to each model, mirroring the Details tab
          (vision, tools, context window, and more).
        </p>
      </div>
      <Switch.Root
        id="show-capability-tags"
        checked={$showCapabilityTags}
        onCheckedChange={(v) => showCapabilityTags.set(v)}
      />
    </div>
  </div>

  <div class="rounded-lg border p-4 space-y-3 max-w-md mb-4">
    <h4 class="text-sm font-semibold text-muted-foreground">Chat</h4>
    <div class="flex items-start justify-between gap-4">
      <div>
        <Label.Root for="show-generation-stats" class="text-sm">Show generation stats</Label.Root>
        <p class="text-muted-foreground text-xs">
          Show tokens, time, and speed for Playground and Docs agent responses.
        </p>
      </div>
      <Switch.Root
        id="show-generation-stats"
        checked={$showGenerationStats}
        onCheckedChange={(v) => showGenerationStats.set(v)}
      />
    </div>
  </div>

  <div class="rounded-lg border p-4 space-y-4 max-w-2xl mb-4">
    <div>
      <h4 class="text-sm font-semibold text-muted-foreground">CORS policy</h4>
      <p class="text-muted-foreground text-xs mt-1">
        herd exposes no config API, so the active policy cannot be edited here.
        Probe the effective policy below, then build the
        <code class="font-mono">security.cors</code> snippet to paste into
        <code class="font-mono">herd.yaml</code>.
      </p>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between gap-4">
        <span class="text-sm font-medium">Effective policy (live probe)</span>
        <Button variant="outline" size="sm" onclick={runProbe} disabled={probing}>
          <RefreshCw class={probing ? "size-3.5 animate-spin" : "size-3.5"} />
          {probing ? "Probing…" : "Re-probe"}
        </Button>
      </div>
      {#if probe}
        <p class="text-xs">
          {describeEffectivePolicy(probe)}
          <span class="text-muted-foreground"> — probed as {probe.probedOrigin}</span>
        </p>
        <dl class="text-xs space-y-1 rounded-md bg-muted/50 p-3">
          {@render probeRow("Access-Control-Allow-Origin", probe.allowOrigin)}
          {@render probeRow("Access-Control-Allow-Credentials", probe.allowCredentials)}
          {@render probeRow("Access-Control-Allow-Methods", probe.allowMethods)}
          {@render probeRow("Access-Control-Allow-Headers", probe.allowHeaders)}
          {@render probeRow("Access-Control-Expose-Headers", probe.exposeHeaders)}
          {@render probeRow("Access-Control-Max-Age", probe.maxAge)}
          {@render probeRow("Access-Control-Allow-Private-Network", probe.allowPrivateNetwork)}
        </dl>
      {:else}
        <p class="text-muted-foreground text-xs">Probing herd…</p>
      {/if}
    </div>

    <div class="border-t pt-4 space-y-4">
      <span class="text-sm font-medium">Policy builder</span>

      <div class="space-y-2">
        <div class="flex items-center justify-between gap-4">
          <div>
            <span class="text-sm">Allowed origins</span>
            <p class="text-muted-foreground text-xs">
              Empty keeps the legacy permissive policy. Use "*" to allow any origin deliberately.
            </p>
          </div>
          <Button variant="outline" size="sm" onclick={addOrigin}>
            <Plus class="size-3.5" /> Add
          </Button>
        </div>
        {#each corsCfg.allowedOrigins as _, i (i)}
          <div class="flex gap-2">
            <Input
              bind:value={corsCfg.allowedOrigins[i]}
              placeholder="https://dashboard.example.com or *"
              class="font-mono text-xs"
              aria-label={`Allowed origin ${i + 1}`}
            />
            <Button
              variant="ghost"
              size="sm"
              onclick={() => removeOrigin(i)}
              aria-label={`Remove allowed origin ${i + 1}`}
            >
              <X class="size-3.5" />
            </Button>
          </div>
        {:else}
          <p class="text-muted-foreground text-xs">
            No origins listed — herd allows any origin (legacy permissive).
          </p>
        {/each}
      </div>

      <div class="flex items-start justify-between gap-4">
        <div>
          <Label.Root for="cors-credentials" class="text-sm">Allow credentials</Label.Root>
          <p class="text-muted-foreground text-xs">
            Send Access-Control-Allow-Credentials so browsers attach cookies and
            Authorization headers. Cannot be combined with a "*" origin.
          </p>
        </div>
        <Switch.Root
          id="cors-credentials"
          checked={corsCfg.allowCredentials}
          onCheckedChange={(v) => (corsCfg.allowCredentials = v)}
        />
      </div>

      <div class="flex items-start justify-between gap-4">
        <div>
          <Label.Root for="cors-private-network" class="text-sm">Allow private network</Label.Root>
          <p class="text-muted-foreground text-xs">
            Answer Chrome's Private Network Access preflight so a page on a public
            origin can reach herd on a private address. Cannot be combined with a "*" origin.
          </p>
        </div>
        <Switch.Root
          id="cors-private-network"
          checked={corsCfg.allowPrivateNetwork}
          onCheckedChange={(v) => (corsCfg.allowPrivateNetwork = v)}
        />
      </div>

      <div class="space-y-2">
        <div>
          <span class="text-sm">Allowed methods</span>
          <p class="text-muted-foreground text-xs">
            Empty advertises herd's default (GET, POST, PUT, PATCH, DELETE, OPTIONS).
          </p>
        </div>
        <ToggleGroup.Root
          type="multiple"
          variant="outline"
          bind:value={corsCfg.allowedMethods}
          class="flex flex-wrap gap-1"
        >
          {#each KNOWN_HTTP_METHODS as method (method)}
            <ToggleGroup.Item value={method} class="text-xs">{method}</ToggleGroup.Item>
          {/each}
        </ToggleGroup.Root>
      </div>

      {@render headerList(
        "Allowed headers",
        "allowedHeaders",
        "Empty echoes the client's Access-Control-Request-Headers, falling back to herd's default.",
        "X-Custom-Header",
      )}

      {@render headerList(
        "Exposed headers",
        "exposedHeaders",
        "Response headers a browser may read beyond the CORS-safelisted set. Empty omits the header.",
        "X-Request-Id",
      )}

      <div class="flex items-center justify-between gap-4">
        <div>
          <Label.Root for="cors-max-age" class="text-sm">Max age (seconds)</Label.Root>
          <p class="text-muted-foreground text-xs">
            Preflight cache lifetime. Empty = herd default (86400).
          </p>
        </div>
        <Input
          id="cors-max-age"
          type="number"
          min="0"
          step="1"
          class="w-32"
          placeholder="86400"
          bind:value={maxAgeText}
          oninput={syncMaxAge}
        />
      </div>

      {#if corsProblems.length > 0}
        <ul class="text-xs text-destructive space-y-1">
          {#each corsProblems as problem (problem)}
            <li>⚠ {problem}</li>
          {/each}
        </ul>
      {/if}

      <div class="space-y-2">
        <div class="flex items-center justify-between gap-4">
          <span class="text-sm font-medium">herd.yaml snippet</span>
          <Button variant="outline" size="sm" onclick={copyYaml} disabled={corsProblems.length > 0}>
            {#if copied}
              <Check class="size-3.5" /> Copied
            {:else}
              <Copy class="size-3.5" /> Copy YAML
            {/if}
          </Button>
        </div>
        <pre
          class="text-xs font-mono bg-muted/50 rounded-md p-3 overflow-x-auto whitespace-pre">{yamlPreview}</pre>
      </div>
    </div>
  </div>

  <div class="rounded-lg border p-4 space-y-2 max-w-md">
    <h4 class="text-sm font-semibold text-muted-foreground">Build Information</h4>
    <dl class="text-sm space-y-1">
      <div class="flex justify-between gap-4">
        <dt class="text-muted-foreground">Event Stream</dt>
        <dd class="font-medium">{$connectionState ?? "unknown"}</dd>
      </div>
      <div class="flex justify-between gap-4">
        <dt class="text-muted-foreground">Version</dt>
        <dd class="font-medium">{$versionInfo?.version ?? "unknown"}</dd>
      </div>
      <div class="flex justify-between gap-4">
        <dt class="text-muted-foreground">Commit Hash</dt>
        <dd class="font-medium">{$versionInfo?.commit?.substring(0, 7) ?? "unknown"}</dd>
      </div>
      <div class="flex justify-between gap-4">
        <dt class="text-muted-foreground">Build Date</dt>
        <dd class="font-medium">{$versionInfo?.build_date ?? "unknown"}</dd>
      </div>
    </dl>
  </div>
</div>
