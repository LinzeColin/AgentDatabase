const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("harnessAPI", {
  list:  () => ipcRenderer.invoke("harness:list"),
  state: () => ipcRenderer.invoke("harness:state"),
  pick:  (id) => ipcRenderer.invoke("harness:pick", id),
  mode:  (m) => ipcRenderer.invoke("harness:mode", m),
  onChanged: (fn) => ipcRenderer.on("harness:changed", (_e, s) => fn(s)),
});
