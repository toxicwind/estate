<script lang="ts">
	// ComfyUI, served by herd itself. The backend proxies /comfyui/ to the
	// fixed local model comfyui_auto: an explicit request for the /comfyui/
	// root starts the model, sub-paths 409 while it is not loaded. This route
	// therefore renders from the model state the /api/events feed reports --
	// the iframe only mounts once the model is ready, and a launch button
	// covers the stopped state. No polling: the feed pushes state changes.
	//
	// The launch request is retried with backoff (immediate, 2s, 8s) because
	// herd can be mid-start when it is first hit; and the mounted iframe is
	// guarded by a 15s load timer -- a model can report "ready" while ComfyUI
	// itself is unreachable behind the proxy, which must show an error card
	// rather than a blank page.
	import { onDestroy, onMount } from "svelte";
	import {
		Workflow,
		ExternalLink,
		Loader2,
		CircleAlert,
		Play,
		PowerOff,
		RotateCcw,
	} from "@lucide/svelte";
	import { Badge } from "$lib/components/ui/badge/index.js";
	import { Button } from "$lib/components/ui/button/index.js";
	import * as Card from "$lib/components/ui/card/index.js";
	import { models, unloadSingleModel } from "../stores/api";
	import { connectionState } from "../stores/theme";
	import { formatUptime } from "$lib/format";
	import {
		COMFYUI_MODEL_ID,
		COMFYUI_LAUNCH_RETRY_DELAYS_MS,
		comfyuiUrl,
		findComfyUIModel,
		comfyuiPhase,
		comfyuiPhaseLabel,
		launchWithRetry,
		type ComfyUIPhase,
	} from "$lib/comfyui";

	const url = comfyuiUrl();

	const comfyModel = $derived(findComfyUIModel($models));
	const connected = $derived($connectionState === "connected");
	const phase = $derived(comfyuiPhase(comfyModel, connected));

	let launching = $state(false);
	let launchAttempt = $state(1);
	let launchError = $state<string | null>(null);
	let aborter: AbortController | null = null;

	// Iframe load guard: if the iframe has not loaded within 15s of mounting
	// (or it errors), swap it for an error card with a retry instead of
	// leaving a blank page. Remounting via iframeKey re-arms the timer.
	let iframeError = $state(false);
	let iframeKey = $state(0);
	let loadTimer: ReturnType<typeof setTimeout> | undefined;

	function clearIframeLoadTimer(): void {
		if (loadTimer !== undefined) {
			clearTimeout(loadTimer);
			loadTimer = undefined;
		}
	}

	function armIframeLoadTimer(): void {
		clearIframeLoadTimer();
		iframeError = false;
		loadTimer = setTimeout(() => {
			iframeError = true;
		}, 15_000);
	}

	function onIframeLoad(): void {
		clearIframeLoadTimer();
	}

	function onIframeError(): void {
		clearIframeLoadTimer();
		iframeError = true;
	}

	function retryIframe(): void {
		iframeKey += 1; // remounts the iframe via {#key}
		armIframeLoadTimer();
	}

	// Uptime ticks on the same 30s cadence the Surfaces tab uses for health.
	let now = $state(Date.now());
	let timer: ReturnType<typeof setInterval> | undefined;
	const uptime = $derived(
		comfyModel?.readyAt === undefined
			? null
			: formatUptime(Math.max(0, now - comfyModel.readyAt)),
	);

	$effect(() => {
		if (phase === "ready") {
			armIframeLoadTimer();
		} else {
			clearIframeLoadTimer();
			iframeError = false;
		}
	});

	onMount(() => {
		timer = setInterval(() => {
			now = Date.now();
		}, 30_000);
	});

	onDestroy(() => {
		if (timer !== undefined) clearInterval(timer);
		clearIframeLoadTimer();
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
		launchAttempt = 1;
		launchError = null;
		aborter?.abort();
		aborter = new AbortController();
		try {
			// The explicit root request is what starts the model on the
			// backend; the events feed flips the phase to ready when it is
			// up, which mounts the iframe below. Retried with backoff so a
			// slow herd start does not surface as a one-shot failure.
			await launchWithRetry(
				fetch,
				url,
				aborter.signal,
				COMFYUI_LAUNCH_RETRY_DELAYS_MS,
				(attempt) => {
					launchAttempt = attempt;
				},
			);
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
		{#if iframeError}
			<Card.Root class="flex min-h-0 flex-1 items-center justify-center py-0">
				<Card.Content class="flex max-w-md flex-col items-center gap-3 p-8 text-center">
					<span
						class="bg-muted flex size-14 items-center justify-center rounded-full"
					>
						<CircleAlert class="text-destructive size-7" />
					</span>
					<h2 class="text-base font-semibold">ComfyUI is not responding</h2>
					<p class="text-muted-foreground text-sm">
						The model reports ready, but the interface did not load from
						<span class="font-mono">{url}</span> within 15 seconds. The backend
						may be unreachable behind the ready state.
					</p>
					<Button onclick={() => retryIframe()}>
						<RotateCcw class="size-4" />
						Retry
					</Button>
				</Card.Content>
			</Card.Root>
		{:else}
			<Card.Root class="flex min-h-0 flex-1 flex-col overflow-hidden py-0">
				<Card.Content class="min-h-0 flex-1 p-0">
					{#key iframeKey}
						<iframe
							src={url}
							title="ComfyUI"
							class="size-full border-0"
							referrerpolicy="no-referrer"
							allow="clipboard-read; clipboard-write"
							onload={onIframeLoad}
							onerror={onIframeError}
						></iframe>
					{/key}
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
		{/if}
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
							{launchAttempt > 1
								? `Retrying… attempt ${launchAttempt}/${COMFYUI_LAUNCH_RETRY_DELAYS_MS.length}`
								: "Starting…"}
						{:else}
							<Play />
							Start ComfyUI
						{/if}
					</Button>
					{#if launchError}
						<div class="flex items-center gap-2">
							<p class="text-destructive text-sm">{launchError}</p>
							<Button variant="outline" size="sm" onclick={() => void launch()}>
								<RotateCcw class="size-3.5" />
								Retry
							</Button>
						</div>
					{/if}
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}
</div>
