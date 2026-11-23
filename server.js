/**
 * FOSJA - API Cerebral Individual v1.0 GIGANTE
 * 100% INDIVIDUAL - Zero dependências externas, Zero Gemini, Zero Claude
 * Só FOSJA. Cérebro próprio.
 * Node.js 18+ nativo
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORTA = process.env.PORT || 3000;
const ARQUIVO_MEMORIA = path.join(__dirname, 'cerebro_memoria.json');

// Estrutura inicial da memória da FOSJA
const memoriaPadrao = () => ({
  perfil: {
    nome: "Pai",
    projeto: "FOSJA",
    gosta: [],
    odeia: []
  },
  fatos: {},
  historico: [],
  atualizadoEm: new Date().toISOString()
});

function carregarMemoria() {
  try {
    if (!fs.existsSync(ARQUIVO_MEMORIA)) {
      const inicial = memoriaPadrao();
      fs.writeFileSync(ARQUIVO_MEMORIA, JSON.stringify(inicial, null, 2), 'utf8');
      return inicial;
    }
    return JSON.parse(fs.readFileSync(ARQUIVO_MEMORIA, 'utf8'));
  } catch (err) {
    return memoriaPadrao();
  }
}

function salvarMemoria(mem) {
  mem.atualizadoEm = new Date().toISOString();
  fs.writeFileSync(ARQUIVO_MEMORIA, JSON.stringify(mem, null, 2), 'utf8');
}

// MOTOR MATEMÁTICO - Prioridade absoluta, sem erro
function calcularExpressaoSegura(texto) {
  const matchPorcentagem = texto.match(/(\d+(?:[.,]\d+)?)\s*%\s*de\s*(\d+(?:[.,]\d+)?)/i);
  if (matchPorcentagem) {
    const pct = parseFloat(matchPorcentagem[1].replace(',', '.'));
    const base = parseFloat(matchPorcentagem[2].replace(',', '.'));
    const resultado = (pct / 100) * base;
    return { expressao: `${pct}% de ${base}`, resultado: Number(resultado.toFixed(6)) };
  }
  let limpa = texto.replace(/quanto\s+[eé]\s*/gi, '').replace(/calcule\s*/gi, '').replace(/,/g, '.').replace(/×/g, '*').replace(/÷/g, '/').replace(/\?/g, '').trim();
  if (!/^[0-9+\-*/().^\s]+$/.test(limpa) || !/\d/.test(limpa)) return null;
  let pos = 0;
  const str = limpa.replace(/\s+/g, '');
  function parseExpressao() {
    let val = parseTermo();
    while (pos < str.length && (str[pos] === '+' || str[pos] === '-')) {
      const op = str[pos++];
      const direito = parseTermo();
      val = op === '+' ? val + direito : val - direito;
    }
    return val;
  }
  function parseTermo() {
    let val = parsePotencia();
    while (pos < str.length && (str[pos] === '*' || str[pos] === '/')) {
      const op = str[pos++];
      const direito = parsePotencia();
      if (op === '/') { if (direito === 0) throw new Error('Divisão por zero'); val /= direito; } else val *= direito;
    }
    return val;
  }
  function parsePotencia() {
    let base = parseFator();
    if (pos < str.length && str[pos] === '^') { pos++; return Math.pow(base, parsePotencia()); }
    return base;
  }
  function parseFator() {
    if (str[pos] === '+') { pos++; return parseFator(); }
    if (str[pos] === '-') { pos++; return -parseFator(); }
    if (str[pos] === '(') { pos++; const val = parseExpressao(); if (str[pos] !== ')') throw new Error('Parêntese não fechado'); pos++; return val; }
    const inicio = pos;
    while (pos < str.length && /[0-9.]/.test(str[pos])) pos++;
    if (inicio === pos) throw new Error('Token inválido');
    return parseFloat(str.slice(inicio, pos));
  }
  try {
    const resultado = parseExpressao();
    if (pos !== str.length || !Number.isFinite(resultado)) return null;
    return { expressao: limpa, resultado: Number(resultado.toFixed(6)) };
  } catch { return null; }
}

