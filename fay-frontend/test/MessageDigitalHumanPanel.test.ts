import { describe, expect, it } from 'vitest';
import appLayoutSource from '../src/layouts/AppLayout.vue?raw';
import dashboardSource from '../src/views/Dashboard.vue?raw';
import messageSource from '../src/views/Message.vue?raw';
import chatComposerSource from '../src/components/messages/ChatComposer.vue?raw';

describe('message digital human panel', () => {
  it('uses a message-specific view context from the global layout stage', () => {
    expect(appLayoutSource).toContain('<DigitalHumanPanel :view-context="digitalHumanContext" />');
    expect(appLayoutSource).toContain("route.name === 'message' ? 'message' : 'default'");
    expect(messageSource).not.toContain('<DigitalHumanPanel');
    expect(dashboardSource).not.toContain('<DigitalHumanPanel');
    expect(dashboardSource).not.toContain('view-context="message"');
  });

  it('composes the message page as an immersive chat stage', () => {
    expect(messageSource).toContain('immersive-message-stage');
    expect(messageSource).toContain('conversation-glass');
    expect(messageSource).toContain('conversation-zone');
    expect(messageSource).not.toContain('digital-human-hero');
    expect(appLayoutSource).toContain('voice-orb');
  });

  it('labels manual voice input separately from realtime listening', () => {
    expect(chatComposerSource).toContain('语音发送');
    expect(chatComposerSource).toContain('实时监听');
    expect(chatComposerSource).toContain('唤醒词检测');
  });

  it('keeps the composer input readable in the narrow glass chat panel', () => {
    expect(chatComposerSource).toContain('grid-template-columns: minmax(180px, 1fr) auto auto;');
    expect(chatComposerSource).toContain('grid-column: 1 / -1;');
  });
});
