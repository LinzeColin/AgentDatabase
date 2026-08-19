const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("skinAPI", {
  list:    () => ipcRenderer.invoke("skins:list"),
  apply:   (id) => ipcRenderer.invoke("skins:apply", id),
  current: () => ipcRenderer.invoke("skins:current"),
});
// HarnessUI 是一套「多变体库」而不是一张固定画面，所以它有自己的一组调用：
// 列出全部角色、读当前模式、挑一张、切换单选/轮播。
contextBridge.exposeInMainWorld("harnessAPI", {
  list:  () => ipcRenderer.invoke("harness:list"),
  state: () => ipcRenderer.invoke("harness:state"),
  pick:  (id) => ipcRenderer.invoke("harness:pick", id),
  mode:  (m) => ipcRenderer.invoke("harness:mode", m),
});
