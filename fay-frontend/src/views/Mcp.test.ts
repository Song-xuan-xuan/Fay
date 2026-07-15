import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import source from './Mcp.vue?raw';

const mcpCss = readFileSync(new URL('../styles/mcp.css', import.meta.url), 'utf-8');

describe('Mcp settings view', () => {
  it('switches between MCP services and the wallpaper library', () => {
    expect(source).toContain("const activeSettingsView = ref<SettingsView>('mcp')");
    expect(source).toContain('class="settings-view-switch"');
    expect(source).toContain('label="mcp"');
    expect(source).toContain('label="backgrounds"');
    expect(source).toContain('v-show="activeSettingsView === \'mcp\'"');
    expect(source).toContain('v-show="activeSettingsView === \'backgrounds\'"');
    expect(source).toContain('v-if="activeSettingsView === \'mcp\'"');
    expect(source).toContain('BackgroundManager');
    expect(source).toContain('mcp-background-manager');
  });

  it('uses stable accessible dimensions for the settings switch', () => {
    expect(mcpCss).toContain('.settings-view-switch .el-radio-button__inner');
    expect(mcpCss).toContain('min-height: 44px;');
  });

  it('matches the rounded translucent console style', () => {
    expect(mcpCss).toContain('border-radius: 999px;');
    expect(mcpCss).toContain('.mcp-panel .el-button:not(.is-circle)');
    expect(mcpCss).toContain('.mcp-panel .mcp-section,');
    expect(mcpCss).toContain('.mcp-panel .background-manager {');
    expect(mcpCss).toContain('backdrop-filter: blur(18px) saturate(155%);');
    expect(mcpCss).toContain('box-shadow: 0 14px 36px rgba(35, 95, 150, 0.12)');
  });

  it('uses a transparent outer surface that does not clip settings content', () => {
    expect(mcpCss).toContain('.stage-content > .mcp-panel {');
    expect(mcpCss).toContain('background: transparent;');
    expect(mcpCss).toContain('box-shadow: none;');
    expect(mcpCss).toContain('overflow: visible;');
    expect(mcpCss).toContain('flex: 0 0 auto;');
  });
});
