// mathcat: draw a formula to a PNG and show that file in a pane.
// The terminal reads the file. This module keeps the path.

import { cellBox, drawArgv, parse, pngSize, screenPng } from './formula.js'

const PANE = 'mathcat'
const STORE = 'entries'
const DIR = '/tmp/mathcat-pane'
const SHOW = 'mcp__mathcat__show'

let entries = []
let index = 0
let note = ''

export function register(on) {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'mathcat',
      description: 'Draw a formula and show it',
      argumentHint: '[formula | --legend | --note | drop]',
      immediate: true,
    })
    await $.tool.register({
      name: 'show',
      description: 'Draw one mathtext formula and show the PNG in the mathcat pane.',
      inputSchema: {
        type: 'object',
        properties: {
          tex: { type: 'string', description: 'One formula. No preamble.' },
          legend: { type: 'boolean', description: 'Add the English-name ledger.' },
          notes: {
            type: 'array',
            items: { type: 'string' },
            description: 'Short fine-print lines under the formula.',
          },
        },
        required: ['tex'],
      },
    })
    await load($)
    return next(e)
  })

  on('classic.SessionStart', { source: ['clear', 'resume', 'fork'] }, async ($, e, next) => {
    await load($)
    return next(e)
  })

  on('command.run', { command: 'mathcat' }, async ($, e) => {
    const text = await run($, e.args || '')
    await present($)
    return { text }
  })

  on('tool.call', { tool: SHOW }, async ($, e) => {
    const text = await draw($, jobFromTool(e))
    await present($)
    return { result: text }
  })

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== PANE) return next(e)
    const { Box, Text, Button, Input, Image } = $.ui.resolve(e)
    const current = entries[index]
    const fitted = current ? cellBox(e.props.bodyColumns, current.width, current.height) : null
    const picture =
      current && e.surface === 'terminal' && Image
        ? Image({
            key: 'view',
            source: { file: current.path, format: 'png', generation: current.generation },
            columns: fitted.columns,
            rows: fitted.rows,
            alt: current.tex.slice(0, 200),
          })
        : Text({ children: [current ? current.tex : 'No formula yet.'] })
    const where = current
      ? Text({ dimColor: true, children: [index + 1 + '/' + entries.length + '  ' + current.tex] })
      : Text({ dimColor: true, children: ['/mathcat e^{i\\pi}+1=0'] })
    return Box({
      flexDirection: 'column',
      gap: 1,
      children: [
        picture,
        where,
        ...(current ? [Text({ dimColor: true, children: [current.path] })] : []),
        ...(note ? [Text({ children: [note] })] : []),
        Box({
          flexDirection: 'row',
          columnGap: 2,
          children: [
            Button({ key: 'prev', label: 'Prev', plain: true, onPress: () => shift($, -1) }),
            Button({ key: 'next', label: 'Next', plain: true, onPress: () => shift($, 1) }),
            Button({ key: 'drop', label: 'Drop', plain: true, onPress: () => remove($) }),
          ],
        }),
        Input({
          key: 'draw',
          label: 'TeX',
          placeholder: 'e^{i\\pi}+1=0',
          value: '',
          submitLabel: 'draw',
          onSubmit: (value) => run($, value),
        }),
      ],
    })
  })
}

async function present($) {
  await $.ui.open({ id: PANE, title: 'mathcat', focus: true, closeOnEscape: true, rows: 28 })
}

async function load($) {
  const stored = await $.store.get(STORE)
  entries = Array.isArray(stored) ? stored.filter(isEntry) : []
  const storedIndex = await $.store.get('index')
  index = Number.isInteger(storedIndex) ? storedIndex : 0
  if (entries.length === 0) index = 0
  else if (index < 0 || index >= entries.length) index = 0
}

async function save($) {
  await $.store.set(STORE, entries)
  await $.store.set('index', index)
}

function isEntry(value) {
  return !!value && typeof value.path === 'string' && typeof value.tex === 'string' && Number.isInteger(value.generation)
}

function jobFromTool(event) {
  const input = event.input && typeof event.input === 'object' ? event.input : event
  const parsed = parse('-- ' + String(input.tex ?? ''))
  if (parsed.error || parsed.kind !== 'draw') return parsed.error ? parsed : { error: 'Give a formula.' }
  const raw = Array.isArray(input.notes) ? input.notes : typeof input.notes === 'string' ? [input.notes] : []
  const notes = raw.map((note) => String(note))
  if (notes.some((note) => note.trim() === '')) return { error: 'A --note needs a line.' }
  if (notes.length > 12) return { error: 'Too many notes.' }
  if (notes.some((note) => note.length > 500)) return { error: 'A note is too long.' }
  return { kind: 'draw', tex: parsed.tex, legend: input.legend === true, notes }
}

