---
name: film-team-setup
description: Establish or update a Film OS production team roster, including how each person is addressed, GitHub usernames, roles, and optional delivery repositories. Use during new-project onboarding or when a project's team composition changes.
---

# Film Team Setup

用于建立或更新作品项目的团队名单。三人只是当前默认示例，团队人数和称呼必须由项目实际团队决定。

## 必须先读

- `AGENTS.md`
- `PROJECT.yaml`
- `项目工作区/00_团队与权限.md`
- `governance/AUTHORITY.yaml`
- `governance/TEAM.yaml`（若存在）

## 询问内容

按自然语言一次询问：

1. 导演怎么称呼？
2. 导演的 GitHub 用户名？
3. 团队一共有多少人，包括导演？
4. 除导演外的每位主创怎么称呼？
5. 每位主创的 GitHub 用户名？
6. 每位主创主要负责什么？
7. 每位主创是否已有交付仓库？有则记录地址，没有可以后补。

不要替任何人决定称呼、角色或仓库。不知道的字段使用“待补充”。

## 写入方式

确认信息后运行：

```bash
python3 tools/team_setup.py \
  --project . \
  --director-name "<导演称呼>" \
  --director-github "<导演GitHub>" \
  --expected-size <总人数> \
  --member "<主创称呼>|<GitHub用户名>|<负责内容>|<交付仓库地址或空>"
```

`--member` 可以重复。工具会自动：

- 写入 `governance/TEAM.yaml`
- 更新 `项目工作区/00_团队与权限.md`
- 有交付仓库时同步更新 `governance/MEMBER_DELIVERY_REPOSITORIES.yaml`

## 权限边界

- 只有通过本地导演钥匙验证的工作区可以修改团队名单。
- 主创可以查看和提议，但不能直接改写正式团队名单。
- 团队名单不等于创作审批权限；导演权限仍由导演钥匙决定。
- 不根据 GitHub 用户名、聊天账号或电脑名称推断导演身份。
- 不把 API Key、令牌或私人凭证写入团队名单。

## 完成后

报告：

- 导演称呼
- 团队总人数
- 每位主创的称呼、GitHub、负责内容和交付仓库状态
- 是否还有“待补充”字段
- 唯一的下一步
