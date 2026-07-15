/**
 * quality_check.mjs
 *
 * Détecteur de violations qualité TypeScript via AST (@typescript-eslint/parser).
 * Exécuté depuis le répertoire du projet généré où @typescript-eslint/parser est disponible.
 *
 * Usage : node quality_check.mjs <file1.ts> <file2.ts> ...
 * Output : JSON array de violations { file, line, rule, message, rag_query }
 *
 * Règles détectées :
 *   Z21 — findMany() sans take (pagination manquante)
 *   Z24 — findUnique() dans .map() (N+1)
 *   Z25 — findMany() sans select (surcharge données)
 *   Z26 — 2+ mutations prisma consécutives sans $transaction
 */

import { readFileSync } from 'fs'

// ── Contrat (optionnel) ──────────────────────────────────────────────────────
// --contract <path> : contrat émis par dev_graph décrivant, page par page, ce que
// l'architect a déclaré. Sans lui, seules les règles Z* (patterns de code) tournent.
// Les règles C* comparent le code généré au contrat — c'est le second capteur :
// elles attrapent ce qui compile parfaitement mais ment (KPI tronqué, fetch interdit).
let contract = null
{
  const i = process.argv.indexOf('--contract')
  if (i !== -1 && process.argv[i + 1]) {
    try {
      contract = JSON.parse(readFileSync(process.argv[i + 1], 'utf-8'))
    } catch {
      contract = null
    }
  }
}
const PAGINATED_METHODS = new Set(
  contract?.paginated_methods ?? ['getAll', 'getAllWithRelations', 'getPublicAll', 'getPublished']
)

// @typescript-eslint/parser est disponible dans node_modules du projet généré
let parse
try {
  const mod = await import('@typescript-eslint/parser')
  parse = mod.parse
} catch {
  // Fallback : essayer le chemin relatif
  const mod = await import('./node_modules/@typescript-eslint/parser/dist/index.js')
  parse = mod.parse
}

const filePaths = process.argv.slice(2).filter((a, i, all) => {
  if (a === '--contract') return false
  if (all[i - 1] === '--contract') return false
  return true
})
const violations = []

// Contrat indexé par fichier de page (chemin relatif au projet).
const contractByFile = new Map()
for (const page of contract?.pages ?? []) {
  if (page?.file) contractByFile.set(page.file, page)
}

for (const filePath of filePaths) {
  let code
  try {
    code = readFileSync(filePath, 'utf-8')
  } catch {
    continue
  }

  let ast
  try {
    // filePath est INDISPENSABLE : sans lui le parser suppose une extension .ts,
    // interprète le JSX comme des assertions de type et échoue sur tout .tsx.
    ast = parse(code, { jsx: true, loc: true, range: true, tokens: false, filePath })
  } catch (err) {
    // Un fichier illisible n'est PAS un fichier propre — on le signale au lieu de
    // le sauter en silence (c'est ce silence qui a rendu le checker aveugle aux pages).
    violations.push({
      file: filePath,
      line: err?.location?.start?.line ?? 0,
      rule: 'C0-unparseable',
      message: `Fichier non analysable par le checker (${err?.message ?? 'erreur de parsing'}) — aucune garantie qualité ne peut être donnée dessus.`,
    })
    continue
  }

  walkNode(ast, filePath, violations)
  detectConsecutiveMutations(ast, filePath, violations)

  const pageContract = contractByFile.get(normalizeRel(filePath))
  if (pageContract) checkPageContract(ast, filePath, pageContract, violations)
}

process.stdout.write(JSON.stringify(violations, null, 2) + '\n')

// ── Règles C* — code généré vs contrat architect ─────────────────────────────