async function run($, args) {
  const parsed = parse(args)
  if (parsed.error) return fail($, parsed.error)
  if (parsed.kind === 'open') {
    note = ''
    return entries.length ? entries.length + ' formula' + (entries.length === 1 ? '' : 's') + '.' : 'No formula yet.'
  }
  if (parsed.kind === 'drop') return remove($)
  return draw($, parsed)
}

async function draw($, job) {
  if (job.error) return fail($, job.error)
  if (!job.tex) return fail($, 'Give a formula.')
  const made = await $.process.run(['mkdir', '-p', DIR])
  if (!made || made.exitCode !== 0) return fail($, 'Could not write the PNG.')
  const stamp = await stampOf($)
  const out = DIR + '/' + stamp.toString(36) + '-' + Math.random().toString(36).slice(2, 8) + '.png'
  const argv = drawArgv(out, job)
  const ran = await runMathcat($, argv.slice(1))
  if (ran.error) return fail($, ran.error)
  if (ran.exitCode !== 0) {
    const detail = String(ran.stderr || ran.stdout || '').trim()
    return fail($, detail || 'The formula did not render.')
  }
  const screened = screenPng(ran.stdout)
  if (screened.error) return fail($, screened.error)
  const exists = await $.fs.exists(screened.path)
  if (!exists) return fail($, 'mathcat did not write a PNG.')
  const generation = await generationOf($, screened.path)
  const size = await measure($, screened.path)
  const entry = {
    path: screened.path,
    generation,
    tex: job.tex,
    legend: !!job.legend,
    notes: job.notes || [],
    width: size ? size.width : 0,
    height: size ? size.height : 0,
  }
  const found = entries.findIndex((item) => same(item, entry))
  if (found >= 0) {
    entries[found] = entry
    index = found
  } else {
    entries.push(entry)
    index = entries.length - 1
  }
  note = ''
  await save($)
  $.ui.invalidate('ui.render')
  return 'Drew ' + job.tex
}

async function runMathcat($, args) {
  const first = await tryRun($, ['mathcat', ...args])
  if (first.started) return first
  let home = ''
  try {
    home = (await $.env.get('HOME')) || ''
  } catch {
    home = ''
  }
  if (home) {
    const second = await tryRun($, [home.replace(/\/$/, '') + '/.local/bin/mathcat', ...args])
    if (second.started) return second
  }
  return { error: 'mathcat is not on PATH.' }
}

async function tryRun($, argv) {
  try {
    const ran = await $.process.run(argv, { timeoutMs: 60000 })
    return { started: true, exitCode: ran.exitCode, stdout: ran.stdout, stderr: ran.stderr }
  } catch {
    return { started: false }
  }
}

async function measure($, path) {
  try {
    const file = await $.fs.read(path, { as: 'bytes' })
    return pngSize(file && file.base64)
  } catch {
    return null
  }
}

async function stampOf($) {
  try {
    const now = await $.clock.now()
    if (Number.isFinite(now)) return Math.max(0, Math.floor(now))
  } catch {
    // Date.now still names a new file.
  }
  return Date.now()
}

async function generationOf($, path) {
  try {
    const stat = await $.fs.stat(path)
    if (stat && Number.isFinite(stat.mtimeMs)) return Math.max(0, Math.floor(stat.mtimeMs))
  } catch {
    // A missing stamp still shows the file. Drawing it again bumps the number.
  }
  return Date.now()
}

function same(entry, job) {
  const notes = Array.isArray(entry.notes) ? entry.notes : []
  const next = job.notes || []
  return entry.tex === job.tex && !!entry.legend === !!job.legend && notes.length === next.length && notes.every((line, i) => line === next[i])
}

async function shift($, by) {
  if (entries.length === 0) return
  index = (index + by + entries.length) % entries.length
  note = ''
  await save($)
  $.ui.invalidate('ui.render')
}

async function remove($) {
  if (entries.length === 0) return fail($, 'No formula yet.')
  const gone = entries[index].tex
  entries.splice(index, 1)
  if (index >= entries.length) index = 0
  note = ''
  await save($)
  $.ui.invalidate('ui.render')
  return 'Dropped ' + gone
}

function fail($, text) {
  note = text
  $.ui.invalidate('ui.render')
  return text
}
