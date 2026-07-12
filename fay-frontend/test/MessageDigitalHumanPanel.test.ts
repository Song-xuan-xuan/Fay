import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import appLayoutSource from '../src/layouts/AppLayout.vue?raw';
import dashboardSource from '../src/views/Dashboard.vue?raw';
import messageSource from '../src/views/Message.vue?raw';
import digitalHumanPanelSource from '../src/components/messages/DigitalHumanPanel.vue?raw';
import chatComposerSource from '../src/components/messages/ChatComposer.vue?raw';

const pagesCss = readFileSync(new URL('../src/styles/pages.css', import.meta.url), 'utf-8');
const markdownCss = readFileSync(new URL('../src/styles/markdown.css', import.meta.url), 'utf-8');
const chatComposerCss = readFileSync(new URL('../src/components/messages/ChatComposer.css', import.meta.url), 'utf-8');

function getCssBlock(source: string, selector: string) {
  const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const matches = [...source.matchAll(new RegExp(`(?:^|\\n)${escapedSelector}\\s*\\{([\\s\\S]*?)\\n\\}`, 'g'))];
  return matches.at(-1)?.[1] ?? '';
}

describe('message digital human panel', () => {
  it('uses a message-specific view context from the global layout stage', () => {
    expect(appLayoutSource).toContain('<DigitalHumanPanel :view-context="digitalHumanContext" />');
    expect(appLayoutSource).toContain("route.name === 'message' ? 'message' : 'default'");
    expect(messageSource).not.toContain('<DigitalHumanPanel');
    expect(dashboardSource).not.toContain('<DigitalHumanPanel');
    expect(dashboardSource).not.toContain('view-context="message"');
  });

  it('allows autoplay inside the digital human iframe', () => {
    expect(digitalHumanPanelSource).toContain('allow="autoplay"');
  });

  it('composes the message page as an immersive chat stage', () => {
    expect(messageSource).toContain('immersive-message-stage');
    expect(messageSource).toContain('conversation-glass');
    expect(messageSource).toContain('conversation-zone');
    expect(messageSource).not.toContain('digital-human-hero');
    expect(appLayoutSource).not.toContain('voice-orb');
  });

  it('labels manual voice input separately from continuous voice conversation', () => {
    expect(chatComposerSource).toContain('语音发送');
    expect(chatComposerSource).toContain('连续语音对话');
    expect(chatComposerSource).toContain('无需唤醒词');
  });

  it('keeps the composer input readable in the narrow glass chat panel', () => {
    expect(chatComposerSource).toContain('class="composer-shell"');
    expect(chatComposerSource).toContain('class="composer-input"');
    expect(chatComposerSource).toContain('class="composer-toolbar"');
    expect(chatComposerSource).toContain('class="composer-icon-button"');
    expect(chatComposerSource).not.toContain('class="composer-primary-actions"');
    expect(chatComposerCss).toContain('position: absolute;');
    expect(chatComposerCss).toContain('border-radius: 22px;');
  });

  it('keeps the composer visible by making only the message list scroll', () => {
    expect(getCssBlock(pagesCss, '.immersive-message-stage')).toContain('height: calc(100vh - 128px);');
    expect(getCssBlock(pagesCss, '.conversation-zone')).toContain('height: min(720px, calc(100vh - 168px));');
    expect(getCssBlock(pagesCss, '.conversation-glass')).toContain('height: 100%;');
    expect(getCssBlock(pagesCss, '.chat-panel')).toContain('height: 100%;');
    expect(getCssBlock(pagesCss, '.composer')).toContain('flex: 0 0 auto;');
    expect(getCssBlock(pagesCss, '.chat-body')).toContain('overflow-y: auto;');
  });

  it('keeps long assistant reasoning inside the chat bubble', () => {
    expect(getCssBlock(pagesCss, '.chat-body')).toContain('overflow-x: hidden;');
    expect(getCssBlock(pagesCss, '.message-row')).toContain('width: min(100%, 70%);');
    expect(getCssBlock(pagesCss, '.message-bubble')).toContain('overflow: hidden;');
    expect(getCssBlock(pagesCss, '.think-block')).toContain('overflow-wrap: anywhere;');
    expect(getCssBlock(pagesCss, '.think-block')).toContain('word-break: break-word;');
    expect(getCssBlock(markdownCss, '.markdown-body pre')).toContain('white-space: pre-wrap;');
    expect(getCssBlock(markdownCss, '.markdown-body pre')).toContain('overflow-wrap: anywhere;');
  });
});
