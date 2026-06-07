import type { MessageRecord } from '../types';

function cloneMessage(message: MessageRecord): MessageRecord {
  return {
    ...message,
    thinkExpanded: message.thinkExpanded ?? false,
    thinkLoading: message.thinkLoading ?? false,
  };
}

export function mergePanelReply(
  messages: MessageRecord[],
  panelReply: MessageRecord,
  selectedUsername: string,
): MessageRecord[] {
  if (!panelReply.username || panelReply.username !== selectedUsername) {
    return messages;
  }

  const index = messages.findIndex((message) => (
    message.id === panelReply.id && message.type === panelReply.type
  ));

  if (index === -1) {
    return [...messages, cloneMessage(panelReply)];
  }

  const next = messages.slice();
  const existing = next[index];
  next[index] = {
    ...existing,
    ...panelReply,
    content: `${existing.content || ''}${panelReply.content || ''}`,
    timetext: panelReply.timetext || existing.timetext,
    thinkExpanded: existing.thinkExpanded,
    thinkLoading: panelReply.content?.includes('<think>') && !panelReply.content?.includes('</think>'),
  };
  return next;
}
