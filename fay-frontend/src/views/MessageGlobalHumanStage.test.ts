import { describe, expect, it } from 'vitest';
import messageSource from './Message.vue?raw';

describe('Message global digital human stage integration', () => {
  it('does not render a page-local digital human when the layout provides the global stage', () => {
    expect(messageSource).not.toContain("import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue'");
    expect(messageSource).not.toContain('<DigitalHumanPanel');
    expect(messageSource).not.toContain('digital-human-hero');
  });

  it('keeps the conversation workspace focused on sessions, chat, and composer controls', () => {
    expect(messageSource).toContain('conversation-zone');
    expect(messageSource).toContain('<SessionPanel');
    expect(messageSource).toContain('<MessageList');
    expect(messageSource).toContain('<ChatComposer');
  });
});
