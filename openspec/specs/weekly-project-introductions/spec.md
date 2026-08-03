# weekly-project-introductions Specification

## Purpose
定义研究周报项目简介从源 Markdown 到页面卡片的完整数据与展示契约，保持仓库优先的字段顺序，将简介与项目定位分别解析，按指定次序呈现并避免展开内容重复，同时使用独立且轻量的视觉样式而不破坏既有事实网格。

## Requirements

### Requirement: Weekly source reports preserve repository-first field order
Weekly project recommendation source Markdown SHALL keep `仓库` before `项目简介` for each weekly project entry.

#### Scenario: Weekly report field order is validated
- **WHEN** a weekly report project is inspected
- **THEN** the `仓库` field appears before the `项目简介` field
- **AND** the `项目简介` field appears before `入选理由`

### Requirement: Weekly introductions are parsed as separate project data
The digest parser SHALL parse `项目简介` into a dedicated project introduction field without replacing the project positioning field.

#### Scenario: Weekly introduction and positioning are both present
- **WHEN** a weekly report project contains `项目简介` and `入选理由`
- **THEN** the parsed project introduction equals the `项目简介` value
- **AND** the parsed project positioning equals the `入选理由` value

### Requirement: Project cards display introductions below positioning
Project cards SHALL render the project introduction below `.project-positioning` when an introduction exists.

#### Scenario: Weekly card has positioning and introduction
- **WHEN** a weekly project has both positioning and introduction text
- **THEN** the positioning is rendered first
- **AND** the introduction is rendered immediately after positioning

### Requirement: Expanded analysis omits duplicated introduction line
Expanded project analysis SHALL omit the raw `项目简介` Markdown list item when that value is already rendered as the card introduction.

#### Scenario: Weekly detail is expanded
- **WHEN** a weekly project detail block is rendered
- **THEN** the expanded analysis does not include a duplicate `项目简介` list item
- **AND** the source Markdown still retains the `项目简介` field

### Requirement: Introductions have distinct lightweight styling
Rendered project introductions SHALL use a distinct lightweight visual treatment from both `.project-positioning` and project fact rows.

#### Scenario: Introduction styling is available
- **WHEN** a project introduction is rendered
- **THEN** it uses a dedicated introduction class
- **AND** the styling does not create a nested card or move the introduction into the facts grid
