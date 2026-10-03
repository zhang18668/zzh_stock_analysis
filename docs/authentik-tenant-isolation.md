# Authentik 用户数据隔离

部署在 Authentik Forward Auth 后时，可启用按用户隔离模式：

```env
TENANT_ISOLATION_ENABLED=true
TENANT_ID_HEADER=X-authentik-uid
API_BIND_HOST=127.0.0.1
```

启用后，后端使用 Authentik 的稳定用户 UID 计算不可逆目录键，并分别保存：

- SQLite 数据库：`data/tenants/<tenant-key>/<database-file>`
- 本地报告：`reports/tenants/<tenant-key>/`
- Web 分析任务队列、任务状态和 SSE 订阅

该模式只能在可信反向代理后开启。代理必须删除客户端传入的
`X-authentik-*` 身份头，再写入 Authentik 校验后的值；应用端口不得直接暴露到公网。
缺少身份头的非健康检查请求会返回 `401`，不会回退到共享租户。

运行配置和模型/通知密钥仍属于服务器级配置，不复制到每个用户数据库。建议仅允许管理员访问设置页。
定时任务等不带 Web 身份的后台入口继续使用默认数据库，不能读取任一用户租户数据库。

## Authentik user data isolation

Set the two variables above only behind a trusted Authentik Forward Auth proxy.
Each authenticated UID gets an opaque directory key, a separate SQLite database,
a separate report directory, and an independent in-memory Web task queue. Requests
without a verified identity fail closed with `401`. Runtime configuration and
provider credentials remain server-scoped and should be restricted to administrators.
