import { describe, expect, it } from 'vitest';
import { exampleImportJson } from '../config/recommendationImportExample';
import routeWorkbenchSource from '../components/recommendation/RouteWorkbench.vue?raw';
import source from './RecommendationManage.vue?raw';

describe('RecommendationManage view', () => {
  it('offers an import tutorial explaining package fields and weights', () => {
    expect(source).toContain('导入教程');
    expect(source).toContain('importTutorialVisible');
    expect(source).toContain('完整包字段说明');
    expect(source).toContain('权重说明');
    expect(source).toContain('interest_match');
    expect(source).toContain('template_external_id');
    expect(source).toMatch(/<el-dialog[\s\S]*append-to-body/);
  });

  it('includes a copyable complete JSON example in the import tutorial', () => {
    expect(source).toContain('exampleImportJson');
    expect(source).toContain('复制示例 JSON');
    expect(source).toContain('handleCopyExampleJson');
    expect(source).toContain('navigator.clipboard.writeText');
    expect(source).toContain('import-example-code');
  });

  it('presents route maintenance as a route workbench', () => {
    const workbench = `${source}\n${routeWorkbenchSource}`;

    expect(workbench).toContain('路线工作台');
    expect(workbench).toContain('路线时间轴');
    expect(workbench).toContain('节点详情');
    expect(workbench).toContain('上移');
    expect(workbench).toContain('下移');
    expect(workbench).toContain('高级配置');
  });

  it('uses administrator-friendly labels for attraction and strategy maintenance', () => {
    expect(source).toContain('景点资料库');
    expect(source).toContain('高级信息');
    expect(source).toContain('推荐策略');
    expect(source).toContain('更重视兴趣匹配');
  });

  it('ships a valid full-package example JSON', () => {
    const example = JSON.parse(exampleImportJson);
    expect(example.attractions[0].external_id).toBe('spot-lingshan-buddha');
    expect(example.templates[0].external_id).toBe('route-half-day-classic');
    expect(example.stops[0].template_external_id).toBe('route-half-day-classic');
    expect(example.edges[0].from_attraction_external_id).toBe('spot-lingshan-buddha');
    expect(example.config.weights.interest_match).toBe(0.45);
  });
});
