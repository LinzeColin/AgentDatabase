window.__ModuleLoader__.load({
	id: "dsh-harness-ui-skins",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });

		/**
		 * Browser half of the HarnessUI skin: 306 character backdrops, two modes.
		 *
		 * MODE gallery  — a picker grid; the user chooses, the choice sticks.
		 * MODE rotate   — one backdrop per interval (default 4h), drawn without
		 *                 replacement so a full cycle shows every entry exactly
		 *                 once before any repeats.
		 *
		 * Three constraints shaped this file, all of them learned the hard way on
		 * this machine and written down in ~/.dsh/AGENTS.md:
		 *
		 * 1. NO `infinite` CSS ANIMATION, ANYWHERE. A single always-running
		 *    keyframe animation over a full-window backdrop took this app to 111%
		 *    CPU at idle; removing it took it to 2.5%. Transitions that run once
		 *    on a state change are fine — they end.
		 * 2. The artwork is fetched over http from a local file server, because
		 *    the plugin route serves only `client.js` and the renderer blocks
		 *    `file://`. If that server is down the skin must still look
		 *    deliberate, not broken — hence the gradient fallback.
		 * 3. Swapping a backdrop decodes megabytes. Decode FIRST, swap after, or
		 *    the window flashes empty mid-change.
		 */

		const inject = [];

		const SCOPE = "dshHarnessUi";              // body dataset key -> [data-dsh-harness-ui]
		const STORE = "harness-ui.state.v1";
		const CATALOG_URL = "http://127.0.0.1:3099/catalog.json";
		const DEFAULT_INTERVAL_MS = 4 * 60 * 60 * 1000;

		/** Read persisted state, tolerating a corrupt or absent record. */
		function loadState() {
			try {
				const raw = window.localStorage.getItem(STORE);
				if (raw) return JSON.parse(raw);
			} catch (error) {
				console.warn("[harness-ui] 状态读取失败，使用默认值:", error);
			}
			return { mode: "rotate", selected: null, cycle: [], cursor: 0, lastRotate: 0 };
		}

		function saveState(state) {
			try {
				window.localStorage.setItem(STORE, JSON.stringify(state));
			} catch (error) {
				console.warn("[harness-ui] 状态写入失败:", error);
			}
		}

		/**
		 * A fresh no-repeat cycle over every catalogue id.
		 * Fisher-Yates on a copy; the caller persists it so a restart resumes the
		 * same cycle rather than starting a new one and repeating entries.
		 */
		function newCycle(entries) {
			const ids = entries.map((entry) => entry.id);
			for (let i = ids.length - 1; i > 0; i -= 1) {
				const j = Math.floor(Math.random() * (i + 1));
				[ids[i], ids[j]] = [ids[j], ids[i]];
			}
			return ids;
		}

		/** Decoded images the browser will now have in cache. Bounded so a long
		 *  session cannot pin hundreds of decoded bitmaps in memory. */
		const warmed = new Set();

		/** Decode ahead of time so the next swap is a cache hit, not a fetch.
		 *  Measured: a cold swap took ~1000ms, a warmed one ~180ms. */
		function warm(url) {
			if (!url || warmed.has(url)) return;
			if (warmed.size > 24) warmed.clear();
			warmed.add(url);
			const image = new Image();
			image.decoding = "async";
			image.src = url;
		}

		/** Decode before showing. Resolves to the url, or null if it will not load. */
		function preload(url) {
			return new Promise((resolve) => {
				const image = new Image();
				const timer = setTimeout(() => resolve(null), 15000);
				image.onload = () => { clearTimeout(timer); resolve(url); };
				image.onerror = () => { clearTimeout(timer); resolve(null); };
				image.src = url;
			});
		}

		function styleSheet() {
			const style = document.createElement("style");
			style.id = "harness-ui-skin";
			style.textContent = `
body[data-dsh-harness-ui]::before {
  content: ""; position: fixed; inset: 0; z-index: -1;
  background-image: var(--harness-bg, none);
  background-size: cover; background-position: center;
  background-color: var(--harness-fallback, #0d1117);
  /* One-shot on change. Never 'infinite' — see the CPU note at the top. */
  transition: opacity 420ms ease;
  opacity: var(--harness-bg-opacity, 1);
}
body[data-dsh-harness-ui] { background: transparent; }
body[data-dsh-harness-ui]:not([data-ds-dark-theme]) { --harness-fallback: #e8eef7; }
#harness-ui-picker {
  position: fixed; right: 16px; bottom: 56px; width: min(720px, 68vw);
  max-height: 62vh; overflow: auto; z-index: 2147483000;
  background: var(--harness-panel, #101826f2); color: #e8eef7;
  border: 1px solid #ffffff24; border-radius: 14px; padding: 14px;
  box-shadow: 0 24px 64px #00000070; display: none;
  font: 13px/1.5 -apple-system, "PingFang SC", system-ui, sans-serif;
}
#harness-ui-picker[data-open="1"] { display: block; }
#harness-ui-picker .hu-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(148px, 1fr)); gap: 10px;
}
#harness-ui-picker .hu-card {
  border: 1px solid #ffffff1f; border-radius: 9px; overflow: hidden;
  cursor: pointer; background: #0009; transition: border-color 160ms ease;
}
#harness-ui-picker .hu-card:hover,
#harness-ui-picker .hu-card:focus-visible { border-color: #7fb7ff; outline: none; }
#harness-ui-picker .hu-card[data-active="1"] { border-color: #ffd479; }
#harness-ui-picker .hu-card img { display: block; width: 100%; aspect-ratio: 16/9; object-fit: cover; }
#harness-ui-picker .hu-card figcaption { padding: 5px 7px; font-size: 11px; color: #c6d3e8; }
#harness-ui-toggle {
  position: fixed; right: 16px; bottom: 16px; z-index: 2147483000;
  padding: 7px 13px; border-radius: 999px; cursor: pointer;
  background: #101826e6; color: #e8eef7; border: 1px solid #ffffff2b;
  font: 12px/1 -asystem-ui, "PingFang SC", system-ui, sans-serif;
}
#harness-ui-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; flex-wrap: wrap; }
#harness-ui-bar button, #harness-ui-bar select, #harness-ui-bar input {
  background: #0b1220; color: #dce6f7; border: 1px solid #ffffff2b;
  border-radius: 7px; padding: 4px 9px; font-size: 12px;
}
#harness-ui-bar button { cursor: pointer; }
#harness-ui-bar .hu-status { margin-left: auto; color: #93a4c2; font-size: 11px; }
@media (prefers-reduced-motion: reduce) {
  body[data-dsh-harness-ui]::before { transition: none; }
}`;
			return style;
		}

		function apply(ctx) {
			const state = loadState();
			let catalog = null;
			let timer = null;

			const root = document.documentElement;
			document.body.dataset[SCOPE] = "";
			if (!document.getElementById("harness-ui-skin")) {
				document.head.appendChild(styleSheet());
			}

			const isDark = () => document.body.hasAttribute("data-ds-dark-theme");
			const byId = (id) => catalog?.entries.find((entry) => entry.id === id) || null;

			/** Decode, then swap. A failed decode leaves the current backdrop alone. */
			async function show(entry) {
				if (!entry) return false;
				const url = isDark() ? entry.dark : entry.light;
				const ready = await preload(url);
				if (!ready) {
					console.warn("[harness-ui] 素材加载失败，保留当前背景:", url);
					return false;
				}
				root.style.setProperty("--harness-bg", `url("${ready}")`);
				warm(isDark() ? entry.light : entry.dark);
				status(`${entry.gameName} · ${entry.character}${entry.variant === "default" ? "" : " / " + entry.variant}`);
				return true;
			}

			/** Next unseen entry; refills the cycle when it runs dry. */
			async function rotate(force) {
				if (!catalog?.entries.length) return;
				const now = Date.now();
				if (!force && now - (state.lastRotate || 0) < interval()) return;
				if (!state.cycle?.length || state.cursor >= state.cycle.length) {
					state.cycle = newCycle(catalog.entries);
					state.cursor = 0;
				}
				// Walk forward past ids that vanished from the catalogue between runs.
				let entry = null;
				while (state.cursor < state.cycle.length && !entry) {
					entry = byId(state.cycle[state.cursor]);
					state.cursor += 1;
				}
				if (await show(entry)) {
					state.lastRotate = now;
					state.selected = entry.id;
					saveState(state);
					paintActive();
					warmNext();
				}
			}

			/** Warm both themes of whatever comes next, so a swap and a theme flip
			 *  are both instant. Peeks without advancing the cursor. */
			function warmNext() {
				if (!catalog?.entries.length || !state.cycle?.length) return;
				const peek = byId(state.cycle[state.cursor]);
				if (!peek) return;
				warm(peek.light);
				warm(peek.dark);
			}

			function interval() {
				return Number(state.intervalMs) > 0 ? Number(state.intervalMs) : DEFAULT_INTERVAL_MS;
			}

			function schedule() {
				if (timer) clearInterval(timer);
				if (state.mode !== "rotate") return;
				// A minute-granular check, not a 4-hour timeout: a timeout does not
				// survive the window sleeping, and this way a missed slot is picked
				// up on the next tick instead of being skipped entirely.
				timer = setInterval(() => { rotate(false); }, 60 * 1000);
			}

			/* ---------------- picker UI ---------------- */

			const toggle = document.createElement("button");
			toggle.id = "harness-ui-toggle";
			toggle.type = "button";
			toggle.textContent = "皮肤";

			const panel = document.createElement("div");
			panel.id = "harness-ui-picker";
			panel.innerHTML = `
<div id="harness-ui-bar">
  <select data-hu="game"><option value="">全部游戏</option></select>
  <input data-hu="search" type="search" placeholder="搜角色…" size="12" />
  <button type="button" data-hu="mode"></button>
  <button type="button" data-hu="next">下一张</button>
  <select data-hu="interval">
    <option value="3600000">1 小时</option>
    <option value="14400000" selected>4 小时</option>
    <option value="28800000">8 小时</option>
  </select>
  <span class="hu-status"></span>
</div>
<div class="hu-grid"></div>`;

			const statusEl = () => panel.querySelector(".hu-status");
			function status(text) { const el = statusEl(); if (el) el.textContent = text; }

			function paintActive() {
				panel.querySelectorAll(".hu-card").forEach((card) => {
					card.dataset.active = card.dataset.id === state.selected ? "1" : "0";
				});
			}

			function paintMode() {
				const button = panel.querySelector('[data-hu="mode"]');
				button.textContent = state.mode === "rotate" ? "模式：轮播" : "模式：手动";
			}

			function renderGrid() {
				const grid = panel.querySelector(".hu-grid");
				const game = panel.querySelector('[data-hu="game"]').value;
				const term = panel.querySelector('[data-hu="search"]').value.trim().toLowerCase();
				const shown = (catalog?.entries || []).filter((entry) =>
					(!game || entry.game === game) &&
					(!term || entry.character.includes(term) || entry.variant.includes(term)));
				grid.textContent = "";
				const fragment = document.createDocumentFragment();
				for (const entry of shown) {
					const card = document.createElement("figure");
					card.className = "hu-card";
					card.tabIndex = 0;
					card.dataset.id = entry.id;
					card.dataset.active = entry.id === state.selected ? "1" : "0";
					const image = document.createElement("img");
					image.loading = "lazy";
					image.src = entry.thumb;
					image.alt = entry.character;
					const caption = document.createElement("figcaption");
					caption.textContent = entry.variant === "default"
						? entry.character : `${entry.character} · ${entry.variant}`;
					card.append(image, caption);
					const pick = async () => {
						// Picking is an explicit choice, so it also leaves rotate mode —
						// otherwise the next tick would overwrite what was just chosen.
						state.mode = "gallery";
						state.selected = entry.id;
						saveState(state);
						paintMode();
						if (await show(entry)) paintActive();
					};
					card.addEventListener("click", pick);
					card.addEventListener("keydown", (event) => {
						if (event.key === "Enter" || event.key === " ") { event.preventDefault(); pick(); }
					});
					fragment.appendChild(card);
				}
				grid.appendChild(fragment);
				status(`${shown.length} / ${catalog?.entries.length || 0}`);
			}

			panel.querySelector('[data-hu="mode"]').addEventListener("click", () => {
				state.mode = state.mode === "rotate" ? "gallery" : "rotate";
				saveState(state);
				paintMode();
				schedule();
				if (state.mode === "rotate") rotate(true);
			});
			panel.querySelector('[data-hu="next"]').addEventListener("click", () => rotate(true));
			panel.querySelector('[data-hu="interval"]').addEventListener("change", (event) => {
				state.intervalMs = Number(event.target.value);
				saveState(state);
				schedule();
			});
			panel.querySelector('[data-hu="game"]').addEventListener("change", renderGrid);
			panel.querySelector('[data-hu="search"]').addEventListener("input", renderGrid);
			toggle.addEventListener("click", () => {
				panel.dataset.open = panel.dataset.open === "1" ? "0" : "1";
			});

			document.body.append(toggle, panel);

			/* ---------------- boot ---------------- */

			(async () => {
				try {
					const response = await fetch(CATALOG_URL, { cache: "no-store" });
					catalog = await response.json();
				} catch (error) {
					status("素材服务未启动");
					console.warn("[harness-ui] 目录拉取失败：", error);
					return;
				}
				const games = [...new Set(catalog.entries.map((entry) => entry.game))];
				const select = panel.querySelector('[data-hu="game"]');
				for (const game of games) {
					const option = document.createElement("option");
					option.value = game;
					option.textContent = catalog.entries.find((e) => e.game === game).gameName;
					select.appendChild(option);
				}
				panel.querySelector('[data-hu="interval"]').value = String(interval());
				paintMode();
				renderGrid();
				if (state.selected && state.mode === "gallery") await show(byId(state.selected));
				else await rotate(true);
				schedule();
			})();

			// Day/night is the host's decision; follow it without re-fetching the
			// catalogue, so a theme flip only re-decodes one image.
			const observer = new MutationObserver(() => { show(byId(state.selected)); });
			observer.observe(document.body, { attributes: true, attributeFilter: ["data-ds-dark-theme"] });

			return () => {
				if (timer) clearInterval(timer);
				observer.disconnect();
				toggle.remove();
				panel.remove();
				document.getElementById("harness-ui-skin")?.remove();
				delete document.body.dataset[SCOPE];
				root.style.removeProperty("--harness-bg");
			};
		}

		exports.apply = apply;
		exports.inject = inject;
		return module.exports;
	}
});
