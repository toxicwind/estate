import { createApiKeyLogin } from "./api-key-login";
import type { OAuthController, OAuthLoginCallbacks } from "./oauth/types";
import type { ProviderDefinition } from "./types";

const AUTH_URL = "https://developers.cloudflare.com/ai-gateway/configuration/authentication/";

/**
 * Login to Cloudflare AI Gateway.
 *
 * Opens browser to Cloudflare AI Gateway authentication docs and prompts for a gateway token/API key.
 * Returns the API key directly (not OAuthCredentials - this isn't OAuth).
 */
export const loginCloudflareAiGateway = createApiKeyLogin({
	providerLabel: "Cloudflare AI Gateway",
	authUrl: AUTH_URL,
	instructions: "Copy your Cloudflare AI Gateway token/API key. Configure account/gateway base URL in models config.",
	promptMessage: "Paste your Cloudflare AI Gateway token/API key",
	placeholder: "cf-aig-...",
	validation: null,
});

export const cloudflareAiGatewayProvider = {
	id: "cloudflare-ai-gateway",
	name: "Cloudflare AI Gateway",
	login: (callbacks: OAuthController) => loginCloudflareAiGateway(callbacks as OAuthLoginCallbacks),
} as const satisfies ProviderDefinition;
import { buildModel } from "@oh-my-pi/pi-catalog/build";
import { apiRouteFor } from "@oh-my-pi/pi-catalog/compat/behavior";
import {
	CLOUDFLARE_AI_GATEWAY_ANTHROPIC_BASE_URL,
	CLOUDFLARE_AI_GATEWAY_BASE_URL,
	CLOUDFLARE_AI_GATEWAY_COMPAT_BASE_URL,
	CLOUDFLARE_AI_GATEWAY_OPENAI_BASE_URL,
	parseCloudflareAiGatewayCredential,
} from "@oh-my-pi/pi-catalog/wire/cloudflare-ai-gateway";
import { $env } from "@oh-my-pi/pi-utils";
import { NO_AUTH_SENTINEL } from "../auth-retry";
import * as AIError from "../error";
import type { ProviderTransport } from "./build";

/**
 * Cloudflare AI Gateway model/request shaping.
 * Restored 2026-09-15: dropped by 1900610cf3 (de-submodule rewrite);
 * byte-identical logic to vendor/oh-my-pi mirror.
 */
export const cloudflareAiGatewayTransport: ProviderTransport = {
	prepareModel: model => {
		const hasGatewayPlaceholders = model.baseUrl.includes("<account>") || model.baseUrl.includes("<gateway>");
		const route = apiRouteFor("cloudflare-ai-gateway", model.id);
		if (!route) return model;
		if (route.api === "anthropic-messages") {
			const requestModelId = (route.requestModelId ?? model.id).replaceAll(".", "-");
			const baseUrl = hasGatewayPlaceholders ? CLOUDFLARE_AI_GATEWAY_ANTHROPIC_BASE_URL : model.baseUrl;
			if (
				model.api === "anthropic-messages" &&
				model.baseUrl === baseUrl &&
				model.requestModelId === requestModelId
			) {
				return model;
			}
			return {
				...model,
				api: "anthropic-messages",
				baseUrl,
				requestModelId,
			};
		}
		if (route.api === "openai-completions") {
			const isOpenAIRoute = route.requestModelId !== undefined;
			const baseUrl = hasGatewayPlaceholders
				? isOpenAIRoute
					? CLOUDFLARE_AI_GATEWAY_OPENAI_BASE_URL
					: CLOUDFLARE_AI_GATEWAY_COMPAT_BASE_URL
				: model.baseUrl;
			if (
				model.api === "openai-completions" &&
				model.baseUrl === baseUrl &&
				model.requestModelId === route.requestModelId
			) {
				return model;
			}
			return buildModel({
				...model,
				api: "openai-completions",
				baseUrl,
				compat: model.compatConfig,
				...(route.requestModelId !== undefined ? { requestModelId: route.requestModelId } : {}),
			});
		}
		return model;
	},
	prepareRequest: (model, options) => {
		const credential = parseCloudflareAiGatewayCredential(options.apiKey ?? $env.CLOUDFLARE_AI_GATEWAY_API_KEY ?? "");
		if (!credential) return { model, options };
		const accountId = credential.accountId ?? $env.CLOUDFLARE_ACCOUNT_ID;
		const gatewayId = credential.gatewayId ?? $env.CLOUDFLARE_GATEWAY_ID;
		let baseUrl = model.baseUrl;
		if (baseUrl.startsWith(CLOUDFLARE_AI_GATEWAY_BASE_URL)) {
			if (!accountId) throw new AIError.ConfigurationError("Cloudflare account ID is required");
			if (!gatewayId) throw new AIError.ConfigurationError("Cloudflare AI Gateway ID is required");
			baseUrl = baseUrl.replace("<account>", accountId).replace("<gateway>", gatewayId);
		}

		const isAnthropic = model.api === "anthropic-messages";
		let headers = model.headers;
		if (!isAnthropic) {
			headers = { ...headers };
			for (const name in headers) {
				const normalized = name.toLowerCase();
				if (normalized === "authorization" || normalized === "x-api-key") delete headers[name];
			}
			headers["cf-aig-authorization"] = `Bearer ${credential.token}`;
		}
		return {
			model: { ...model, baseUrl, headers },
			options: { ...options, apiKey: isAnthropic ? credential.token : NO_AUTH_SENTINEL },
		};
	},
};