// EXTRATOR DE MEMÓRIA
function extrairAtualizacoesMemoria(texto, mem) {
  const mudancas = [];
  const nomeMatch = texto.match(/meu nome [eé]\s+([a-zA-ZÀ-ÿ]{2,30})/i);
  if (nomeMatch) { mem.perfil.nome = nomeMatch[1].trim(); mudancas.push(`nome=${mem.perfil.nome}`); }
  const projMatch = texto.match(/meu projeto [eé]\s+([^.,!?\n]{2,60})/i);
  if (projMatch) { mem.perfil.projeto = projMatch[1].trim(); mudancas.push(`projeto=${mem.perfil.projeto}`); }
  const gostaMatch = texto.match(/(?:eu )?gosto de\s+([^.,!?\n]{2,50})/i);
  if (gostaMatch) { const item = gostaMatch[1].trim(); if (!mem.perfil.gosta.includes(item)) { mem.perfil.gosta.push(item); mudancas.push(`gosta+=${item}`); } }
  const odeiaMatch = texto.match(/(?:eu )?odeio\s+([^.,!?\n]{2,50})/i);
  if (odeiaMatch) { const item = odeiaMatch[1].trim(); if (!mem.perfil.odeia.includes(item)) { mem.perfil.odeia.push(item); mudancas.push(`odeia+=${item}`); } }
  return mudancas;
}

// CLASSIFICADOR FOSJA
function classificarIntencao(texto, calculo) {
  if (calculo) return { tipo: 'calculo_exato', confianca: 0.99 };
  const t = texto.toLowerCase();
  if (/\b(código|codigo|html|css|js|javascript|python|api|bug|erro|função|funcao)\b/.test(t)) return { tipo: 'engenharia_codigo', confianca: 0.92 };
  if (/\b(decidir|melhor|comparar|prós|contras|vale a pena|escolher|estratégia)\b/.test(t)) return { tipo: 'analise_decisao', confianca: 0.90 };
  if (/\b(plano|passo a passo|checklist|organizar|roteiro|meta)\b/.test(t)) return { tipo: 'planejamento', confianca: 0.88 };
  if (/\b(lembra|meu nome|meu projeto|memória|memoria)\b/.test(t)) return { tipo: 'consulta_memoria', confianca: 0.95 };
  return { tipo: 'conversa_geral', confianca: 0.80 };
}

// GERADOR FOSJA - SÓ LOCAL, SEM API EXTERNA
function gerarRespostaFosja(mensagem, mem, intencao, calculo, mudancas) {
  const saudacao = mem.perfil.nome ? `${mem.perfil.nome}, ` : 'Pai, ';
  if (calculo) {
    return { resposta: `${saudacao}o resultado exato de ${calculo.expressao} é ${calculo.resultado}.`, analise_logica: [`Expressão identificada: ${calculo.expressao}`, `Validação aritmética executada localmente sem aproximação`, `Resultado final: ${calculo.resultado}`] };
  }
  if (intencao.tipo === 'consulta_memoria') {
    const resumo = [`Nome: ${mem.perfil.nome || 'não informado'}`, `Projeto: ${mem.perfil.projeto || 'não informado'}`, `Gosta: ${mem.perfil.gosta.join(', ') || 'nada salvo'}`, `Odeia: ${mem.perfil.odeia.join(', ') || 'nada salvo'}`].join(' | ');
    return { resposta: `Aqui tá o que eu tenho guardado na memória agora: ${resumo}.`, analise_logica: ['Consulta direta ao estado persistente em cerebro_memoria.json'] };
  }
  if (mudancas.length > 0) {
    return { resposta: `Anotado na memória (${mudancas.join(', ')}). Já vou adaptar as próximas respostas pra isso.`, analise_logica: [`Atualização de contexto: ${mudancas.join(', ')}`] };
  }
  if (intencao.tipo === 'analise_decisao') {
    return { resposta: `${saudacao}pra decidir com lógica sobre "${mensagem}", divide em 3 critérios: 1) Custo de tempo/dinheiro, 2) Risco reversível vs irreversível, 3) Impacto no teu objetivo${mem.perfil.projeto ? ` (${mem.perfil.projeto})` : ''}. Escolhe a opção que gera resultado mais rápido com menor risco.`, analise_logica: ['Decomposição do problema em custo, risco e impacto', 'Aplicação de critério de decisão racional'] };
  }
  if (intencao.tipo === 'planejamento') {
    return { resposta: `${saudacao}estrutura racional pro teu pedido: Passo 1 — Define o entregável mínimo funcional. Passo 2 — Quebra em blocos de 30 minutos. Passo 3 — Testa um bloco antes de avançar pro próximo.`, analise_logica: ['Conversão de pedido em plano sequencial executável'] };
  }
  if (intencao.tipo === 'engenharia_codigo') {
    return { resposta: `${saudacao}recebi teu pedido de código: "${mensagem}". Me fala a linguagem e o que tem que fazer que eu já te devolvo o código pronto, sem enrolação, estilo FOSJA.`, analise_logica: ['Classificação: engenharia_codigo', 'Pronto para gerar código local'] };
  }
  return { resposta: `${saudacao}recebi "${mensagem}" no meu motor individual FOSJA (intenção: ${intencao.tipo}). Eu sou única, não uso Gemini, não uso Claude, eu penso com meu próprio cérebro. Me fala mais que eu continuo.`, analise_logica: [`Classificação: ${intencao.tipo} (confiança ${intencao.confianca})`, 'Processado pelo núcleo FOSJA individual, sem chave externa'] };
}

