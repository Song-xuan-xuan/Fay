import type { MessageRecord } from '../types';

export function toggleShareMessage(messages: MessageRecord[], index: number): MessageRecord[] {
  return messages.map((message, currentIndex) => (
    currentIndex === index ? { ...message, shareSelected: !message.shareSelected } : message
  ));
}

export function selectAllShareMessages(messages: MessageRecord[]): MessageRecord[] {
  return messages.map((message) => ({ ...message, shareSelected: true }));
}

export function clearShareSelection(messages: MessageRecord[]): MessageRecord[] {
  return messages.map((message) => ({ ...message, shareSelected: false }));
}

export function getShareSelectedMessages(messages: MessageRecord[]): MessageRecord[] {
  return messages.filter((message) => message.shareSelected);
}