function normalizeRel(p) {
  return p.replace(/\\/g, '/').replace(/^\.\//, '')
}

function checkPageContract(ast, filePath, page, violations) {
  const aggSources = new Set(page.agg_sources ?? [])
  const serviceCalls = collectServiceCalls(ast)

  // C2 — l'architect a déclaré data_fetches: [] (page de présentation, sans données).
  // Tout appel de service ici est une invention du LLM : la page ment sur son rôle,
  // et duplique de la logique qui vit ailleurs.
  if (page.allows_data === false) {
    for (const call of serviceCalls) {
      violations.push({
        file: filePath,
        line: call.line,
        rule: 'C2-fetch-on-static-page',
        message:
          `Le contrat de « ${page.path} » déclare data_fetches: [] (aucune donnée), ` +
          `mais la page appelle ${call.service}.${call.method}(). ` +
          `Retirer l'appel : cette page ne doit afficher aucune donnée.`,
      })
    }
    return
  }

  // C1 — un KPI / une liste filtrée agrège une source chargée par un appel PAGINÉ.
  // Le calcul est juste, mais il porte sur les 20 premières lignes : le total affiché
  // est silencieusement faux. Ni le build ni les tests ne peuvent le voir.
  for (const call of serviceCalls) {
    if (!call.assignedTo || !aggSources.has(call.assignedTo)) continue
    if (!PAGINATED_METHODS.has(call.method)) continue
    if (call.argCount >= 3) continue // (userId, page, pageSize) — dé-paginé explicitement
    violations.push({
      file: filePath,
      line: call.line,
      rule: 'C1-aggregate-over-paginated',
      message:
        `« ${call.assignedTo} » alimente un KPI ou une liste filtrée du contrat, ` +
        `mais est chargé via ${call.method}() qui est paginé (20 lignes par défaut). ` +
        `L'agrégat sera faux au-delà de 20 enregistrements. Charger la totalité de la source.`,
    })
  }
}

/**
 * Collecte les appels `xxxService.method(...)` avec, si présent, la variable
 * qui en reçoit le résultat (`const items = await xxxService.getAll(userId)`).
 */
function collectServiceCalls(ast) {
  const calls = []

  function visit(node, assignedTo) {
    if (!node || typeof node !== 'object' || !node.type) return

    if (node.type === 'VariableDeclarator' && node.id?.type === 'Identifier') {
      visit(node.init, node.id.name)
      return
    }
    if (node.type === 'AwaitExpression') {
      visit(node.argument, assignedTo)
      return
    }

    if (node.type === 'CallExpression' && node.callee?.type === 'MemberExpression') {
      const objName = node.callee.object?.name
      const method = node.callee.property?.name
      if (objName && method && /Service$/.test(objName)) {
        calls.push({
          service: objName,
          method,
          argCount: (node.arguments || []).length,
          assignedTo: assignedTo ?? null,
          line: node.loc?.start?.line ?? 0,
        })
      }
    }

    for (const key of Object.keys(node)) {
      const child = node[key]
      if (Array.isArray(child)) for (const c of child) visit(c, null)
      else if (child && typeof child === 'object' && child.type) visit(child, null)
    }
  }

  visit(ast, null)
  return calls
}

// ── Traversée récursive ─────────────────────────────────────────────────────

function walkNode(node, filePath, violations) {
  if (!node || typeof node !== 'object' || !node.type) return

  // Z21 — findMany sans take
  if (isFindManyWithoutTake(node)) {
    violations.push({
      file: filePath,
      line: node.loc?.start?.line ?? 0,
      rule: 'Z21-pagination-missing',
      message: 'findMany() sans take/skip — ajouter la pagination (pageSize=20 par défaut)',
      rag_query: 'pagination findMany skip take PaginatedResponse',
    })
  }

  // Z24 — findUnique dans .map() → N+1
  if (isMapWithFindUnique(node)) {
    violations.push({
      file: filePath,
      line: node.loc?.start?.line ?? 0,
      rule: 'Z24-n1-pattern',
      message: 'findUnique() dans .map() → N+1 requêtes. Utiliser include: { relation: true } à la place.',
      rag_query: 'N+1 prevention include select imbriqué findUnique loop Prisma',
    })
  }

  // Z25 — findMany sans select (dans les fichiers services uniquement)
  if (filePath.includes('/services/') || filePath.includes('\\services\\')) {
    if (isFindManyWithoutSelect(node)) {
      violations.push({
        file: filePath,
        line: node.loc?.start?.line ?? 0,
        rule: 'Z25-select-missing',
        message: 'findMany() sans select dans un service — spécifier seulement les champs nécessaires.',
        rag_query: 'select minimal findMany performance Prisma GetPayload',
      })
    }
  }

  for (const key of Object.keys(node)) {
    const child = node[key]
    if (Array.isArray(child)) {
      for (const c of child) walkNode(c, filePath, violations)
    } else if (child && typeof child === 'object' && child.type) {
      walkNode(child, filePath, violations)
    }
  }
}

// ── Z26 — 2 mutations Prisma consécutives sans $transaction ─────────────────

function detectConsecutiveMutations(ast, filePath, violations) {
  const mutationOps = new Set(['create', 'createMany', 'update', 'updateMany', 'delete', 'deleteMany', 'upsert'])

  function checkBlock(statements) {
    let consecutiveCount = 0
    let firstLine = 0

    for (const stmt of statements) {
      const isPrismaMutation = isPrismaCall(stmt, mutationOps)
      const isTransaction = isTransactionCall(stmt)

      if (isTransaction) {
        consecutiveCount = 0
        continue
      }

      if (isPrismaMutation) {
        if (consecutiveCount === 0) firstLine = stmt.loc?.start?.line ?? 0
        consecutiveCount++
        if (consecutiveCount >= 2) {
          violations.push({
            file: filePath,
            line: firstLine,
            rule: 'Z26-missing-transaction',
            message: '2+ mutations Prisma consécutives sans $transaction — les envelopper dans prisma.$transaction()',
            rag_query: 'transaction prisma $transaction séquentielle rollback multi-table',
          })
          consecutiveCount = 0
        }
      } else {
        consecutiveCount = 0
      }

      // Descendre dans les blocs imbriqués
      if (stmt.type === 'IfStatement') {
        if (stmt.consequent?.body) checkBlock(stmt.consequent.body)
        if (stmt.alternate?.body) checkBlock(stmt.alternate.body)
      }
      if (stmt.type === 'TryStatement') {
        if (stmt.block?.body) checkBlock(stmt.block.body)
      }
    }
  }

  function traverseForBlocks(node) {
    if (!node || typeof node !== 'object') return
    if (node.type === 'BlockStatement' && node.body) checkBlock(node.body)
    for (const key of Object.keys(node)) {
      const child = node[key]
      if (Array.isArray(child)) for (const c of child) traverseForBlocks(c)
      else if (child && typeof child === 'object' && child.type) traverseForBlocks(child)
    }
  }

  traverseForBlocks(ast)
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function getMemberCallChain(node) {
  // Retourne [objet, methode] pour les CallExpression
  if (node.type !== 'CallExpression') return null
  const callee = node.callee
  if (callee?.type !== 'MemberExpression') return null
  return { method: callee.property?.name, object: callee.object }
}

function isMemberCallNamed(node, methodName) {
  const chain = getMemberCallChain(node)
  return chain?.method === methodName
}

function isFindManyWithoutTake(node) {
  if (!isMemberCallNamed(node, 'findMany')) return false
  const args = node.arguments
  if (!args?.length) return true // findMany() sans args = pas de limite
  const firstArg = args[0]
  if (firstArg?.type !== 'ObjectExpression') return false
  // where: { id: { in: [...] } } — le résultat est borné par la liste d'ids de l'appelant
  // (garde d'ownership, prefetch M2M). Paginer tronquerait le jeu de validation.
  if (isBoundedByIdIn(firstArg)) return false
  const propNames = (firstArg.properties || []).map(p => p.key?.name).filter(Boolean)
  return !propNames.includes('take') && !propNames.includes('skip')
}

function getObjectProp(objExpr, name) {
  if (objExpr?.type !== 'ObjectExpression') return null
  const prop = (objExpr.properties || []).find(p => p.key?.name === name)
  return prop?.value ?? null
}

function isBoundedByIdIn(argObj) {
  const idClause = getObjectProp(getObjectProp(argObj, 'where'), 'id')
  return getObjectProp(idClause, 'in') !== null
}

function isFindManyWithoutSelect(node) {
  if (!isMemberCallNamed(node, 'findMany')) return false
  const args = node.arguments
  if (!args?.length) return false
  const firstArg = args[0]
  if (firstArg?.type !== 'ObjectExpression') return false
  const propNames = (firstArg.properties || []).map(p => p.key?.name).filter(Boolean)
  // Ne signaler que si un where est présent (c'est une vraie requête service)
  return propNames.includes('where') && !propNames.includes('select') && !propNames.includes('include')
}

function isMapWithFindUnique(node) {
  if (!isMemberCallNamed(node, 'map')) return false
  const callback = node.arguments?.[0]
  if (!callback) return false
  return subtreeContainsFindUnique(callback)
}

function subtreeContainsFindUnique(node) {
  if (!node || typeof node !== 'object') return false
  if (node.type === 'CallExpression' && isMemberCallNamed(node, 'findUnique')) return true
  for (const key of Object.keys(node)) {
    const child = node[key]
    if (Array.isArray(child)) { if (child.some(c => subtreeContainsFindUnique(c))) return true }
    else if (child && typeof child === 'object' && child.type) { if (subtreeContainsFindUnique(child)) return true }
  }
  return false
}

function isPrismaCall(stmt, mutationOps) {
  // Détecte await prisma.model.create/update/delete(...)
  const expr = stmt.type === 'ExpressionStatement' ? stmt.expression
    : stmt.type === 'VariableDeclaration' ? stmt.declarations?.[0]?.init
    : null
  if (!expr) return false
  const inner = expr.type === 'AwaitExpression' ? expr.argument : expr
  if (inner?.type !== 'CallExpression') return false
  const chain = getMemberCallChain(inner)
  return chain && mutationOps.has(chain.method)
}

function isTransactionCall(stmt) {
  const expr = stmt.type === 'ExpressionStatement' ? stmt.expression
    : stmt.type === 'VariableDeclaration' ? stmt.declarations?.[0]?.init
    : null
  if (!expr) return false
  const inner = expr.type === 'AwaitExpression' ? expr.argument : expr
  if (inner?.type !== 'CallExpression') return false
  return isMemberCallNamed(inner, '$transaction')
}
