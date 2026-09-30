<script lang="ts">
	// ComfyUI, served by herd itself. The backend proxies /comfyui/ to the
	// fixed local model comfyui_auto: an explicit request for the /comfyui/
	// root starts the model, sub-paths 409 while it is not loaded. This route
	// therefore renders from the model state the /api/events feed reports --
	// the iframe only mounts once the model is ready, and a launch button
	// covers the stopped state. No polling: the feed pushes state changes.
	import { onDestroy, onMount } from "svelte";
	import {
		Workflow,
		ExternalLink,
		Loader2,
		CircleAlert,
		Play,
		PowerOff,
	} from "@lucide/svelte";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import * as Card from "$lib/components/ui/card/index.js";
	import { models, unloadSingleModel } from "../stores/api";
	import { connectionState } from "../stores/theme";
	import { formatUptime } from "$lib/format";
	import {
		COMFYUI_MODEL_ID,
		comfyuiUrl,
		findComfyUIModel,
		comfyuiPhase,
		comfyuiPhaseLabel,
		type ComfyUIPhase,
	} from "$lib/comfyui";

	const url = comfyuiUrl();

	const comfyModel = $derived(findComfyUIModel($models));
	const connected = $derived($connectionState === "connected");
	const phase = $derived(comfyuiPhase(comfyModel, connected));

	let launching = $state(false);
	let launchError = $state<string | null>(null);
	let aborter: AbortController | null = null;

	// Uptime ticks on the same 30s cadence the Surfaces tab uses for health.
	let now = $state(Date.now());
	let timer: ReturnType<typeof setInterval> | undefined;
	const uptime = $derived(
		comfyModel?.readyAt === undefined
			? null
			: formatUptime(Math.max(0, now - comfyModel.readyAt)),
	);

	onMount(() => {
		timer = setInterval(() => {
			now = Date.now();
		}, 30_000);
	});

	onDestroy(() => {
		if (timer !== undefined) clearInterval(timer);
		aborter?.abort();
	});

	function dotClass(p: ComfyUIPhase): string {
		if (p === "ready") return "bg-emerald-500";
		if (p === "starting" || p === "stopping") return "bg-amber-500";
		if (p === "disconnected") return "bg-destructive";
		return "bg-muted-foreground/40";
	}

	function badgeVariant(p: ComfyUIPhase): "secondary" | "destructive" | "outline" {
		if (p === "ready") return "secondary";
		if (p === "disconnected") return "destructive";
		return "outline";
	}

	async function launch(): Promise<void> {
		if (launching) return;
		launching = true;
		launchError = null;
		aborter?.abort();
		aborter = new AbortController();
		try {
			// The explicit root request is what starts the model on the
			// backend; the events feed flips the phase to ready when it is
			// up, which mounts the iframe below.
			const res = await fetch(url, { signal: aborter.signal });
			if (!res.ok) throw new Error(`herd answered ${res.status}`);
			// Drain the body so a slow proxy start does not leave the
			// connection hanging; UI state comes from the events feed.
			await res.arrayBuffer();
		} catch (e) {
			if (e instanceof DOMException && e.name === "AbortError") return;
			launchError = e instanceof Error ? e.message : String(e);
		} finally {
			launching = false;
		}
	}

	async function unload(): Promise<void> {
		launchError = null;
		try {
			await unloadSingleModel(COMFYUI_MODEL_ID);
		} catch (e) {
			launchError = e instanceof Error ? e.message : String(e);
		}
	}
</script>

<div class="flex h-full flex-col gap-4">
	<div class="flex items-center justify-between gap-4">
		<div>
			<h1 class="text-lg font-semibold">ComfyUI</h1>
			<p class="text-muted-foreground text-sm">
				Node-graph image generation, served through herd.
			</p>
		</div>
		<div class="flex items-center gap-2">
			<Badge variant={badgeVariant(phase)}>
				<span class="size-2 rounded-full {dotClass(phase)}"></span>
				{comfyuiPhaseLabel(phase)}
			</Badge>
			{#if phase === "ready"}
				<a
					href={url}
					target="_blank"
					rel="noreferrer noopener"
					class="text-muted-foreground hover:text-foreground inline-flex size-7 items-center justify-center"
					title="Open ComfyUI in a new tab"
				>
					<ExternalLink class="size-4" />
				</a>
			{/if}
		</div>
	</div>

	{#if phase === "ready"}
		<Card.Root class="flex min-h-0 flex-1 flex-col overflow-hidden py-0">
			<Card.Content class="min-h-0 flex-1 p-0">
				<iframe
					src={url}
					title="ComfyUI"
					class="size-full border-0"
					referrerpolicy="no-referrer"
					allow="clipboard-read; clipboard-write"
				></iframe>
			</Card.Content>
			<div
				class="text-muted-foreground flex items-center gap-3 border-t px-4 py-2 text-xs"
			>
				<span class="font-mono">{COMFYUI_MODEL_ID}</span>
				{#if uptime}
					<span>up {uptime}</span>
				{/if}
				{#if launchError}
					<span class="text-destructive">{launchError}</span>
				{/if}
				<span class="ml-auto"></span>
				<Button variant="outline" size="sm" onclick={() => void unload()}>
					<PowerOff />
					Unload
				</Button>
			</div>
		</Card.Root>
	{:else}
		<Card.Root class="flex min-h-0 flex-1 items-center justify-center py-0">
			<Card.Content class="flex max-w-md flex-col items-center gap-3 p-8 text-center">
				{#if phase === "disconnected"}
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<CircleAlert class="text-destructive size-7" />
					</span>
					<h2 class="text-base font-semibold">Cannot reach herd</h2>
					<p class="text-muted-foreground text-sm">
						The backend is unreachable, so ComfyUI state is unknown. Check
						the connection indicator in the sidebar.
					</p>
				{:else if phase === "unconfigured"}
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<Workflow class="text-muted-foreground size-7" />
					</span>
					<h2 class="text-base font-semibold">ComfyUI is not configured</h2>
					<p class="text-muted-foreground text-sm">
						This herd instance has no <span class="font-mono">{COMFYUI_MODEL_ID}</span>
						model configured. Add one to the herd config to enable this tab.
					</p>
				{:else if phase === "starting"}
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<Loader2 class="size-7 animate-spin" />
					</span>
					<h2 class="text-base font-semibold">ComfyUI is starting</h2>
					<p class="text-muted-foreground text-sm">
						The <span class="font-mono">{COMFYUI_MODEL_ID}</span> model is
						loading. The interface appears here automatically when it is ready.
					</p>
				{:else if phase === "stopping"}
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<Loader2 class="size-7 animate-spin" />
					</span>
					<h2 class="text-base font-semibold">ComfyUI is stopping</h2>
					<p class="text-muted-foreground text-sm">
						The <span class="font-mono">{COMFYUI_MODEL_ID}</span> model is
						unloading.
					</p>
				{:else}
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<Workflow class="text-muted-foreground size-7" />
					</span>
					<h2 class="text-base font-semibold">ComfyUI is not running</h2>
					<p class="text-muted-foreground text-sm">
						Start the <span class="font-mono">{COMFYUI_MODEL_ID}</span> model
						to open the ComfyUI interface. The first start loads the model and
						can take a while.
					</p>
					<Button onclick={() => void launch()} disabled={launching}>
						{#if launching}
							<Loader2 class="animate-spin" />
							Starting…
						{:else}
							<Play />
							Start ComfyUI
						{/if}
					</Button>
					{#if launchError}
						<p class="text-destructive text-sm">{launchError}</p>
					{/if}
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}
</div>
