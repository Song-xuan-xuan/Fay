import { describe, expect, it } from 'vitest';
import changePasswordSource from './auth/ChangePasswordDialog.vue?raw';
import profileSource from './auth/ProfileDialog.vue?raw';
import digitalHumanEditorSource from './digital-humans/DigitalHumanEditor.vue?raw';
import mcpServerSource from './mcp/McpServerDialog.vue?raw';
import sharePreviewSource from './messages/SharePreviewDialog.vue?raw';
import userInfoSource from './messages/UserInfoDialog.vue?raw';
import auditLogSource from './users/AuditLogDrawer.vue?raw';
import live2dSource from '../views/Live2D.vue?raw';
import userManagementSource from '../views/UserManagement.vue?raw';

const overlaySources = [
  { name: 'ChangePasswordDialog', source: changePasswordSource },
  { name: 'ProfileDialog', source: profileSource },
  { name: 'DigitalHumanEditor', source: digitalHumanEditorSource },
  { name: 'McpServerDialog', source: mcpServerSource },
  { name: 'SharePreviewDialog', source: sharePreviewSource },
  { name: 'UserInfoDialog', source: userInfoSource },
  { name: 'AuditLogDrawer', source: auditLogSource },
  { name: 'Live2D', source: live2dSource },
  { name: 'UserManagement', source: userManagementSource },
];

function overlayTags(source: string) {
  return source.match(/<el-(?:dialog|drawer)\b[^>]*>/gs) || [];
}

describe('overlay components', () => {
  for (const { name, source } of overlaySources) {
    it(`${name} mounts full-screen overlays to body`, () => {
      const tags = overlayTags(source);
      expect(tags.length).toBeGreaterThan(0);
      for (const tag of tags) {
        expect(tag).toContain('append-to-body');
      }
    });
  }
});
