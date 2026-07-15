import { describe, expect, it } from 'vitest';
import capabilitySource from './CapabilityNetwork.vue?raw';
import ctaSource from './HomeCta.vue?raw';
import guideSource from './DigitalHumanStory.vue?raw';
import heroSource from './HomeHero.vue?raw';
import insightSource from './InsightStory.vue?raw';
import ragSource from './RagStory.vue?raw';
import routeSource from './RouteStory.vue?raw';
import homeSource from '../../views/Home.vue?raw';
import contentSource from '../../config/homeContent.ts?raw';

const homepageCopy = [
  heroSource,
  guideSource,
  ragSource,
  routeSource,
  capabilitySource,
  insightSource,
  ctaSource,
  homeSource,
  contentSource,
].join('\n');

describe('homepage concise copy', () => {
  it('removes source paths, repeated sample labels and implementation explanations', () => {
    expect(homepageCopy).not.toContain('library/灵山胜境');
    expect(homepageCopy).not.toContain('仅用于展示系统的数据分析能力');
    expect(homepageCopy).not.toContain('样本量 n=');
    expect(homepageCopy).not.toContain('语音进入系统后，数字人完成理解、检索与表达');
    expect(insightSource).not.toContain('<details');
    expect(contentSource).not.toContain('HOME_SOURCES');
  });

  it('uses the approved technology and cultural-tourism copy', () => {
    expect(heroSource).toContain('让景区会讲述，让服务更懂游客。');
    expect(guideSource).toContain('让景区知识，真正开口说话');
    expect(ragSource).toContain('有依据的回答，才值得信任');
    expect(routeSource).toContain('把时间，变成一条刚好的路线');
    expect(capabilitySource).toContain('一个数字人，连接整个景区');
    expect(insightSource).toContain('从每一次游览，看见真实需求');
    expect(ctaSource).toContain('下一段旅程');
    expect(homeSource).toContain('想听灵山故事，还是规划一条游览路线？');
  });

  it('keeps the existing homepage section structure', () => {
    expect(heroSource).toContain('class="home-section home-hero"');
    expect(guideSource).toContain('home-guide-story');
    expect(ragSource).toContain('home-rag-story');
    expect(routeSource).toContain('home-route-story');
    expect(capabilitySource).toContain('home-network-story');
    expect(insightSource).toContain('home-insight-story');
    expect(ctaSource).toContain('class="home-section home-cta"');
  });
});

