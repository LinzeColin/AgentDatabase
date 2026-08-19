/**
 * Host half of the HarnessUI skin.
 *
 * Deliberately almost empty. The artwork is 612 files and several gigabytes,
 * and this build serves exactly one file per plugin — `/plugins/<pkg>/client.js`
 * — with no static asset route behind it (probed: `preview/light.webp`,
 * `package.json` and every other path under a mounted plugin return 404, while
 * `client.js` returns 200). The reference Deep Whale skin inlines its artwork as
 * data URIs for that reason; at this library's size that would mean a
 * multi-gigabyte bundle, so the images are served by a small local file server
 * instead and the browser half fetches them over http. `file://` is blocked from
 * the renderer, http on 127.0.0.1 is not — both measured against the live UI.
 *
 * Nothing here needs the host, so this row only announces itself.
 */

const name = "dsh-harness-ui-skins";
const inject = [];

function apply(ctx) {
  ctx.logger?.("harness-ui")?.info?.("HarnessUI 皮肤已挂载（素材走本地资源服务）");
}

export { apply, inject, name };
