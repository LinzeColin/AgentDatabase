# Output A

你这段代码没有贴出来，我无法直接定位泄漏点，先给你最常见的几种原因清单。一是全局或模块级变量长期持有本该释放的对象；二是闭包把不再需要的变量带进了存活期很长的回调里；三是 addEventListener 注册后没有对应 removeEventListener，尤其挂在 window 或 document 上的监听器会一直存活；四是 setInterval 创建后没清除；五是 DOM 引用残留：元素被移除后，数组、对象或闭包里仍保存着它的引用，形成“游离 DOM 树”无法回收；六是无上限的缓存、Map、Set 或日志数组只增不减。排查建议：用 Chrome DevTools 的 Memory 面板做两次 heap snapshot，对比 Retained Size 增长最大的对象，沿引用链找出是谁在持有它。把代码贴出来（尤其监听器、闭包和缓存部分），我可以具体帮你定位。
