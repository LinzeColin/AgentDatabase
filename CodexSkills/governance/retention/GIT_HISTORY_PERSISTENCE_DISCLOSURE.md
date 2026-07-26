# Git-history persistence disclosure / Git 历史持久性披露

Status: **DRAFT_NON_ACTIVE**

## Operator disclosure / 操作方披露

The 365-day rule governs full-fidelity artifacts in the Git current tree only. After the strict boundary, an eligible shard may be removed from a later current tree, while Git history, forks, clones, caches, archives, and provider backups can retain the bytes indefinitely.

365 天规则只约束 Git 当前树中的全保真工件。严格超过边界后，符合条件的 shard 可以从后续当前树移除，但 Git 历史、fork、clone、cache、archive 和服务商备份仍可能无限期保留这些字节。

## User disclosure / 用户披露

A retention receipt proves only the audited current-tree transition. It does not prove permanent deletion, removal from Git history or other copies, or irrecoverability.

retention receipt 只证明经审计的当前树转换；它不证明永久删除、不证明已从 Git 历史或其他副本移除，也不证明数据不可恢复。

## Hard-erasure boundary / 硬擦除边界

This mechanism never claims hard deletion. Hard erasure would require a separate owner-authorized MAJOR design for repository rotation or private storage, and still cannot guarantee deletion of third-party copies outside the owner's control.

本机制绝不声称完成硬删除。硬擦除必须另行取得 Owner 授权，并以 MAJOR 级方案设计仓库轮换或私有存储；即便如此，也不能保证删除 Owner 控制范围外的第三方副本。

A future hard-erasure design is out of scope for M-064.
