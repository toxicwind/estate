/**
 * Transport seam for collab-web.
 *
 * `CollabSocket` (src/lib/socket.ts) is the AES-GCM encrypted-relay transport
 * used with pi-coding-agent collab hosts. This interface captures its public
 * surface structurally, so alternative backends — e.g. the Kimi transport in
 * `./kimi.ts`, which speaks Moonshot's kap-server REST + WebSocket protocol —
 * can drive `GuestClient` without changing any existing collab-web behavior.
 *
 * `CollabSocket` already satisfies this interface; `GuestClient` accepts any
 * implementation through its optional constructor parameter.
 */
import type { GuestFrame, HostFrame, RelayControlMessage } from "@oh-my-pi/pi-wire";

export interface CollabTransport {
	onOpen?: () => void;
	onFrame?: (frame: HostFrame, fromPeer: number) => void;
	onControl?: (msg: RelayControlMessage) => void;
	/** Fires once per terminal close. willReconnect=true for drops that will retry. */
	onClose?: (reason: string, willReconnect: boolean) => void;
	readonly isOpen: boolean;
	connect(): void;
	send(frame: GuestFrame, targetPeer?: number): void;
	close(): void;
}
