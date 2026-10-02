import { expect, test } from 'claude-code/testing'

const PANE_PROPS = {
  title: 'mathcat',
  isFocused: true,
  bodyColumns: 80,
  placement: 'dock' as const,
  scroll: { offset: 0, bodyRows: 30 },
  view: {},
}

const PNG = '/tmp/mathcat-pane/a.png'

function pngHeader(width: number, height: number) {
  const u32 = (value: number) => [(value >>> 24) & 255, (value >>> 16) & 255, (value >>> 8) & 255, value & 255]
  const bytes = [137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82, ...u32(width), ...u32(height)]
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
  let out = ''
  for (let i = 0; i < bytes.length; i += 3) {
    const triple = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2]
    out += alphabet[(triple >> 18) & 63] + alphabet[(triple >> 12) & 63] + alphabet[(triple >> 6) & 63] + alphabet[triple & 63]
  }
  return out
}

function stub(
  on,
  {
    entries = [] as { path: string; generation: number; tex: string; width?: number; height?: number }[],
    mathcat = { exitCode: 0, stdout: PNG + '\n', stderr: '' } as
      | { exitCode: number; stdout: string; stderr: string }
      | { missing: true },
  } = {},
) {
  const saved: { key: string; value: unknown }[] = []
  const argv: string[][] = []
  on('store.get', (_$, e) => ({ value: e.key === 'entries' ? entries : e.key === 'index' ? 0 : undefined }))
  on('store.set', (_$, e) => {
    saved.push({ key: e.key, value: e.value })
    return { value: undefined }
  })
  on('command.register', () => ({ value: undefined }))
  on('tool.register', () => ({ value: { tool: 'mcp__mathcat__show' } }))
  on('fs.exists', () => ({ value: true }))
  on('fs.stat', () => ({ value: { kind: 'file', size: 12, mtimeMs: 1700000000000, isLink: false } }))
  on('fs.read', () => ({ value: { base64: pngHeader(800, 100) } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.render', () => ({ type: 'Text', props: {}, children: [''] }))
  on('session.start', () => ({ cwd: '/work' }))
  on('clock.now', () => ({ value: 1700000000000 }))
  on('env.get', () => ({ value: '/Users/ada' }))
  on('process.run', (_$, e) => {
    argv.push([...e.argv])
    if (e.argv[0] === 'mkdir') return { value: { exitCode: 0, stdout: '', stderr: '' } }
    if ('missing' in mathcat && e.argv[0] === 'mathcat') return { deny: 'not found' }
    if ('missing' in mathcat) return { value: { exitCode: 0, stdout: PNG + '\n', stderr: '' } }
    return { value: mathcat }
  })
  return { saved, argv }
}

async function start($) {
  await $.session.start({ surface: 'terminal', isInteractive: true, cwd: '/work' })
}

async function pane($) {
  return $.ui.mount({
    plugin: 'mathcat',
    surface: 'terminal',
    requestId: 'mathcat',
    component: 'Pane',
    props: PANE_PROPS,
  })
}

test('opens with no formula', async ($, on) => {
  stub(on)
  await start($)
  const ui = await pane($)
  expect(await ui.find({ type: 'Text', text: /No formula yet/ })).toBeDefined()
  await ui.unmount()
})

test('draws a formula and shows that file', async ($, on) => {
  const { saved, argv } = stub(on)
  await start($)
  const result = await $.command.run({ command: 'mathcat', args: 'e^{i\\pi}+1=0' })
  expect(result.text).toBe('Drew e^{i\\pi}+1=0')
  const draw = argv.find((row) => row[0] === 'mathcat')
  expect(draw).toContain('--local')
  expect(draw).toContain('--')
  expect(draw?.[draw.length - 1]).toBe('e^{i\\pi}+1=0')

  const stored = saved.find((row) => row.key === 'entries')
  expect(stored?.value).toEqual([
    {
      path: PNG,
      generation: 1700000000000,
      tex: 'e^{i\\pi}+1=0',
      legend: false,
      notes: [],
      width: 800,
      height: 100,
    },
  ])

  const ui = await pane($)
  const image = await ui.find({ key: 'view' })
  expect(image?.props.source).toEqual({ file: PNG, format: 'png', generation: 1700000000000 })
  expect(image?.props.columns).toBe(80)
  expect(image?.props.rows).toBe(5)
  await ui.unmount()
})

test('forwards legend and notes, and strips one pair of dollars', async ($, on) => {
  const { argv } = stub(on)
  await start($)
  const result = await $.command.run({
    command: 'mathcat',
    args: "--legend --note 'Q looks.' '$x=1$'",
  })
  expect(result.text).toBe('Drew x=1')
  const draw = argv.find((row) => row[0] === 'mathcat')
  expect(draw).toEqual([
    'mathcat',
    '--local',
    '-o',
    draw?.[3],
    '--legend',
    '--note',
    'Q looks.',
    '--',
    'x=1',
  ])
})

test('a bad formula is not kept', async ($, on) => {
  const { saved } = stub(on, { mathcat: { exitCode: 1, stdout: '', stderr: 'mathcat: unknown symbol\n' } })
  await start($)
  const result = await $.command.run({ command: 'mathcat', args: '\\begin{matrix}' })
  expect(result.text).toBe('mathcat: unknown symbol')
  expect(saved.some((row) => row.key === 'entries')).toBe(false)
})

test('refuses a flag the pane does not take', async ($, on) => {
  const { argv } = stub(on)
  await start($)
  const result = await $.command.run({ command: 'mathcat', args: '--color #fff x=1' })
  expect(result.text).toBe('The pane takes the formula, --legend, and --note.')
  expect(argv.some((row) => row[0] === 'mathcat')).toBe(false)
})

test('drops the formula it is showing', async ($, on) => {
  stub(on, {
    entries: [{ path: PNG, generation: 1, tex: 'E=mc^2', width: 100, height: 20 }],
  })
  await start($)
  const result = await $.command.run({ command: 'mathcat', args: 'drop' })
  expect(result.text).toBe('Dropped E=mc^2')
  const ui = await pane($)
  expect(await ui.find({ type: 'Text', text: /No formula yet/ })).toBeDefined()
  expect(await ui.find({ key: 'view' })).toBeUndefined()
  await ui.unmount()
})

test('the show tool draws into the same pane', async ($, on) => {
  const { saved } = stub(on)
  await start($)
  const result = await $.tool.call({ tool: 'mcp__mathcat__show', tool_use_id: 'u1', tex: 'E=mc^2', legend: false })
  expect(result.result).toBe('Drew E=mc^2')
  const stored = saved.find((row) => row.key === 'entries')
  expect(Array.isArray(stored?.value) && stored.value[0].tex).toBe('E=mc^2')
})

test('uses ~/.local/bin/mathcat when the name is not on PATH', async ($, on) => {
  const { argv } = stub(on, { mathcat: { missing: true } })
  await start($)
  const result = await $.command.run({ command: 'mathcat', args: 'x=1' })
  expect(result.text).toBe('Drew x=1')
  expect(argv.some((row) => row[0] === '/Users/ada/.local/bin/mathcat')).toBe(true)
})
