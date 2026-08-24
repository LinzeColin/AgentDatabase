# External Verifier Handoff

```bash
python3 scripts/teleiosis.py verifier-handoff build --output /outside/acceptance-review.zip
python3 scripts/teleiosis.py verifier-handoff validate --zip /outside/acceptance-review.zip
```

ZIP 包含冻结 SubjectIdentity、Acceptance、Traceability、Canonical State、release metadata、Project Input 和本地验证摘要，并有独立 handoff manifest。它是给外部 Verifier 的只读输入，不是内部正式裁决。

外部 Verifier 必须重新绑定精确制品、运行风险驱动测试、检查 Requirement→Acceptance→Oracle→Test→Evidence，并保持 NOT_RUN/UNKNOWN/WAIVED 不等于 PASS。
