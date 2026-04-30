# ReviewPulse Engine - 商家口碑与评价智能管理系统后端

ReviewPulse Engine 是 RateVue 前端配套的后端服务，基于 Spring Boot 3 和 MyBatis Plus 构建。它提供了一套完整的 RESTful API，用于支撑多角色（管理员、商家、普通用户）的评价管理、内容发布、数据分析及 AI 赋能功能。

## 核心功能

- **多角色 API 支持**：针对 Admin、Merchant 和 User 角色提供差异化的接口访问。
- **评价系统**：支持多媒体（图片、视频）评价、回复、点赞及收藏功能。
- **商家模块**：涵盖店铺资料管理、动态内容发布及经营数据统计。
- **AI 赋能接口**：支持与前端 AI 智能助手对接，提供对话日志及文档处理能力。
- **文件服务**：集成文件上传与下载功能，支持图片和视频的分类存储。
- **深度分析支持**：提供高效的数据库查询，支持 ECharts 图表所需的数据聚合。

## 技术栈

- **核心框架**：Spring Boot 3.4.6
- **JDK 版本**：Java 21 (LTS)
- **持久层方案**：MyBatis Plus 3.5.12
- **数据库**：MySQL
- **代码辅助**：Lombok
- **接口文档**：Swagger (Springfox)
- **测试框架**：JUnit 5, Mockito
- **项目构建**：Maven

## 目录结构

```
src/main/java/com/example/mybatisplusdemo/
├── common/        # 全局配置、工具类、统一响应及异常处理
├── mapper/        # MyBatis Mapper 接口层
├── model/         # 数据模型 (domain, dto, vo 分层)
├── service/       # 业务逻辑接口及其实现 (impl)
└── web/           # Web 层，包含 REST Controllers
```

## 环境配置

### 1. 数据库准备
- 导入 `sql/` 目录下的数据库执行脚本。
- 在 `src/main/resources/application.yml` 中配置 MySQL 连接信息。

### 2. 构建项目
```bash
mvn clean install
```

### 3. 运行项目
- 运行 `MybatisPlusDemoApplication.java` 中的 `main` 方法。

## 开发说明
- **代码生成**：本项目集成了 MyBatis Plus Generator，可快速生成基础 CRUD 代码。
- **统一响应**：所有 API 均遵循统一的 JSON 返回格式（Result 包装类）。
- **文件存储**：默认存储地址为项目根目录下的 `./file` 文件夹。