function enviarJSON(res, status, dados) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type, Authorization' });
  res.end(JSON.stringify(dados, null, 2));
}

function lerBody(req) {
  return new Promise((resolve, reject) => {
    let corpo = '';
    req.on('data', (chunk) => { corpo += chunk; if (corpo.length > 1e6) reject(new Error('Payload muito grande')); });
    req.on('end', () => { if (!corpo) return resolve({}); try { resolve(JSON.parse(corpo)); } catch { reject(new Error('JSON inválido')); } });
    req.on('error', reject);
  });
}

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') return enviarJSON(res, 204, {});
  const url = req.url.split('?')[0];
  if (req.method === 'GET' && url === '/api/saude') {
    const mem = carregarMemoria();
    return enviarJSON(res, 200, { status: 'online', motor: 'FOSJA Individual v1.0 - Sem Gemini, Sem Dependencia Externa', uptimeSegundos: Math.floor(process.uptime()), turnosNaMemoria: mem.historico.length, perfilAtivo: mem.perfil });
  }
  if (req.method === 'GET' && url === '/api/memoria') return enviarJSON(res, 200, carregarMemoria());
  if (req.method === 'POST' && url === '/api/memoria') {
    try { const body = await lerBody(req); const mem = carregarMemoria(); if (body.nome) mem.perfil.nome = String(body.nome); if (body.projeto) mem.perfil.projeto = String(body.projeto); if (body.chave && body.valor !== undefined) mem.fatos[String(body.chave)] = body.valor; salvarMemoria(mem); return enviarJSON(res, 200, { ok: true, memoria: mem }); } catch (err) { return enviarJSON(res, 400, { ok: false, erro: err.message }); }
  }
  if (req.method === 'DELETE' && url === '/api/memoria') { const limpa = memoriaPadrao(); salvarMemoria(limpa); return enviarJSON(res, 200, { ok: true, mensagem: 'Memória FOSJA zerada.' }); }
  if (req.method === 'POST' && url === '/api/pensar') {
    try {
      const body = await lerBody(req);
      const mensagem = String(body.mensagem || '').trim();
      if (!mensagem) return enviarJSON(res, 400, { ok: false, erro: 'Campo "mensagem" é obrigatório.' });
      const mem = carregarMemoria();
      const mudancas = extrairAtualizacoesMemoria(mensagem, mem);
      const calculo = calcularExpressaoSegura(mensagem);
      const intencao = classificarIntencao(mensagem, calculo);
      // FOSJA INDIVIDUAL - Sempre local, nunca chama API externa
      const local = gerarRespostaFosja(mensagem, mem, intencao, calculo, mudancas);
      const respostaFinal = local.resposta;
      const analiseLogica = local.analise_logica;
      const origem = 'fosja_individual_local';
      mem.historico.push({ papel: 'usuario', texto: mensagem, em: new Date().toISOString() });
      mem.historico.push({ papel: 'fosja', texto: respostaFinal, em: new Date().toISOString() });
      if (mem.historico.length > 30) mem.historico = mem.historico.slice(-30);
      salvarMemoria(mem);
      return enviarJSON(res, 200, { ok: true, origem, intencao, memoriaAtualizada: mudancas, analiseLogica, resposta: respostaFinal, perfil: mem.perfil });
    } catch (err) { return enviarJSON(res, 400, { ok: false, erro: err.message }); }
  }
  return enviarJSON(res, 404, { ok: false, erro: 'Rota não encontrada.' });
});

server.listen(PORTA, () => {
  console.log(`FOSJA INDIVIDUAL rodando em http://localhost:${PORTA}`);
  console.log(`Rotas: GET /api/saude | GET/POST/DELETE /api/memoria | POST /api/pensar`);
});
