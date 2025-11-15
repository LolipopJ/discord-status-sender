# Discord Status Sender

## 如何使用

准备运行环境：

```bash
# 安装依赖库
pipenv install
# 进入虚拟环境
pipenv shell
```

添加环境变量。拷贝 `.env.example` 里的内容，新建 `.env`；或使用 Docker 部署时，编辑 `docker-compose.yml` 中的配置项 `environment`：

- 修改 `DISCORD_TOKEN` 为子账户的 `authorization` 令牌。
- 修改 `DISCORD_CHANNEL_ID` 为子账户与主账户的私聊频道编号。

运行应用：

```bash
python main.py
```

## 贡献代码

在提交前自动格式化代码：

```bash
# 对于开发者，注册 commit 钩子
pre-commit install
```
