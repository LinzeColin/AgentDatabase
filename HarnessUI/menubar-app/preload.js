const { contextBridge, ipcRenderer } = require("electron");
contextBridge.exposeInMainWorld("harnessAPI", {
  list:   () => ipcRenderer.invoke("harness:list"),
  state:  () => ipcRenderer.invoke("harness:state"),
  pick:   (id) => ipcRenderer.invoke("harness:pick", id),
  mode:   (m) => ipcRenderer.invoke("harness:mode", m),
  // 增删：隐藏可撤销，删除会真删文件（主进程弹确认框）
  hide:   (id, on) => ipcRenderer.invoke("harness:hide", id, on),
  remove: (id) => ipcRenderer.invoke("harness:delete", id),
  add:    () => ipcRenderer.invoke("harness:import"),
  onChanged: (fn) => ipcRenderer.on("harness:changed", (_e, s) => fn(s)),
});
