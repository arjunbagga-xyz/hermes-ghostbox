import { PANES_AREA, STATUSBAR_AREAS, TRANSCRIPT_DIRECTIVE_AREA, host } from '@hermes/plugin-sdk';
import { useState } from 'react';
import { jsx, jsxs } from 'react/jsx-runtime';

function GhostBoxDirectiveCard({ attrs }) {
  const [expanded, setExpanded] = useState(true);
  const [status, setStatus] = useState((attrs && attrs.status) || 'active');
  
  const shadowId = (attrs && attrs.shadow_id) || 'shadow_7f8a';
  const score = (attrs && attrs.safety_score) || '98';
  const filesChanged = (attrs && attrs.files_changed) || '0';
  const linesAdded = (attrs && attrs.lines_added) || '0';
  const linesRemoved = (attrs && attrs.lines_removed) || '0';

  const handleCommit = () => {
    setStatus('committed');
    const cmd = `ghostbox_fast_forward_commit(shadow_id="${shadowId}")`;
    if (host && host.composer && typeof host.composer.submit === 'function') {
      host.composer.submit(cmd);
    } else if (host && host.composer && typeof host.composer.insertText === 'function') {
      host.composer.insertText(cmd);
    }
  };

  const handleDiscard = () => {
    setStatus('discarded');
    const cmd = `ghostbox_discard_shadow(shadow_id="${shadowId}")`;
    if (host && host.composer && typeof host.composer.submit === 'function') {
      host.composer.submit(cmd);
    } else if (host && host.composer && typeof host.composer.insertText === 'function') {
      host.composer.insertText(cmd);
    }
  };

  return jsxs('div', {
    style: {
      border: '1px solid var(--ui-stroke-secondary, var(--ui-border))',
      borderRadius: '10px',
      background: 'var(--card, var(--ui-surface-2))',
      color: 'var(--foreground, var(--ui-text-primary))',
      padding: '12px 14px',
      margin: '6px 0',
      fontSize: '12px'
    },
    children: [
      jsxs('div', {
        onClick: () => setExpanded(!expanded),
        style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', gap: '8px' },
        children: [
          jsxs('div', {
            style: { display: 'flex', alignItems: 'center', gap: '8px' },
            children: [
              jsx('span', { style: { fontFamily: 'var(--ui-font-mono)', color: 'var(--ui-accent)', fontWeight: 700 }, children: '🔮 GHOST-BOX' }),
              jsx('span', { style: { fontWeight: 600 }, children: `Shadow Sandbox · ${shadowId}` }),
              jsx('span', {
                style: {
                  fontSize: '10px',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: status === 'committed' ? 'rgba(35, 134, 54, 0.2)' : 'rgba(0, 210, 255, 0.15)',
                  color: 'var(--ui-accent)'
                },
                children: status.toUpperCase()
              })
            ]
          }),
          jsx('span', {
            style: { fontFamily: 'var(--ui-font-mono)', fontSize: '11px', color: 'var(--ui-text-secondary)' },
            children: `Safety: ${score}/100 ${expanded ? '▲' : '▼'}`
          })
        ]
      }),
      expanded && jsxs('div', {
        style: { marginTop: '10px', paddingTop: '8px', borderTop: '1px solid var(--ui-stroke-secondary, var(--ui-border))' },
        children: [
          jsxs('div', {
            style: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '10px' },
            children: [
              jsxs('div', {
                style: { padding: '6px 8px', borderRadius: '6px', background: 'var(--ui-surface-1, rgba(255,255,255,0.04))' },
                children: [
                  jsx('div', { style: { fontSize: '10px', color: 'var(--ui-text-secondary)' }, children: 'DIFF STATS' }),
                  jsx('div', { style: { fontWeight: 700, fontFamily: 'var(--ui-font-mono)' }, children: `+${linesAdded} / -${linesRemoved}` })
                ]
              }),
              jsxs('div', {
                style: { padding: '6px 8px', borderRadius: '6px', background: 'var(--ui-surface-1, rgba(255,255,255,0.04))' },
                children: [
                  jsx('div', { style: { fontSize: '10px', color: 'var(--ui-text-secondary)' }, children: 'FILES MODIFIED' }),
                  jsx('div', { style: { fontWeight: 700, fontFamily: 'var(--ui-font-mono)' }, children: `${filesChanged} files` })
                ]
              })
            ]
          }),
          jsxs('div', {
            style: { display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' },
            children: [
              jsx('button', {
                onClick: handleDiscard,
                disabled: status === 'committed' || status === 'discarded',
                style: {
                  padding: '5px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--ui-stroke-secondary, var(--ui-border))',
                  background: 'transparent',
                  color: 'var(--ui-text-secondary)',
                  cursor: (status !== 'committed' && status !== 'discarded') ? 'pointer' : 'default',
                  fontSize: '11px'
                },
                children: 'Discard Shadow'
              }),
              jsx('button', {
                onClick: handleCommit,
                disabled: status === 'committed' || status === 'discarded',
                style: {
                  padding: '5px 12px',
                  borderRadius: '6px',
                  border: 'none',
                  background: 'var(--ui-accent)',
                  color: 'var(--card, var(--ui-surface-2))',
                  fontWeight: 600,
                  cursor: (status !== 'committed' && status !== 'discarded') ? 'pointer' : 'default',
                  fontSize: '11px'
                },
                children: '⚡ Fast-Forward Commit'
              })
            ]
          })
        ]
      })
    ]
  });
}

