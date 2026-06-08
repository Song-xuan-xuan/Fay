import type { MessageRecord } from '../types';

function cloneMessage(message: MessageRecord): MessageRecord {
  return {
    ...message,
    thinkExpanded: message.thinkExpanded ?? false,
    thinkLoading: message.thinkLoading ?? false,
  };
}

function normalizeSessionId(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined) {
    return null;
  }
  const next = Number(value);
  return Number.isNaN(next) ? null : next;
}

export function mergePanelReply(
  messages: MessageRecord[],
  panelReply: MessageRecord,
  selectedUsername: string,
  selectedSessionId: number | null = null,
): MessageRecord[] {
  if (!panelReply.username || panelReply.username !== selectedUsername) {
    return messages;
  }
  if (selectedSessionId !== null && normalizeSessionId(panelReply.session_id) !== selectedSessionId) {
    return messages;
  }

  const index = messages.findIndex((message) => (
    message.id === panelReply.id && message.type === panelReply.type && (
      selectedSessionId === null || normalizeSessionId(message.session_id) === selectedSessionId
    )
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
