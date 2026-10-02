// Turn a /mathcat line into one formula, and size the pane box to the PNG.
// Terminal cells are about twice as tall as they are wide.

const FLAGS = new Set(['--legend', '--note', '--local', '--'])

export function parse(text) {
  const raw = String(text ?? '').trim()
  if (raw === '' || raw === 'open') return { kind: 'open' }
  if (raw === 'drop') return { kind: 'drop' }
  const tokens = tokenize(raw)
  if (tokens.error) return { error: tokens.error }

  let legend = false
  const notes = []
  const tex = []
  for (let i = 0; i < tokens.value.length; i++) {
    const token = tokens.value[i]
    if (token === '--') {
      tex.push(...tokens.value.slice(i + 1))
      break
    }
    if (token === '--legend') {
      legend = true
      continue
    }
    if (token === '--local') continue
    if (token === '--note') {
      const note = tokens.value[++i]
      if (note == null || note.trim() === '') return { error: 'A --note needs a line.' }
      notes.push(note)
      continue
    }
    if (token.startsWith('--') && FLAGS.has(token) === false && !tex.length) {
      return { error: 'The pane takes the formula, --legend, and --note.' }
    }
    tex.push(token)
  }

  const formula = unwrap(tex.join(' ').trim())
  if (!formula) return { error: 'Give a formula.' }
  if (formula.includes('\0')) return { error: 'Give a formula.' }
  if (formula.length > 4000) return { error: 'That formula is too long.' }
  if (notes.length > 12) return { error: 'Too many notes.' }
  if (notes.some((note) => note.length > 500)) return { error: 'A note is too long.' }
  return { kind: 'draw', tex: formula, legend, notes }
}

export function drawArgv(path, job) {
  const argv = ['mathcat', '--local', '-o', path]
  if (job.legend) argv.push('--legend')
  for (const note of job.notes) argv.push('--note', note)
  argv.push('--', job.tex)
  return argv
}

export function cellBox(bodyColumns, width, height) {
  const columns = Math.min(255, Math.max(1, bodyColumns || 80))
  if (!width || !height) return { columns, rows: 6 }
  const rows = Math.max(1, Math.min(255, Math.round((columns * height) / width / 2)))
  return { columns, rows }
}

export function pngSize(base64) {
  if (typeof base64 !== 'string' || base64.length < 32) return null
  const bytes = decode32(base64.slice(0, 32))
  if (!bytes || bytes.length < 24) return null
  if (bytes[0] !== 137 || bytes[1] !== 80 || bytes[2] !== 78 || bytes[3] !== 71) return null
  const width = u32(bytes, 16)
  const height = u32(bytes, 20)
  if (width < 1 || height < 1 || width > 16384 || height > 16384) return null
  return { width, height }
}

export function screenPng(text) {
  const path = String(text ?? '')
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .pop()
  if (!path || !path.startsWith('/tmp/mathcat-pane/') || !path.toLowerCase().endsWith('.png')) {
    return { error: 'mathcat did not write a PNG.' }
  }
  if (path.includes('\0') || path.split('/').includes('..')) return { error: 'mathcat did not write a PNG.' }
  return { path }
}

function unwrap(tex) {
  if (tex.length >= 3 && tex.startsWith('$') && tex.endsWith('$') && !tex.slice(1, -1).includes('$')) {
    return tex.slice(1, -1).trim()
  }
  return tex
}

function tokenize(text) {
  const value = []
  let current = ''
  let quote = ''
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (quote) {
      if (ch === '\\' && i + 1 < text.length && (text[i + 1] === quote || text[i + 1] === '\\')) {
        current += text[++i]
        continue
      }
      if (ch === quote) {
        quote = ''
        continue
      }
      current += ch
      continue
    }
    if (ch === '"' || ch === "'") {
      quote = ch
      continue
    }
    if (ch === ' ' || ch === '\t' || ch === '\n' || ch === '\r') {
      if (current) {
        value.push(current)
        current = ''
      }
      continue
    }
    current += ch
  }
  if (quote) return { error: 'A quote was not closed.' }
  if (current) value.push(current)
  return { value }
}

function u32(bytes, offset) {
  return bytes[offset] * 16777216 + bytes[offset + 1] * 65536 + bytes[offset + 2] * 256 + bytes[offset + 3]
}

function decode32(text) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
  const out = []
  let buffer = 0
  let bits = 0
  for (const ch of text) {
    if (ch === '=') break
    const value = alphabet.indexOf(ch)
    if (value < 0) return null
    buffer = (buffer << 6) | value
    bits += 6
    if (bits >= 8) {
      bits -= 8
      out.push((buffer >> bits) & 255)
    }
  }
  return out
}
