import { describe, expect, it } from 'vitest';
import type { MessageRecord } from '../types';
import { mergePanelReply } from './messageStream';

describe('mergePanelReply', () => {
  it('appends a new message when current user matches panel reply user', () => {
    const messages: MessageRecord[] = [];

    const next = mergePanelReply(messages, {
      id: 1,
      type: 'fay',
      username: 'User',
      content: '你好',
      timetext: '2026-06-04 10:00:00.000',
    }, 'User');

    expect(next).toHaveLength(1);
    expect(next[0].content).toBe('你好');
  });

  it('concatenates streamed chunks with the same message id and type', () => {
    const messages: MessageRecord[] = [{
      id: 1,
      type: 'fay',
      username: 'User',
      content: '第一段',
    }];

    const next = mergePanelReply(messages, {
      id: 1,
      type: 'fay',
      username: 'User',
      content: '第二段',
      timetext: '2026-06-04 10:00:01.000',
    }, 'User');

    expect(next).toHaveLength(1);
    expect(next[0].content).toBe('第一段第二段');
    expect(next[0].timetext).toBe('2026-06-04 10:00:01.000');
  });

  it('ignores panel replies for a different selected user', () => {
    const messages: MessageRecord[] = [{
      id: 1,
      type: 'user',
      username: 'User',
      content: '已有消息',
    }];

    const next = mergePanelReply(messages, {
      id: 2,
      type: 'fay',
      username: 'Alice',
      content: '不应出现',
    }, 'User');

    expect(next).toEqual(messages);
  });

  it('ignores panel replies for a different selected session', () => {
    const messages: MessageRecord[] = [{
      id: 1,
      type: 'user',
      username: 'User',
      content: '当前会话',
      session_id: 10,
    }];

    const next = mergePanelReply(messages, {
      id: 2,
      type: 'fay',
      username: 'User',
      content: '别的会话',
      session_id: 11,
    }, 'User', 10);

    expect(next).toEqual(messages);
  });
});
