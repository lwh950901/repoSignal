window.__ModuleLoader__.load({
  id: '@local/dsh-fresh-session-min',
  factory(require) {
    const React = require('react');
    const h = React.createElement;
    const PANEL_ID = 'fresh-session-min';

    // 只读快照：客户端读不到宿主文件，这里的字段与 cordis.patch.yml 的 config 手动保持同步。
    const SNAPSHOT = {
      title: '每日GitHub组合可行性方案',
      timeOfDay: '06:30',
      timeZone: 'Asia/Shanghai',
      workspace: 'repo-signal',
      trigger: '内置定时任务（每天 06:30，绑定旧会话）',
      receipt: '本对话（session-53a154fd）',
      promptSource: 'data/github-project-digest/feasibility/FEASIBILITY-TASK.md',
      reportDir: 'data/github-project-digest/feasibility/',
      configPath: 'dsh-plugins/fresh-session-min/cordis.patch.yml',
    };

    const styles = {
      page: {
        minHeight: '100%',
        boxSizing: 'border-box',
        padding: '32px 40px',
        maxWidth: '760px',
        color: 'var(--dsw-alias-label-primary, #1f2328)',
        background: 'var(--dsw-alias-bg-base, transparent)',
      },
      title: { margin: '0 0 6px', fontSize: '22px', fontWeight: 600, letterSpacing: '-0.01em' },
      subtitle: {
        margin: '0 0 24px',
        color: 'var(--dsw-alias-label-secondary, #59636e)',
        fontSize: '13px',
        lineHeight: 1.6,
      },
      card: {
        border: '1px solid var(--dsw-alias-border-l, #d0d7de)',
        borderRadius: '10px',
        padding: '16px 20px',
        marginBottom: '16px',
      },
      row: { display: 'flex', gap: '12px', padding: '6px 0', fontSize: '13px', lineHeight: 1.5 },
      label: { flex: '0 0 88px', color: 'var(--dsw-alias-label-tertiary, #6e7781)' },
      value: { flex: '1 1 auto', wordBreak: 'break-word' },
      note: {
        margin: '18px 0 0',
        color: 'var(--dsw-alias-label-tertiary, #6e7781)',
        fontSize: '12px',
        lineHeight: 1.7,
      },
    };

    function Row(props) {
      return h(
        'div',
        { style: styles.row },
        h('span', { style: styles.label }, props.label),
        h('span', { style: styles.value }, props.children),
      );
    }

    function Page() {
      return h(
        'div',
        { style: styles.page },
        h('h1', { style: styles.title }, SNAPSHOT.title),
        h(
          'p',
          { style: styles.subtitle },
          '当前触发由内置定时任务负责（每天 06:30，出现在自动化任务页）；插件的自动触发已关闭（autoRun: false），不会再双跑。',
        ),
        h(
          'div',
          { style: styles.card },
          h(Row, { label: '触发方式' }, SNAPSHOT.trigger),
          h(Row, { label: '触发时间' }, '每天 ' + SNAPSHOT.timeOfDay + '（' + SNAPSHOT.timeZone + '）'),
          h(Row, { label: '工作区' }, SNAPSHOT.workspace),
          h(Row, { label: '回执会话' }, SNAPSHOT.receipt),
          h(Row, { label: '提示词' }, SNAPSHOT.promptSource),
          h(Row, { label: '报告目录' }, SNAPSHOT.reportDir),
        ),
        h(
          'div',
          { style: styles.card },
          h(Row, { label: '配置文件' }, SNAPSHOT.configPath),
          h(Row, {
            label: '修改方式',
            children: '编辑上面的配置文件后重启应用（或重装插件）生效；本页只读，不直接改配置。',
          }),
        ),
        h(
          'p',
          { style: styles.note },
          '本页是配置快照（与 cordis.patch.yml 手动同步）；每次运行的结果以收到的回执为准，历史报告在报告目录里。',
        ),
      );
    }

    function Icon() {
      return h(
        'svg',
        { viewBox: '0 0 24 24', width: 20, height: 20, 'aria-hidden': true, style: { display: 'block' } },
        h('path', {
          fill: 'currentColor',
          d: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 2a7 7 0 1 1 0 14 7 7 0 0 1 0-14Zm-1 3v4.4l3.3 2 1-1.6-2.3-1.4V8h-2Z',
        }),
      );
    }

    return {
      inject: ['slots'],
      apply(ctx) {
        ctx.slots.inject('main', () =>
          ctx.slots.register({ name: 'main', key: PANEL_ID }, Page),
        );
        ctx.slots.inject('sidebar.panellist', () =>
          ctx.slots.register(
            { name: 'sidebar.panellist', id: PANEL_ID, order: 20, label: () => '可行性任务' },
            Icon,
          ),
        );
      },
    };
  },
});
