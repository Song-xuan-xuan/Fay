import { describe, expect, it } from 'vitest';
import dashboardSource from './Dashboard.vue?raw';
import messageSource from './Message.vue?raw';

describe('message digital human panel', () => {
  it('uses a message-specific view context without changing the dashboard panel', () => {
    expect(messageSource).toContain('<DigitalHumanPanel view-context="message" />');
    expect(dashboardSource).toContain('<DigitalHumanPanel v-if="!rightCollapsed" />');
    expect(dashboardSource).not.toContain('view-context="message"');
  });
});