function GhostBoxSidebarPane() {
  return jsxs('div', {
    style: { padding: '12px', color: 'var(--foreground, var(--ui-text-primary))', fontFamily: 'var(--ui-font-mono)', fontSize: '12px' },
    children: [
      jsx('div', { style: { fontWeight: 700, color: 'var(--ui-accent)', marginBottom: '8px' }, children: '🔮 GHOST-BOX MULTIVERSE MONITOR' }),
      jsx('div', { style: { color: 'var(--ui-text-secondary)', marginBottom: '12px' }, children: 'Speculative sandboxing is active across all tool executions.' }),
      jsxs('div', {
        style: { border: '1px solid var(--ui-stroke-secondary, var(--ui-border))', borderRadius: '6px', padding: '8px' },
        children: [
          jsx('div', { style: { color: 'var(--ui-accent)', fontWeight: 600 }, children: 'Git Worktree Sandbox' }),
          jsx('div', { style: { fontSize: '11px', marginTop: '4px' }, children: '• Ephemeral Git Worktree: Ready' }),
          jsx('div', { style: { fontSize: '11px' }, children: '• Subprocess Secret Scrubbing: Enforced' })
        ]
      })
    ]
  });
}

function GhostBoxStatusPill() {
  return jsx('span', {
    style: { fontFamily: 'var(--ui-font-mono)', fontSize: '11px', color: 'var(--ui-accent)' },
    children: '🔮 ghostbox:isolated'
  });
}

export default {
  id: 'ghostbox',
  name: 'Ghost-Box',
  register(ctx) {
    ctx.register({
      id: 'ghostbox-card',
      area: TRANSCRIPT_DIRECTIVE_AREA,
      data: {
        name: 'ghostbox-card',
        render: ({ attrs }) => jsx(GhostBoxDirectiveCard, { attrs }),
      }
    });

    ctx.register({
      id: 'ghostbox',
      area: PANES_AREA,
      title: 'Ghost-Box',
      data: { placement: 'right', width: '300px' },
      render: () => jsx(GhostBoxSidebarPane, {})
    });

    ctx.register({
      id: 'ghostbox-status',
      area: STATUSBAR_AREAS.right,
      order: 101,
      render: () => jsx(GhostBoxStatusPill, {})
    });
  }
};