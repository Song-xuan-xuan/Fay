import { describe, expect, it } from 'vitest';
import type { MessageRecord } from '../types';
import {
  clearShareSelection,
  selectAllShareMessages,
  toggleShareMessage,
  getShareSelectedMessages,
} from './shareSelection';

const messages: MessageRecord[] = [
  { id: 1, type: 'user', content: 'one' },
  { id: 2, type: 'fay', content: 'two', shareSelected: true },
];

describe('shareSelection', () => {
  it('toggles a single message without mutating the source array', () => {
    const next = toggleShareMessage(messages, 0);

    expect(messages[0].shareSelected).toBeUndefined();
    expect(next[0].shareSelected).toBe(true);
    expect(next[1].shareSelected).toBe(true);
  });

  it('selects and clears all messages', () => {
    expect(selectAllShareMessages(messages).every((message) => message.shareSelected)).toBe(true);
    expect(clearShareSelection(messages).every((message) => message.shareSelected === false)).toBe(true);
  });

  it('returns only selected messages in original order', () => {
    const selected = getShareSelectedMessages(messages);

    expect(selected).toEqual([{ id: 2, type: 'fay', content: 'two', shareSelected: true }]);
  });
});
