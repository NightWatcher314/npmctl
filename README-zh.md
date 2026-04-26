# npmctl

[English](README.md) | [中文](README-zh.md)

`npmctl` 是一个用于通过 API 自动化管理 [Nginx Proxy Manager](https://nginxproxymanager.com/) 的 Python CLI。

`npmctl` 是一个 AI-native 运维项目。仓库内置了 Codex skill：[`skills/nginx-proxy-manager/SKILL.md`](skills/nginx-proxy-manager/SKILL.md)，让 AI agent 可以按照明确的安全规则、命令形状和验证步骤管理 Nginx Proxy Manager，而不是临时猜测原始 API 调用。

它重点覆盖安全的 Proxy Host 工作流：创建和更新代理时不覆盖未指定字段，匹配现有证书，管理原始 `advanced_config` 片段，以及配置 custom locations。

## AI-Native Skill

内置的 `nginx-proxy-manager` skill 会指导 agent 把 `npmctl` 作为 Nginx Proxy Manager 变更的稳定执行器。

skill 中编码的关键规则：

- 不要把 URL path 放进 `forward_host`；目标应当是 `http://host:port` 这样的 origin URL。
- host 级别片段使用 proxy host 的 `advanced_config`，location 级别片段使用 custom location 的 `advanced_config`。
- 更新时保留未指定字段、已有高级配置和已有 locations。
- 变更后使用 `npmctl proxy get DOMAIN -o json` 验证；公开站点再使用 `npmctl proxy test DOMAIN`。
- 删除、清空高级配置、移除 location 等破坏性操作必须有明确用户意图。

## 安装

使用 Homebrew：

```bash
brew tap NightWatcher314/homebrew-formula
brew install npmctl
```

开发环境：

```bash
uv sync
uv run npmctl --help
```

## 配置

创建 profile 并登录：

```bash
npmctl config profile add home --url https://nginx.example.com --use
npmctl auth login --identity admin@example.com
npmctl auth status
```

单次命令指定 profile：

```bash
NPMCTL_PROFILE=home npmctl proxy list
```

查看当前配置：

```bash
npmctl config get
npmctl doctor
```

## Proxy Hosts

列出并查看 Proxy Hosts：

```bash
npmctl proxy list
npmctl proxy get app.example.com -o json
```

创建或更新一个 host：

```bash
npmctl proxy apply app.example.com \
  --to http://192.168.1.10:8080 \
  --cert auto \
  --force-ssl \
  --websocket \
  --http2
```

`proxy apply` 会保留命令行未指定的现有字段，用于让重复执行的自动化流程更安全。

测试公开 host：

```bash
npmctl proxy test app.example.com
```

## 证书

列出证书并为域名匹配合适证书：

```bash
npmctl cert list -o json
npmctl cert match app.example.com -o json
```

## Advanced Config

从 stdin 设置 host 级别 `advanced_config`：

```bash
npmctl proxy advanced set app.example.com --stdin <<'NGINX'
if ($request_uri = "/") {
    return 302 /management.html;
}
NGINX
```

设置 custom location 及其 location 级别 `advanced_config`：

```bash
npmctl proxy location apply app.example.com /api --to http://192.168.1.10:8081
npmctl proxy location advanced set app.example.com /api --stdin <<'NGINX'
proxy_set_header X-Forwarded-Prefix /api;
NGINX
```

转发目标必须是 `http://host:port` 这样的 origin URL。不要把 URL path 放进 `forward_host`；路径行为应使用 custom locations、`forward_path` 或 Nginx 片段处理。

## 认证与存储

默认情况下，`npmctl` 保存 API token，但不保存密码。若要把密码保存到当前 profile：

```bash
NPMCTL_PASSWORD='...' npmctl auth login --identity admin@example.com --save-password
```

之后可以复用保存的密码登录：

```bash
npmctl auth login --use-saved-password
```

配置文件位于 `~/.config/npmctl/config.json`，权限为 `0600`，但保存的密码仍然是明文。只应在可信机器上使用 `--save-password`。

## 开源协议

MIT
