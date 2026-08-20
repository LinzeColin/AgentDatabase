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
		// 同一份状态由菜单栏控制器、Kimi 外壳和这里三方共读共写。各存各的必然分叉 ——
		// 菜单栏切到 A、这边还显示 B，用户看到的和菜单说的对不上。
		const STATE_URL = "http://127.0.0.1:3099/state.json";
		const SYNC_MS = 15000;
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
		function newCycle(entries, hidden) {
			const skip = new Set(hidden || []);
			const ids = entries.filter((entry) => !skip.has(entry.id)).map((entry) => entry.id);
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
/* 背板直接画在根容器上，不用 body::before。
   z-index:-1 的伪元素要能看见，得 html、body 和每一层祖先都不挡它 —— 实测在 DSH
   里挡住了：面板、缩略图、切换全都工作，窗口里却是一片空白默认界面。
   鲸鱼娘皮肤（在这个宿主上一直好用）就是直接画在 [id=root] 上的，照它来。 */
body[data-dsh-harness-ui],
html:has(body[data-dsh-harness-ui]) { background: transparent !important; }

body[data-dsh-harness-ui] [id=root],
body[data-dsh-harness-ui] #app {
  background-image: var(--harness-bg, none) !important;
  background-size: cover !important;
  background-position: center center !important;
  background-repeat: no-repeat !important;
  background-color: var(--harness-fallback, #0d1117) !important;
}
/* 根容器之下的不透明底全部清掉，否则它们把背板整个盖住。
   实测：挡住的是 DIV.pI_x6G_frame（铺满窗口的纯白层），但那是编译出来的哈希类名，
   DSH 每次构建都会变，写死它等于埋定时炸弹；而只清三层结构又清不干净——
   把全部后代清空、再按"这个元素承不承载文字"把底加回去，才是不依赖类名的做法。 */
body[data-dsh-harness-ui] [id=root] * { background-color: transparent !important; }

/* 加回来的只有真正需要底色才读得清的：输入框、弹窗、菜单、下拉。
   用半透明而不是纯色，背板仍然透得出来——这也是参照皮肤的做法。 */
body[data-dsh-harness-ui] [id=root] :is(input, textarea, select),
body[data-dsh-harness-ui] [id=root] :is([role=dialog], [role=menu], [role=listbox], [role=tooltip]),
body[data-dsh-harness-ui] [id=root] :is(pre, code) {
  background-color: rgba(255, 255, 255, .82) !important;
}
body[data-dsh-harness-ui][data-ds-dark-theme] [id=root] :is(input, textarea, select),
body[data-dsh-harness-ui][data-ds-dark-theme] [id=root] :is([role=dialog], [role=menu], [role=listbox], [role=tooltip]),
body[data-dsh-harness-ui][data-ds-dark-theme] [id=root] :is(pre, code) {
  background-color: rgba(16, 22, 36, .80) !important;
}

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
`;
			return style;
		}

		function apply(ctx) {
			const state = loadState();
			let catalog = null;
			let timer = null;
			let syncTimer = null;

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
					report("image-failed", { url: url.slice(0, 120) });
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
					state.cycle = newCycle(catalog.entries, state.hidden);
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

			/** 跟随共享状态。菜单栏控制器负责推进轮播，这边只管把结果画出来，
			 *  所以两处不会各转各的，也不会因为时钟差半分钟而显示不同的角色。 */
			let syncSeen = 0;
			async function syncShared() {
				try {
					const shared = await (await fetch(STATE_URL, { cache: "no-store" })).json();
					if (!shared.updated || shared.updated === syncSeen) return;
					syncSeen = shared.updated;
					state.mode = shared.mode;
					state.intervalMs = shared.intervalMs;
					// 增删由菜单栏控制器做，这边跟着走 —— 隐藏的不显示也不轮到
					const before = (state.hidden || []).join();
					state.hidden = shared.hidden || [];
					if (state.hidden.join() !== before) { state.cycle = []; state.cursor = 0; renderGrid(); }
					if (shared.selected && shared.selected !== state.selected) {
						state.selected = shared.selected;
						saveState(state);
						if (await show(byId(shared.selected))) paintActive();
					}
					paintMode();
				} catch { /* 控制器没开就按本地状态自转，不报错刷屏 */ }
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
  <input data-hu="search" type="search" placeholder="搜中文/英文…" size="12" />
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
				const skip = new Set(state.hidden || []);
				const shown = (catalog?.entries || []).filter((entry) =>
					!skip.has(entry.id) &&
					(!game || entry.game === game) &&
					(!term || entry.character.includes(term) || entry.variant.includes(term)
					 || (entry.label || "").includes(term)));
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
					image.alt = entry.label || entry.character;
					const caption = document.createElement("figcaption");
					const shown = entry.label || entry.character;
					caption.textContent = entry.variant === "default" ? shown : `${shown} · ${entry.variant}`;
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

			/** 把自己的状态回报给素材服务。宿主是打包应用，从外面查不了它的 DOM。 */
			const report = (stage, extra) => {
				try {
					fetch("http://127.0.0.1:3099/__diag", { method: "POST", mode: "no-cors",
						body: JSON.stringify({ stage, ...extra }) });
				} catch { /* 诊断失败不该影响皮肤本身 */ }
			};

			(async () => {
				report("boot", { href: location.href, scoped: document.body.hasAttribute("data-dsh-harness-ui") });
				try {
					const response = await fetch(CATALOG_URL, { cache: "no-store" });
					catalog = await response.json();
					report("catalog", { count: catalog?.entries?.length ?? null });
				} catch (error) {
					status("素材服务未启动");
					report("catalog-failed", { error: String(error).slice(0, 160) });
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
				await syncShared();
				if (state.selected) await show(byId(state.selected));
				else await rotate(true);
				schedule();
				syncTimer = setInterval(syncShared, SYNC_MS);
				report("ready", {
					cards: panel.querySelectorAll(".hu-card").length,
					bg: root.style.getPropertyValue("--harness-bg").slice(0, 90),
					mode: state.mode, selected: state.selected,
				});
			})();

			// Day/night is the host's decision; follow it without re-fetching the
			// catalogue, so a theme flip only re-decodes one image.
			const observer = new MutationObserver(() => { show(byId(state.selected)); });
			observer.observe(document.body, { attributes: true, attributeFilter: ["data-ds-dark-theme"] });

			return () => {
				if (timer) clearInterval(timer);
				if (syncTimer) clearInterval(syncTimer);
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
